"""LoRA 自訂角色：
1) 用文字描述生成『主參考圖』
2) 用 Kontext 保持同一張臉，生成多角度/表情變化圖
3) 打包訓練 LoRA，LoRA 檔自動 host 喺 fal
4) 存入 characters.json，之後 pipeline 生圖會自動套用
用法：python lora_creator.py            （互動模式）
      python lora_creator.py 名 trigger 描述 [風格]
"""
import os
import json
import time
import shutil
import zipfile
import tempfile
import config
import fal_helpers as fal

# 變化圖指令：盡量多角度/表情，等 LoRA 學到立體嘅角色
VARIATION_PROMPTS = [
    "front view portrait, neutral expression",
    "three-quarter view, gentle smile",
    "side profile view",
    "looking up, surprised expression",
    "close-up of face, calm",
    "full body standing pose",
    "looking down, sad expression",
    "angry intense expression",
    "from slightly above, soft smile",
    "dynamic determined pose",
    "soft window lighting, thoughtful",
    "bright daylight, happy laughing",
]


def _load_db():
    if os.path.exists(config.CHARACTERS_DB):
        with open(config.CHARACTERS_DB, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_db(db):
    with open(config.CHARACTERS_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def _generate_hero(description, style_key):
    style = config.IMAGE_STYLES.get(style_key, config.IMAGE_STYLES["manhwa"])
    r = fal.run("fal-ai/flux/dev", {
        "prompt": f"{style}, {description}, single character, simple background, "
                  f"detailed face, high quality, full body or upper body",
        "image_size": "portrait_4_3",
        "num_inference_steps": 30,
    }, with_logs=False)
    return r["images"][0]["url"]


def _variation(hero_url, instruction):
    r = fal.run("fal-ai/flux-pro/kontext", {
        "prompt": f"same exact person, identical face and hair and outfit, {instruction}",
        "image_url": hero_url,
    }, with_logs=False)
    return r["images"][0]["url"]


def create_character(name, trigger_word, description, style="manhwa",
                     num_variations=10, steps=1000, progress_cb=None):
    def log(m):
        print(m)
        if progress_cb:
            try: progress_cb(m)
            except Exception: pass

    os.makedirs(config.TEMP_DIR, exist_ok=True)
    work = tempfile.mkdtemp(prefix="lora_", dir=config.TEMP_DIR)

    log(f"🎨 生成主參考圖：{name}")
    hero_url = _generate_hero(description, style)
    urls = [hero_url]

    prompts = VARIATION_PROMPTS[:num_variations]
    for i, instr in enumerate(prompts, 1):
        log(f"🖼️ 生成變化圖 {i}/{len(prompts)}：{instr}")
        try:
            urls.append(_variation(hero_url, instr))
        except Exception as e:
            log(f"    ⚠️ 變化圖失敗，跳過：{e}")

    log(f"📦 下載並打包 {len(urls)} 張訓練圖…")
    img_dir = os.path.join(work, "imgs")
    os.makedirs(img_dir, exist_ok=True)
    for i, u in enumerate(urls):
        fal.download(u, os.path.join(img_dir, f"img_{i:02d}.png"))
    zip_path = os.path.join(work, "train.zip")
    with zipfile.ZipFile(zip_path, "w") as z:
        for fn in os.listdir(img_dir):
            z.write(os.path.join(img_dir, fn), fn)

    log("☁️ 上載訓練資料到 fal…")
    zip_url = fal.upload_file(zip_path)

    log(f"🎓 訓練 LoRA（trigger: {trigger_word}, steps: {steps}），約 5–10 分鐘…")
    r = fal.run("fal-ai/flux-lora-fast-training", {
        "images_data_url": zip_url,
        "trigger_word": trigger_word,
        "steps": steps,
        "is_style": False,
    })
    lora_url = (r.get("diffusers_lora_file") or {}).get("url") or (r.get("lora_file") or {}).get("url")
    if not lora_url:
        raise RuntimeError("訓練完成但搵唔到 LoRA URL：" + str(r)[:200])

    db = [c for c in _load_db() if c.get("name") != name]  # 覆蓋同名
    char = {
        "name": name,
        "trigger_word": trigger_word,
        "description": description,
        "style": style,
        "lora_url": lora_url,
        "hero_image": hero_url,
        "created_at": int(time.time()),
    }
    db.append(char)
    _save_db(db)

    shutil.rmtree(work, ignore_errors=True)
    log(f"✅ 角色「{name}」已建立，LoRA 已存 fal：\n{lora_url}")
    return char


def interactive():
    print("=== LoRA 自訂角色 ===")
    name = input("角色名稱（中文都得，pipeline 用嚟對劇本）：").strip()
    trigger = input("Trigger word（英文無空格，例 ohwx_lily）：").strip()
    desc = input("外觀描述（英文較準，例 20yo asian woman, long black hair, red dress）：").strip()
    print("可選風格：" + ", ".join(config.IMAGE_STYLES))
    style = input("風格 [manhwa]：").strip() or "manhwa"
    n = input("變化圖數量 [10]：").strip()
    n = int(n) if n.isdigit() else 10
    create_character(name, trigger, desc, style, n)


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        create_character(sys.argv[1], sys.argv[2], sys.argv[3],
                         sys.argv[4] if len(sys.argv) > 4 else "manhwa")
    else:
        interactive()
