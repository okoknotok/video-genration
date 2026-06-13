"""
角色管理系統 — LoRA 訓練 + 本地儲存 + DB

用法:
    python characters.py create              # 互動建立角色
    python characters.py create-batch file   # 批量建立（從 JSON 檔案）
    python characters.py list                # 列出所有角色
    python characters.py preview <name>      # 預覽角色圖
    python characters.py retrain <name>      # 重新訓練 LoRA
    python characters.py delete <name>       # 刪除角色
    python characters.py export              # 匯出角色資料（分享用）
"""

import os
import json
import time
import shutil
import zipfile
import tempfile
import argparse
import sys
from pathlib import Path
from datetime import datetime

# ⚠️ 必須喺 import fal_client 之前載入 .env
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    # 手動 parse .env（避免 dotenv 順序問題）
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

import fal_client

# ============================================================
# 設定
# ============================================================

FAL_KEY = os.getenv("FAL_KEY", "")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

# 路徑
BASE_DIR = Path(__file__).parent
CHAR_DIR = BASE_DIR / "characters_data"
DB_PATH = BASE_DIR / "characters_data" / "characters.json"

# 韓漫風格
MANHWA_STYLE = (
    "korean webtoon style, manhwa art, semi-realistic, soft cel shading, "
    "detailed facial features, cinematic Korean drama lighting, pinterest aesthetic"
)

# ============================================================
# 角色分級配置（慳錢用）
# ============================================================
#
# ⭐ protagonist: LoRA + 8 變化圖 + 1000 steps ≈ $2/人
# 🔹 supporting:  LoRA + 6 變化圖 + 800 steps  ≈ $1.5/人
# · minor:        淨 reference image            ≈ $0.03/人
#
ROLE_CONFIG = {
    "protagonist": {
        "num_variations": 8,
        "steps": 1000,
        "skip_lora": False,
        "variation_method": "kontext",  # 一致性最好
    },
    "supporting": {
        "num_variations": 6,
        "steps": 800,
        "skip_lora": False,
        "variation_method": "kontext",
    },
    "minor": {
        "num_variations": 0,
        "steps": 0,
        "skip_lora": True,
        "variation_method": "none",
    },
}

# LoRA 訓練變化圖 prompts（多角度多表情，等 LoRA 學得準）
VARIATION_PROMPTS = [
    "front view portrait, neutral expression, looking at camera",
    "three-quarter view, gentle smile",
    "side profile view, looking to the right",
    "looking up slightly, surprised expression",
    "close-up of face, calm and composed",
    "full body standing pose, arms relaxed",
    "looking down, sad melancholic expression",
    "angry intense expression, furrowed brows",
    "from slightly above, soft warm smile",
    "dynamic action pose, determined expression",
    "soft window lighting, thoughtful pensive mood",
    "bright daylight, happy laughing expression",
    "back view, looking over shoulder",
    "low angle shot, powerful confident pose",
    "dramatic side lighting, mysterious mood",
]


# ============================================================
# DB 操作
# ============================================================

def load_db():
    """讀取角色資料庫"""
    if DB_PATH.exists():
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"characters": [], "metadata": {"created": datetime.now().isoformat()}}


def save_db(db):
    """儲存角色資料庫"""
    db["metadata"]["updated"] = datetime.now().isoformat()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def get_character(name):
    """搵一個角色"""
    db = load_db()
    for c in db["characters"]:
        if c["name"] == name:
            return c
    return None


def ensure_char_dir(name):
    """確保角色目錄存在"""
    d = CHAR_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    return d


# ============================================================
# 圖片生成
# ============================================================

def generate_hero_image(description, style="manhwa", seed=42):
    """生成主參考圖（hero image）"""
    style_prompt = MANHWA_STYLE if style == "manhwa" else style
    
    prompt = (
        f"{style_prompt}, "
        f"{description}, "
        f"single character, simple neutral background, "
        f"detailed face, high quality, upper body portrait"
    )
    
    result = fal_client.subscribe(
        "fal-ai/flux/dev",
        arguments={
            "prompt": prompt,
            "width": 768,
            "height": 1024,
            "num_inference_steps": 30,
            "guidance_scale": 3.5,
            "seed": seed,
            "enable_safety_checker": False,
        },
        with_logs=False,
    )
    return result["images"][0]["url"]


def generate_variations(hero_url, num_variations=12):
    """用 Kontext 生成多角度變化圖"""
    urls = []
    prompts = VARIATION_PROMPTS[:num_variations]
    
    for i, instruction in enumerate(prompts):
        print(f"  🖼️  變化圖 {i+1}/{len(prompts)}: {instruction}")
        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/kontext",
                arguments={
                    "prompt": f"same exact person, identical face and hair and outfit, {instruction}",
                    "image_url": hero_url,
                },
                with_logs=False,
            )
            urls.append(result["images"][0]["url"])
        except Exception as e:
            print(f"    ⚠️  失敗，跳過: {e}")
    
    return urls


def download_file(url, dest_path):
    """下載檔案到本地"""
    import httpx
    with httpx.Client(timeout=120) as client:
        response = client.get(url)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(response.content)
    return dest_path


# ============================================================
# LoRA 訓練
# ============================================================

def train_lora(name, trigger_word, image_dir, steps=1000, force=False):
    """訓練 LoRA 並下載到本地
    
    Args:
        force: 強制重新訓練（即使已有 LoRA）
    """
    char_name = image_dir.name
    lora_path = image_dir / f"{char_name}_{trigger_word}.safetensors"
    lock_path = image_dir / ".training.lock"
    done_path = image_dir / "DONE"
    
    # 檢查是否已有 LoRA
    if lora_path.exists() and not force:
        print(f"  ⏭️  LoRA 已存在: {lora_path.name}")
        # 從 DB 讀取 URL
        db = load_db()
        for c in db.get("characters", []):
            if c["name"] == name and c.get("lora_url"):
                return str(lora_path), c["lora_url"]
        return str(lora_path), ""
    
    # 檢查是否有其他進程正在訓練
    if lock_path.exists() and not force:
        lock_age = time.time() - lock_path.stat().st_mtime
        if lock_age < 1800:  # 30 分鐘內
            print(f"  ⚠️  另一個進程正在訓練（{int(lock_age/60)} 分鐘前開始）")
            print(f"     Lock file: {lock_path}")
            print(f"     請等待或刪除 lock file 後重試")
            raise RuntimeError(f"Training already in progress (lock: {lock_path})")
    
    # 建立 lock file
    lock_path.write_text(f"Training started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 打包圖片
        zip_path = image_dir / "train.zip"
        with zipfile.ZipFile(zip_path, "w") as z:
            for fn in sorted(image_dir.iterdir()):
                if fn.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp') and fn.name != 'train.zip':
                    z.write(fn, fn.name)
        
        print(f"  ☁️  上載訓練資料 ({zip_path.stat().st_size // 1024}KB)...")
        zip_url = fal_client.upload_file(str(zip_path))
        
        print(f"  🎓 訓練 LoRA (trigger: {trigger_word}, steps: {steps})...")
        print(f"     大約 5-10 分鐘，耐心等...")
        
        result = fal_client.subscribe(
            "fal-ai/flux-lora-fast-training",
            arguments={
                "images_data_url": zip_url,
                "trigger_word": trigger_word,
                "steps": steps,
                "is_style": False,
            },
            with_logs=True,
        )
        
        # 搵 LoRA URL
        lora_url = (
            (result.get("diffusers_lora_file") or {}).get("url")
            or (result.get("lora_file") or {}).get("url")
        )
        
        if not lora_url:
            raise RuntimeError(f"訓練完成但搵唔到 LoRA URL: {str(result)[:200]}")
        
        print(f"  💾 下載 LoRA 到本地...")
        download_file(lora_url, lora_path)
        
        # 寫入完成標記
        done_path.write_text(f"LoRA training completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return str(lora_path), lora_url
    
    finally:
        # 清除 lock file
        if lock_path.exists():
            lock_path.unlink()


# ============================================================
# 核心：建立角色
# ============================================================

def create_character(
    name: str,
    trigger_word: str,
    description: str,
    style: str = "manhwa",
    num_variations: int = None,
    steps: int = None,
    seed: int = 42,
    role: str = "supporting",
    personality: str = "",
    voice_id: str = "",
    skip_lora: bool = None,
):
    """
    建立角色
    
    Args:
        name: 角色名稱（中文）
        trigger_word: LoRA trigger（英文無空格，例 ohwx_minho）
        description: 外貌描述（英文）
        style: 風格（manhwa / cinematic / anime）
        num_variations: 變化圖數量（None = 根據 role 自動設定）
        steps: LoRA 訓練步數（None = 根據 role 自動設定）
        seed: 隨機種子
        role: 角色類型 (protagonist / supporting / minor)
        personality: 性格描述
        voice_id: MiniMax 語音 ID
        skip_lora: 跳過 LoRA（None = 根據 role 自動設定）
    """
    # 從 ROLE_CONFIG 取得預設值
    role_cfg = ROLE_CONFIG.get(role, ROLE_CONFIG["supporting"])
    if skip_lora is None:
        skip_lora = role_cfg["skip_lora"]
    if num_variations is None:
        num_variations = role_cfg["num_variations"]
    if steps is None:
        steps = role_cfg["steps"]
    
    role_label = {"protagonist": "⭐主角", "supporting": "🔹副角", "minor": "·配角"}.get(role, role)
    print(f"\n{'='*60}")
    print(f"🎭 建立角色: {name} ({trigger_word})")
    print(f"   類型: {role_label} | 風格: {style} | LoRA: {'否' if skip_lora else f'是 ({num_variations}圖, {steps}步)'}")
    print(f"{'='*60}\n")
    
    char_dir = ensure_char_dir(name)
    hero_path = char_dir / f"{name}_hero.png"
    var_dir = char_dir / "variations"
    done_path = char_dir / "DONE"
    lora_safetensors = char_dir / f"{name}_{trigger_word}.safetensors"
    
    # === 快取檢查：避免重複生成 ===
    cached = False
    hero_url = ""
    lora_path = None
    lora_url = None
    variation_count = 0
    
    # Check if fully done
    if done_path.exists() and lora_safetensors.exists() and not skip_lora:
        print(f"  ⏭️  角色已完成（LoRA + 變化圖），使用快取")
        cached = True
        db = load_db()
        for c in db.get("characters", []):
            if c["name"] == name:
                hero_url = c.get("hero_url", "")
                lora_url = c.get("lora_url", "")
                lora_path = c.get("lora_path", "")
                variation_count = c.get("variation_count", 0)
                break
        if not lora_path:
            lora_path = str(lora_safetensors)
    
    # Check hero image cache
    if not cached and hero_path.exists():
        print(f"  ⏭️  Hero image 已快取: {hero_path.name}")
        # Need to re-upload to get URL for variations
        try:
            hero_url = fal_client.upload_file(str(hero_path))
        except:
            hero_url = ""
    
    # Check variation images cache
    if not cached and not skip_lora and var_dir.exists():
        existing_vars = list(var_dir.glob(f"{name}_var_*.png"))
        if len(existing_vars) >= num_variations:
            print(f"  ⏭️  變化圖已快取 ({len(existing_vars)} 張)")
            variation_count = len(existing_vars)
    
    # === 生成新內容（只生成缺少嘅部分）===
    
    # 1. Hero image
    if not cached and not hero_path.exists():
        print("  🎨 生成主參考圖...")
        hero_url = generate_hero_image(description, style, seed)
        download_file(hero_url, hero_path)
        print(f"  ✅ Hero image: {hero_path}")
    elif not cached and hero_path.exists():
        print(f"  ⏭️  Hero image 已有，跳過")
    
    if not skip_lora and not cached:
        # 2. 變化圖
        if variation_count < num_variations:
            if not hero_url:
                try:
                    hero_url = fal_client.upload_file(str(hero_path))
                except Exception as e:
                    print(f"  ⚠️  無法上傳 hero image: {e}")
                    hero_url = ""
            
            if hero_url:
                print(f"\n  🖼️  生成 {num_variations} 張變化圖...")
                var_urls = generate_variations(hero_url, num_variations)
                variation_count = len(var_urls)
                
                var_dir.mkdir(exist_ok=True)
                for i, url in enumerate(var_urls):
                    download_file(url, var_dir / f"{name}_var_{i:02d}.png")
                print(f"  ✅ {variation_count} 張變化圖已儲存")
            else:
                print(f"  ❌ 無 hero URL，跳過變化圖")
        
        # 3. LoRA 訓練（內建防重複）
        print(f"\n  🎓 開始 LoRA 訓練...")
        lora_path, lora_url = train_lora(name, trigger_word, char_dir, steps)
        print(f"  ✅ LoRA 已儲存: {lora_path}")
    elif not skip_lora and cached:
        pass  # Already done
    else:
        print("  ⏭️  跳過 LoRA 訓練（配角模式）")
    
    # 4. 存入 DB
    db = load_db()
    
    # 移除同名舊記錄
    db["characters"] = [c for c in db["characters"] if c["name"] != name]
    
    char_record = {
        "name": name,
        "trigger_word": trigger_word,
        "description": description,
        "style": style,
        "role": role,
        "personality": personality,
        "voice_id": voice_id,
        "hero_image": str(hero_path),
        "hero_url": hero_url,
        "lora_path": lora_path,
        "lora_url": lora_url,
        "variation_count": variation_count,
        "seed": seed,
        "created_at": int(time.time()),
        "updated_at": int(time.time()),
    }
    
    db["characters"].append(char_record)
    save_db(db)
    
    print(f"\n  ✅ 角色「{name}」已建立！")
    print(f"  📁 目錄: {char_dir}")
    if lora_path:
        print(f"  🎓 LoRA: {lora_path}")
    
    return char_record


def create_character_batch(config_path):
    """從 JSON 檔案批量建立角色"""
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)
    
    characters = config.get("characters", [])
    print(f"\n📋 批量建立 {len(characters)} 個角色...\n")
    
    results = []
    for i, char in enumerate(characters):
        print(f"\n[{i+1}/{len(characters)}]")
        try:
            result = create_character(
                name=char["name"],
                trigger_word=char["trigger_word"],
                description=char["description"],
                style=char.get("style", "manhwa"),
                num_variations=char.get("variations", 12),
                steps=char.get("steps", 1000),
                seed=char.get("seed", 42),
                role=char.get("role", "supporting"),
                personality=char.get("personality", ""),
                voice_id=char.get("voice_id", ""),
                skip_lora=char.get("skip_lora", False),
            )
            results.append(result)
        except Exception as e:
            print(f"  ❌ 失敗: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ 完成: {len(results)}/{len(characters)} 個角色")
    print(f"{'='*60}")
    
    return results


# ============================================================
# 管理功能
# ============================================================

def list_characters():
    """列出所有角色"""
    db = load_db()
    chars = db["characters"]
    
    if not chars:
        print("📭 未有角色。用 'create' 開始建立！")
        return
    
    print(f"\n🎭 角色資料庫 ({len(chars)} 個角色)\n")
    print(f"{'名稱':<12} {'類型':<12} {'Trigger':<18} {'LoRA':<6} {'變化圖':<6}")
    print("─" * 60)
    
    for c in chars:
        has_lora = "✅" if c.get("lora_path") else "❌"
        role_labels = {"protagonist": "⭐主角", "supporting": "🔹副角", "minor": "·配角"}
        role = role_labels.get(c.get("role", "minor"), c.get("role", "配角"))
        print(f"{c['name']:<12} {role:<12} {c['trigger_word']:<18} {has_lora:<6} {c.get('variation_count', 0):<6}")
    
    print()


def preview_character(name):
    """顯示角色資料"""
    char = get_character(name)
    if not char:
        print(f"❌ 搵唔到角色: {name}")
        return
    
    print(f"\n🎭 {char['name']}")
    print(f"   Trigger: {char['trigger_word']}")
    print(f"   類型: {char.get('role', '配角')}")
    print(f"   風格: {char.get('style', 'manhwa')}")
    print(f"   描述: {char['description'][:80]}...")
    if char.get("personality"):
        print(f"   性格: {char['personality']}")
    print(f"   LoRA: {char.get('lora_path', '未訓練')}")
    print(f"   變化圖: {char.get('variation_count', 0)} 張")
    print(f"   Hero: {char.get('hero_image', '無')}")
    print()


def delete_character(name):
    """刪除角色"""
    db = load_db()
    original_count = len(db["characters"])
    db["characters"] = [c for c in db["characters"] if c["name"] != name]
    
    if len(db["characters"]) == original_count:
        print(f"❌ 搵唔到角色: {name}")
        return
    
    # 刪除本地檔案
    char_dir = CHAR_DIR / name
    if char_dir.exists():
        shutil.rmtree(char_dir)
        print(f"  🗑️  已刪除目錄: {char_dir}")
    
    save_db(db)
    print(f"✅ 已刪除角色: {name}")


def export_characters():
    """匯出角色資料"""
    db = load_db()
    export_path = BASE_DIR / "characters_export.json"
    
    # 只匯出 metadata，唔包含本地路徑
    export_data = []
    for c in db["characters"]:
        export_data.append({
            "name": c["name"],
            "trigger_word": c["trigger_word"],
            "description": c["description"],
            "style": c.get("style", "manhwa"),
            "role": c.get("role", "supporting"),
            "personality": c.get("personality", ""),
            "voice_id": c.get("voice_id", ""),
            "lora_url": c.get("lora_url", ""),
            "hero_url": c.get("hero_url", ""),
        })
    
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已匯出 {len(export_data)} 個角色到: {export_path}")


# ============================================================
# 互動模式
# ============================================================

def interactive_create():
    """互動建立角色"""
    print("\n🎭 LoRA 角色建立器（韓漫風格）\n")
    
    name = input("角色名稱（中文，例：陳默）: ").strip()
    trigger = input("Trigger word（英文無空格，例：ohwx_chenmo）: ").strip()
    
    print("\n角色類型:")
    print("  1. ⭐ 主角 (protagonist) — 訓練 LoRA，12 張變化圖")
    print("  2. 🔹 副角 (supporting) — 訓練 LoRA，8 張變化圖")
    print("  3. ·配角 (minor) — 只生成 reference image，唔訓練 LoRA")
    
    role_choice = input("選擇 [1]: ").strip() or "1"
    role_map = {"1": "protagonist", "2": "supporting", "3": "minor"}
    role = role_map.get(role_choice, "protagonist")
    
    desc = input("\n外貌描述（英文，例: 25yo asian man, short black hair, sharp jawline）: ").strip()
    personality = input("性格描述（中文，可選）: ").strip()
    
    # 預設 voice
    voice_suggestions = {
        "male": "male-qn-jingying",
        "female": "female-shaonv",
        "narrator": "Chinese_Mature_Male_Narrator",
    }
    print(f"\n語音建議: 男={voice_suggestions['male']}, 女={voice_suggestions['female']}")
    voice_id = input(f"Voice ID [留空用預設]: ").strip()
    
    # 設定（從 ROLE_CONFIG 讀取）
    role_cfg = ROLE_CONFIG.get(role, ROLE_CONFIG["supporting"])
    skip_lora = role_cfg["skip_lora"]
    num_var = role_cfg["num_variations"]
    steps = role_cfg["steps"]
    
    print(f"\n📋 確認:")
    print(f"   名稱: {name}")
    print(f"   Trigger: {trigger}")
    print(f"   類型: {role}")
    print(f"   LoRA: {'否' if skip_lora else f'是 ({num_var} 變化圖, {steps} steps)'}")
    
    confirm = input("\n開始? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("已取消")
        return
    
    create_character(
        name=name,
        trigger_word=trigger,
        description=desc,
        role=role,
        personality=personality,
        voice_id=voice_id,
        num_variations=num_var,
        steps=steps,
        skip_lora=skip_lora,
    )


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="角色管理系統")
    sub = parser.add_subparsers(dest="command")
    
    sub.add_parser("create", help="互動建立角色")
    
    batch_p = sub.add_parser("create-batch", help="批量建立角色")
    batch_p.add_argument("config", help="JSON 配置檔案路徑")
    
    sub.add_parser("list", help="列出所有角色")
    
    preview_p = sub.add_parser("preview", help="預覽角色")
    preview_p.add_argument("name", help="角色名稱")
    
    retrain_p = sub.add_parser("retrain", help="重新訓練 LoRA")
    retrain_p.add_argument("name", help="角色名稱")
    
    delete_p = sub.add_parser("delete", help="刪除角色")
    delete_p.add_argument("name", help="角色名稱")
    
    sub.add_parser("export", help="匯出角色資料")
    
    args = parser.parse_args()
    
    if args.command == "create":
        interactive_create()
    elif args.command == "create-batch":
        create_character_batch(args.config)
    elif args.command == "list":
        list_characters()
    elif args.command == "preview":
        preview_character(args.name)
    elif args.command == "retrain":
        char = get_character(args.name)
        if char:
            print(f"重新訓練 {args.name}...")
            # TODO: implement retrain
            print("🚧 敬請期待")
        else:
            print(f"❌ 搵唔到角色: {args.name}")
    elif args.command == "delete":
        delete_character(args.name)
    elif args.command == "export":
        export_characters()
    else:
        parser.print_help()


def create_one_from_args(args):
    """CLI shortcut: create one character from args
    Usage: python characters.py quick <name> <trigger> <description> [--role protagonist]
    """
    return create_character(
        name=args.name,
        trigger_word=args.trigger,
        description=args.description,
        style=getattr(args, 'style', 'manhwa'),
        role=getattr(args, 'role', 'supporting'),
        personality=getattr(args, 'personality', ''),
        voice_id=getattr(args, 'voice_id', ''),
    )


if __name__ == "__main__":
    main()
