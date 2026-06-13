"""
末日農場 - 全自動製片系統 (Config-Driven)
Auto Film Production System - Manhwa Panel Edition

用法:
    python main.py --config stories/story_01.py

環境變數:
    FAL_KEY - Fal AI API Key
"""

import os
import sys
import json
import argparse
import subprocess
import importlib.util
import platform
import math
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# 自動讀取 .env
load_dotenv(Path(__file__).parent / ".env")

# ============================================================
# 配置 Configuration
# ============================================================

FAL_KEY = os.getenv("FAL_KEY", "")

# 視頻設定
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

# 漫畫頁設定
MANGA_PAGE_WIDTH = 1920
MANGA_PAGE_HEIGHT = 1080
PANEL_BORDER = 3
PANEL_GAP = 6
OUTER_MARGIN = 20


# ============================================================
# 工具函數 Utility Functions
# ============================================================

def log(msg):
    """打印日誌"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def save_json(data, filepath):
    """儲存 JSON 檔案"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def detect_chinese_font() -> str:
    """偵測系統中文字體"""
    system = platform.system()
    if system == "Linux":
        try:
            r = subprocess.run(["fc-list", ":lang=zh", "family"],
                               capture_output=True, text=True, check=True)
            fonts = [l.split(",")[0].split(":")[0].strip()
                     for l in r.stdout.strip().split("\n") if l.strip()]
            if not fonts:
                raise RuntimeError(
                    "❌ 未安裝中文字體!執行:\n"
                    " sudo apt install -y fonts-noto-cjk fonts-wqy-microhei && fc-cache -fv"
                )
            for pref in ["Noto Sans CJK SC", "Noto Sans CJK TC",
                         "WenQuanYi Micro Hei", "WenQuanYi Zen Hei"]:
                if any(pref in f for f in fonts):
                    return pref
            return fonts[0]
        except FileNotFoundError:
            return "Noto Sans CJK SC"
    return "PingFang SC" if system == "Darwin" else "Microsoft YaHei"


def load_config(config_path: str):
    """動態載入 .py story config"""
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config 檔案不存在: {config_path}")

    spec = importlib.util.spec_from_file_location("story_config", config_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "STORY"):
        raise ValueError(f"{config_path} 沒有定義 STORY 變量")

    return module.STORY


def download(url, save_path):
    """下載檔案"""
    import httpx
    if not save_path.exists():
        with httpx.Client(timeout=120) as client:
            response = client.get(url)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                f.write(response.content)
    return save_path


def run_command(cmd, description="", timeout=300):
    """執行命令（list → shell=False, str → shell=True）"""
    log(f"🔧 {description}...")
    try:
        use_shell = isinstance(cmd, str)
        result = subprocess.run(
            cmd,
            shell=use_shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode != 0:
            log(f"⚠️ 警告: {result.stderr[:500]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log(f"❌ 命令超時: {description}")
        return False


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def get_audio_duration(audio_path: Path) -> float:
    """用 ffprobe 取得音頻時長(秒)"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(audio_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    return 0.0


# ============================================================
# 安裝依賴
# ============================================================

def install_dependencies():
    """安裝所需套件"""
    log("📦 安裝依賴套件...")

    try:
        import fal_client
        log("✅ fal-client 已安裝")
    except ImportError:
        log("📦 安裝 fal-client...")
        run_command(
            f"{sys.executable} -m pip install --break-system-packages fal-client",
            "安裝 fal-client"
        )

    if subprocess.run("which ffmpeg", shell=True, capture_output=True).returncode != 0:
        log("⚠️ ffmpeg 未安裝,請手動安裝: sudo apt install ffmpeg")
    else:
        log("✅ ffmpeg 已就緒")


# ============================================================
# Phase 1: 角色 Reference Images
# ============================================================

def load_characters_db():
    """讀取 characters.json（LoRA 角色資料庫）"""
    db_path = Path(__file__).parent / "characters.json"
    if db_path.exists():
        with open(db_path, encoding="utf-8") as f:
            return json.load(f)
    return {"characters": []}


def generate_character_images(config):
    """生成所有角色嘅 reference image（Flux Pro + LoRA）"""
    import fal_client

    char_cache_dir = Path(config.output_dir) / "characters"
    ensure_dir(char_cache_dir)

    char_db = load_characters_db()
    lora_chars = {c["name"]: c for c in char_db.get("characters", [])}

    for char in config.characters:
        if not char.appearance_prompt:
            log(f"⏭️  角色 [{char.id}] ({char.name}) - 無外貌描述,跳過")
            continue

        cache_file = char_cache_dir / f"{char.id}.png"

        if cache_file.exists():
            log(f"⏭️  角色 [{char.id}] ({char.name}) - 使用快取")
            char.ref_image_url = str(cache_file)
            continue

        lora_char = lora_chars.get(char.name)

        # 用 Flux Pro + LoRA
        if lora_char and lora_char.get("lora_url"):
            log(f"🎓 角色 [{char.id}] ({char.name}) - Flux Pro + LoRA: {lora_char['trigger_word']}")
            try:
                result = fal_client.subscribe(
                    "fal-ai/flux-pro/v1.1",
                    arguments={
                        "prompt": f"{lora_char['trigger_word']}, {char.appearance_prompt}",
                        "image_size": {"width": 1024, "height": 1024},
                        "num_inference_steps": 40,
                        "guidance_scale": 3.5,
                        "seed": config.global_seed,
                        "enable_safety_checker": False,
                        "loras": [{"path": lora_char["lora_url"], "scale": 0.85}],
                    },
                    with_logs=False,
                )
                image_url = result["images"][0]["url"]
                download(image_url, cache_file)
                char.ref_image_url = str(cache_file)
                log(f"✅ 角色 [{char.id}] ({char.name}) Flux Pro 圖已快取: {cache_file}")
                continue
            except Exception as e:
                log(f"⚠️  Flux Pro + LoRA 失敗，回落: {e}")

        # 回落 Flux Pro 無 LoRA
        log(f"🖼️  生成角色 [{char.id}] ({char.name}) reference image (Flux Pro)...")
        try:
            result = fal_client.subscribe(
                "fal-ai/flux-pro/v1.1",
                arguments={
                    "prompt": char.appearance_prompt,
                    "image_size": {"width": 1024, "height": 1024},
                    "num_inference_steps": 40,
                    "guidance_scale": 3.5,
                    "seed": config.global_seed,
                    "enable_safety_checker": False,
                },
                with_logs=False,
            )
            image_url = result["images"][0]["url"]
            download(image_url, cache_file)
            char.ref_image_url = str(cache_file)
            log(f"✅ 角色 [{char.id}] ({char.name}) 已快取: {cache_file}")
        except Exception as e:
            log(f"❌ 角色 [{char.id}] ({char.name}) 生成失敗: {e}")


# ============================================================
# Phase 2: 場景圖片 (Flux Pro + LoRA)
# ============================================================

def build_scene_prompt(scene, config):
    """將角色 placeholder 換成描述，有 LoRA 嘅加 trigger word，禁止生成文字"""
    char_db = load_characters_db()
    lora_chars = {c["name"]: c for c in char_db.get("characters", [])}

    prompt = scene.scene_prompt
    for char_id in scene.characters_in_scene:
        char = next((c for c in config.characters if c.id == char_id), None)
        if char:
            lora_char = lora_chars.get(char.name)
            if lora_char and lora_char.get("lora_url"):
                replacement = f"{lora_char['trigger_word']} ({char.name})"
            else:
                replacement = char.name
            prompt = prompt.replace("{" + char_id + "}", replacement)

    # 禁止 AI 生成任何文字（文字由 Pillow 後期 overlay）
    prompt += ", no text, no words, no letters, no writing, no speech bubbles, no dialogue boxes, no captions, no titles, no signs with text, pure illustration only"
    return prompt


def _get_scene_loras(scene, config):
    """收集場景中所有有 LoRA 嘅角色"""
    char_db = load_characters_db()
    lora_chars = {c["name"]: c for c in char_db.get("characters", [])}

    loras = []
    lora_char_ids = []
    non_lora_char_ids = []

    for cid in scene.characters_in_scene:
        char = next((c for c in config.characters if c.id == cid), None)
        if char:
            lora_char = lora_chars.get(char.name)
            if lora_char and lora_char.get("lora_url"):
                loras.append({"path": lora_char["lora_url"], "scale": 0.85})
                lora_char_ids.append(cid)
            else:
                non_lora_char_ids.append(cid)

    return loras, lora_char_ids, non_lora_char_ids


def generate_scene_images(config):
    """生成所有場景圖片（Flux Dev + Anime LoRA + IP-Adapter + ControlNet）"""
    import fal_client
    import base64
    from PIL import Image, ImageDraw

    scenes_dir = Path(config.output_dir) / "scenes"
    ensure_dir(scenes_dir)

    # Anime LoRA (Animagine XL 3.1)
    ANIME_LORA = {
        "path": "https://huggingface.co/Linaqruf/animagine-xl-3.1/blob/main/animagine-xl-3.1.safetensors",
        "scale": 0.8
    }

    for scene in config.scenes:
        img_path = scenes_dir / f"scene_{scene.id:02d}_image.png"

        # 快取優先
        if img_path.exists():
            log(f"⏭️  場景 {scene.id} - 使用現有圖片")
            continue

        prompt = build_scene_prompt(scene, config)

        # 收集角色 reference images
        image_refs = []
        if scene.characters_in_scene:
            for char_id in scene.characters_in_scene:
                char = next((c for c in config.characters if c.id == char_id), None)
                if char and char.ref_image_url and Path(char.ref_image_url).exists():
                    ref_data = Path(char.ref_image_url).read_bytes()
                    b64 = base64.b64encode(ref_data).decode()
                    ref_url = f"data:image/png;base64,{b64}"
                    image_refs.append({"image_url": ref_url, "strength": 0.8})

        # 生成 ControlNet pose（如果有角色）
        control_image_url = None
        if scene.characters_in_scene:
            # 簡單站立姿勢
            pose = Image.new('RGB', (1024, 576), 'black')
            draw = ImageDraw.Draw(pose)
            draw.ellipse([462, 80, 562, 180], outline='white', width=5)  # head
            draw.line([512, 180, 512, 350], fill='white', width=5)  # body
            draw.line([512, 250, 400, 350], fill='white', width=5)  # left arm
            draw.line([512, 250, 624, 350], fill='white', width=5)  # right arm
            draw.line([512, 350, 420, 500], fill='white', width=5)  # left leg
            draw.line([512, 350, 604, 500], fill='white', width=5)  # right leg

            import io
            buffer = io.BytesIO()
            pose.save(buffer, format='PNG')
            pose_b64 = base64.b64encode(buffer.getvalue()).decode()
            control_image_url = f"data:image/png;base64,{pose_b64}"

        # Flux Dev + Anime LoRA
        log(f"🎨 場景 {scene.id} - Flux Dev + Anime LoRA" +
            (f" + IP-Adapter({len(image_refs)})" if image_refs else "") +
            (" + ControlNet" if control_image_url else ""))

        try:
            arguments = {
                "prompt": prompt,
                "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, blurry, jpeg artifacts, watermark, deformed",
                "image_size": {"width": 1024, "height": 576},
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "seed": config.global_seed + scene.id,
                "enable_safety_checker": False,
                "loras": [ANIME_LORA]
            }

            if image_refs:
                arguments["image_references"] = image_refs

            if control_image_url:
                arguments["controlnet_conditioning_scale"] = 0.8
                arguments["control_image_url"] = control_image_url

            result = fal_client.subscribe(
                "fal-ai/flux/dev",
                arguments=arguments,
                with_logs=False,
            )
            image_url = result["images"][0]["url"]
            download(image_url, img_path)
            log(f"✅ 場景 {scene.id} 圖片完成: {img_path}")

        except Exception as e:
            log(f"❌ 場景 {scene.id} 圖片生成失敗: {e}")


# ============================================================
# Phase 3: TTS 音頻
# ============================================================

# ── 粵語 → 普通話轉換（TTS 配音用）──────────────────
_YUE_TO_MANDARIN = [
    ("白手興家", "白手起家"),
    ("走馬燈一樣", "走马灯一样"),
    ("一個一個", "一个一个"),
    ("可以返去", "可以回去"),
    ("返去報仇", "回去报仇"),
    ("佢哋", "他们"), ("我哋", "我们"), ("你哋", "你们"), ("佢", "他"),
    ("呢啲", "这些"), ("嗰啲", "那些"),
    ("呢個", "这个"), ("嗰個", "那个"),
    ("呢度", "这里"), ("嗰度", "那里"),
    ("呢種", "这种"), ("嗰種", "那种"),
    ("呢次", "这次"), ("嗰次", "那次"),
    ("呢一切", "这一切"),
    ("唔係", "不是"), ("係", "是"),
    ("冇", "没有"),
    ("返嚟", "回来"), ("返去", "回去"), ("返", "回"),
    ("行嚟", "走来"), ("行去", "走去"),
    ("衝上", "冲上"),
    ("聽到", "听到"), ("睇到", "看到"), ("見到", "看到"),
    ("觸踫", "触碰"),
    ("俾", "给"), ("搵", "找"), ("諗", "想"), ("睇", "看"),
    ("企喺", "站在"),
    ("嘅", "的"), ("咗", "了"), ("過", "过"), ("緊", "着"),
    ("唔", "不"),
    ("嚟", "来"),
    ("點解", "为什么"), ("點樣", "怎样"),
    ("咩", "什么"), ("邊個", "谁"),
    ("仲有", "还有"), ("但係", "但是"),
    ("因為", "因为"), ("所以", "所以"),
    ("如果", "如果"), ("只要", "只要"), ("只有", "只有"),
    ("曾經", "曾经"), ("以為", "以为"), ("明白", "明白"),
    ("一齊", "一起"), ("多謝", "谢谢"),
    ("拍檔", "搭档"), ("恩師", "恩师"),
    ("未婚妻", "未婚妻"), ("跳板", "跳板"),
    ("咁", "这么"), ("噉", "这样"), ("嘢", "东西"),
]

def to_mandarin(text: str) -> str:
    """將粵語口語轉為普通話書面語（TTS 配音用）"""
    result = text
    for yue, mandarin in _YUE_TO_MANDARIN:
        result = result.replace(yue, mandarin)
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')
        result = cc.convert(result)
    except ImportError:
        pass
    return result


def to_traditional(text: str) -> str:
    """將文本轉為繁體中文（字幕用）"""
    try:
        from opencc import OpenCC
        cc = OpenCC('s2t')
        return cc.convert(text)
    except ImportError:
        return text


def generate_tts(config):
    """生成所有場景 TTS（普通話配音）"""
    import fal_client

    audio_dir = Path(config.output_dir) / "audio"
    ensure_dir(audio_dir)

    for scene in config.scenes:
        aud_path = audio_dir / f"scene_{scene.id:02d}_audio.mp3"

        if aud_path.exists():
            log(f"⏭️  場景 {scene.id} - 使用現有音頻")
            scene.duration = get_audio_duration(aud_path)
            continue

        speaker_char = next(
            (c for c in config.characters if c.id == scene.speaker),
            None
        )
        if speaker_char:
            voice_id = speaker_char.voice_id
            speed = speaker_char.voice_speed
            pitch = speaker_char.voice_pitch
        else:
            voice_id = "Chinese_Mature_Male_Narrator"
            speed = 1.0
            pitch = 0

        tts_text = to_mandarin(scene.narration)
        log(f"🔊 場景 {scene.id} TTS: {tts_text[:30]}... (voice={voice_id})")

        try:
            result = fal_client.subscribe(
                "fal-ai/minimax/speech-02-turbo",
                arguments={
                    "text": tts_text,
                    "stream": False,
                    "model": "speech-02-turbo",
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": speed,
                        "vol": 1.0,
                        "pitch": pitch,
                    },
                    "audio_setting": {
                        "sample_rate": 32000,
                        "bitrate": 128000,
                        "format": "mp3",
                        "channel": 1,
                    },
                    "language_boost": "Chinese",
                    "output_format": "url",
                },
                with_logs=False,
            )
            audio_url = result["audio"]["url"]
            download(audio_url, aud_path)
            scene.duration = get_audio_duration(aud_path)
            log(f"✅ 場景 {scene.id} 音頻完成 ({scene.duration:.1f}s): {aud_path}")

        except Exception as e:
            log(f"❌ 場景 {scene.id} TTS 生成失敗: {e}")


# ============================================================
# Phase 4: 漫畫分鏡頁 (Manhwa Panel Layout)
# ============================================================

def _get_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """取得字體，失敗就回落預設"""
    try:
        # 試下用 fc-match 搵字體路徑
        r = subprocess.run(
            ["fc-match", f"{font_name}:file"],
            capture_output=True, text=True
        )
        font_path = r.stdout.strip().split(":")[0].strip()
        if font_path and Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    except Exception:
        pass
    # 回落：直接試常見路徑
    for fp in [
        "/home/charlesai/.fonts/NotoSansSC-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def _text_to_lines(text: str, max_chars: int = 12) -> list:
    """將文字拆成多行（中文不拆字，按 max_chars 換行）"""
    if not text:
        return []
    lines = []
    for i in range(0, len(text), max_chars):
        lines.append(text[i:i+max_chars])
    return lines


def _draw_speech_bubble(draw: ImageDraw.Draw, img: Image.Image, text: str,
                        position: tuple, font: ImageFont.FreeTypeFont,
                        font_name: str = "Noto Sans CJK SC"):
    """畫對話框（橢圓形白底黑字 + 尾巴）"""
    # 計算文字大小
    trad_text = to_traditional(to_mandarin(text))
    lines = _text_to_lines(trad_text, 10)
    if not lines:
        return

    line_height = font.size + 4
    text_width = max(font.getlength(line) for line in lines)
    text_height = line_height * len(lines)

    # 橢圓 bubble 尺寸（加 padding）
    pad_x, pad_y = 24, 16
    bw = text_width + pad_x * 2
    bh = text_height + pad_y * 2
    bw = max(bw, 80)
    bh = max(bh, 50)

    # bubble 中心
    bx, by = position
    x0 = bx - bw // 2
    y0 = by - bh // 2
    x1 = bx + bw // 2
    y1 = by + bh // 2

    # 確保喺畫面內
    x0 = max(10, x0)
    y0 = max(10, y0)
    x1 = min(img.width - 10, x1)
    y1 = min(img.height - 10, y1)

    # 畫橢圓白底
    draw.ellipse([x0, y0, x1, y1], fill="white", outline="black", width=2)

    # 畫尾巴（三角形指向下方）
    tail_cx = (x0 + x1) // 2
    tail_top = y1 - 2
    tail_bottom = y1 + 20
    draw.polygon([
        (tail_cx - 8, tail_top),
        (tail_cx + 8, tail_top),
        (tail_cx, tail_bottom)
    ], fill="white", outline="black", width=1)
    # 蓋住連接處嘅邊
    draw.line([(tail_cx - 9, tail_top), (tail_cx + 9, tail_top)], fill="white", width=3)

    # 寫文字
    ty = y0 + pad_y
    for line in lines:
        lw = font.getlength(line)
        tx = x0 + (bw - lw) // 2
        draw.text((tx, ty), line, fill="black", font=font)
        ty += line_height


def _draw_narration_box(draw: ImageDraw.Draw, img: Image.Image, text: str,
                        position: str, font: ImageFont.FreeTypeFont,
                        panel_x: int = 0, panel_y: int = 0,
                        panel_w: int = 0, panel_h: int = 0):
    """畫旁白框（半透明黑底白字，放喺 panel 頂部或底部）"""
    trad_text = to_traditional(to_mandarin(text))
    lines = _text_to_lines(trad_text, 18)
    if not lines:
        return

    line_height = font.size + 4
    text_width = max(font.getlength(line) for line in lines)
    text_height = line_height * len(lines)

    pad_x, pad_y = 16, 8
    box_w = text_width + pad_x * 2
    box_h = text_height + pad_y * 2

    # 用 panel 坐標（如果提供），否則用全頁
    pw = panel_w if panel_w > 0 else img.width
    px = panel_x
    py = panel_y

    x0 = px + (pw - box_w) // 2
    if position == "top":
        y0 = py + 10
    else:
        y0 = py + (panel_h if panel_h > 0 else img.height) - box_h - 10

    x1 = x0 + box_w
    y1 = y0 + box_h

    # 確保唔超出 panel 範圍
    x0 = max(px + 4, x0)
    x1 = min(px + pw - 4, x1)

    # 半透明黑底
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill=(0, 0, 0, 200))
    if img.mode == "RGBA":
        img.paste(Image.alpha_composite(img, overlay))
    else:
        img_rgba = img.convert("RGBA")
        img_rgba.paste(Image.alpha_composite(img_rgba, overlay))
        img.paste(img_rgba.convert("RGB"))

    # 寫白字
    ty = y0 + pad_y
    for line in lines:
        lw = font.getlength(line)
        tx = x0 + (x1 - x0 - lw) // 2
        draw.text((tx, ty), line, fill="white", font=font)
        ty += line_height


def _choose_layout(shot_types: list) -> str:
    """根據 shot_type 選擇 panel 佈局"""
    has_wide = "wide_shot" in shot_types
    has_close = "close_up" in shot_types
    n = len(shot_types)

    if n <= 1:
        return "1x1"
    elif n == 2:
        if has_wide:
            return "1+1_h"  # 上下兩格（wide 在上面）
        return "1x2"  # 左右兩格
    elif n == 3:
        if has_wide:
            return "1+2"  # 上面一 wide，下面兩格
        return "2+1"  # 上面兩格，下面一 wide
    else:  # n == 4
        return "2x2"


def _compute_panel_rects(layout: str, page_w: int, page_h: int) -> list:
    """根據佈局計算各 panel 嘅 rect (x, y, w, h)"""
    m = OUTER_MARGIN
    g = PANEL_GAP
    usable_w = page_w - 2 * m
    usable_h = page_h - 2 * m

    rects = []

    if layout == "1x1":
        rects.append((m, m, usable_w, usable_h))

    elif layout == "1x2":
        pw = (usable_w - g) // 2
        rects.append((m, m, pw, usable_h))
        rects.append((m + pw + g, m, usable_w - pw - g, usable_h))

    elif layout == "1+1_h":
        ph = (usable_h - g) // 2
        rects.append((m, m, usable_w, ph))
        rects.append((m, m + ph + g, usable_w, usable_h - ph - g))

    elif layout == "2x2":
        pw = (usable_w - g) // 2
        ph = (usable_h - g) // 2
        rects.append((m, m, pw, ph))
        rects.append((m + pw + g, m, usable_w - pw - g, ph))
        rects.append((m, m + ph + g, pw, usable_h - ph - g))
        rects.append((m + pw + g, m + ph + g, usable_w - pw - g, usable_h - ph - g))

    elif layout == "1+2":
        top_h = int(usable_h * 0.45)
        bot_h = usable_h - top_h - g
        pw = (usable_w - g) // 2
        rects.append((m, m, usable_w, top_h))
        rects.append((m, m + top_h + g, pw, bot_h))
        rects.append((m + pw + g, m + top_h + g, usable_w - pw - g, bot_h))

    elif layout == "2+1":
        top_h = int(usable_h * 0.55)
        bot_h = usable_h - top_h - g
        pw = (usable_w - g) // 2
        rects.append((m, m, pw, top_h))
        rects.append((m + pw + g, m, usable_w - pw - g, top_h))
        rects.append((m, m + top_h + g, usable_w, bot_h))

    return rects


def _composite_panel(page: Image.Image, panel_img: Image.Image, rect: tuple,
                     scene, font_name: str):
    """將 scene 圖片貼到 panel 區域，加上對話框/旁白"""
    px, py, pw, ph = rect

    # resize panel 圖
    panel_resized = panel_img.resize((pw, ph), Image.Resampling.LANCZOS)

    # 貼到 page
    page.paste(panel_resized, (px, py))

    # 畫 panel border
    draw = ImageDraw.Draw(page)
    draw.rectangle([px, py, px + pw - 1, py + ph - 1],
                   outline="black", width=PANEL_BORDER)

    # 對話框
    bubble_font = _get_font(font_name, max(16, min(22, pw // 40)))
    narr_font = _get_font(font_name, max(16, min(20, pw // 45)))

    narration = scene.narration
    speaker = scene.speaker

    if speaker != "narrator" and narration:
        # 角色對話 → speech bubble
        bubble_cx = px + pw // 2
        bubble_cy = py + ph // 3  # 上方 1/3
        _draw_speech_bubble(draw, page, narration, (bubble_cx, bubble_cy),
                           bubble_font, font_name)
    elif speaker == "narrator" and narration:
        # 旁白 → 矩形半透明框（頂部），傳入 panel 坐標
        _draw_narration_box(draw, page, narration, "top", narr_font,
                           panel_x=px, panel_y=py, panel_w=pw, panel_h=ph)


def generate_manga_pages(config, font_name: str):
    """每個 scene 一張 full-page 漫畫圖（無對話框，字幕後期加）"""
    scenes_dir = Path(config.output_dir) / "scenes"
    pages_dir = Path(config.output_dir) / "manga_pages"
    ensure_dir(pages_dir)

    valid_scenes = []
    for scene in config.scenes:
        img_path = scenes_dir / f"scene_{scene.id:02d}_image.png"
        if img_path.exists():
            valid_scenes.append((scene, img_path))
        else:
            log(f"⚠️ 場景 {scene.id} 無圖片，跳過")

    if not valid_scenes:
        log("❌ 無任何場景圖片可合成")
        return

    log(f"📖 共 {len(valid_scenes)} 頁全幅漫畫")

    for page_idx, (scene, img_path) in enumerate(valid_scenes):
        page_path = pages_dir / f"page_{page_idx+1:02d}.png"

        if page_path.exists():
            log(f"⏭️  第 {page_idx+1} 頁 - 使用現有頁面")
            continue

        # 直接 resize 成 1920×1080（加黑色邊框 fill）
        img = Image.open(img_path).convert("RGB")
        # 按比例 resize 並居中（letterbox）
        img_ratio = img.width / img.height
        page_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

        if img_ratio > page_ratio:
            # 圖片較寬 → fit width
            new_w = VIDEO_WIDTH
            new_h = int(VIDEO_WIDTH / img_ratio)
        else:
            # 圖片較高 → fit height
            new_h = VIDEO_HEIGHT
            new_w = int(VIDEO_HEIGHT * img_ratio)

        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 黑色背景
        page = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0))
        x_off = (VIDEO_WIDTH - new_w) // 2
        y_off = (VIDEO_HEIGHT - new_h) // 2
        page.paste(img_resized, (x_off, y_off))

        page.save(page_path, quality=95)
        log(f"✅ 第 {page_idx+1} 頁完成: {page_path}")

    return valid_scenes


# ============================================================
# Phase 5: 漫畫頁 → 視頻
# ============================================================

# ── Ken Burns + 呼吸 + 調色 filter 產生 ────────────────
_KB_MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]

def _build_scene_vf(duration: float, motion: str, fps: int = VIDEO_FPS) -> str:
    """產生 ffmpeg filter chain：Ken Burns + 呼吸 pulse + 調色 + vignette"""
    frames = max(int(duration * fps), 1)

    # 1) Ken Burns zoompan
    if motion == "zoom_in":
        z = "1+0.06*on/" + str(frames)
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "zoom_out":
        z = "1.06-0.06*on/" + str(frames)
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z = "1.06"
        x = "(iw-iw/zoom)*on/" + str(frames)
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z = "1.06"
        x = "(iw-iw/zoom)*(1-on/" + str(frames) + ")"
        y = "ih/2-(ih/zoom/2)"
    elif motion == "pan_down":
        z = "1.06"
        x = "iw/2-(iw/zoom/2)"
        y = "(ih-ih/zoom)*on/" + str(frames)
    else:  # pan_up or static → slight zoom_in
        z = "1+0.04*on/" + str(frames)
        x, y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"

    zoompan = (
        f"zoompan=z='{z}':x='{x}':y='{y}':"
        f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={fps}"
    )

    # 2) 呼吸 pulse（輕微 scale 1.00~1.02 循環，模擬角色微動）
    breathe = (
        f"scale={int(VIDEO_WIDTH*1.04)}:{int(VIDEO_HEIGHT*1.04)},"
        f"zoompan=z='1+0.01*sin(2*PI*on/{frames})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:fps={fps}"
    )

    # 3) 調色：冷色調 + 高對比 + 輕微 vignette
    color = "eq=contrast=1.08:saturation=1.15:brightness=-0.02"
    cool = "colorbalance=bs=0.08:bm=0.05:bh=0.03:gs=-0.02:gm=-0.01"
    vignette = "vignette=PI/4"

    # 組合（zoompan 已經 output 正確尺寸，之後加 breathe + color + vignette）
    return f"{zoompan},{breathe},{color},{cool},{vignette}"


def concat_manga_pages(config, font_name: str):
    """每個 scene 一張全幅圖 + Ken Burns + 呼吸 + 調色 + fade 轉場"""
    import random
    pages_dir = Path(config.output_dir) / "manga_pages"
    video_dir = Path(config.output_dir) / "page_videos"
    ensure_dir(video_dir)

    valid_scenes = []
    for scene in config.scenes:
        img_path = Path(config.output_dir) / "scenes" / f"scene_{scene.id:02d}_image.png"
        if img_path.exists():
            valid_scenes.append(scene)

    page_files = sorted(pages_dir.glob("page_??.png"))
    if not page_files:
        log("❌ 無漫畫頁可合成")
        return None

    random.seed(config.global_seed if hasattr(config, 'global_seed') else 42)
    page_videos = []

    for page_idx, page_file in enumerate(page_files):
        vid_path = video_dir / f"page_{page_idx+1:02d}.mp4"

        # 時長 = TTS 時長
        if page_idx < len(valid_scenes):
            page_duration = max(valid_scenes[page_idx].duration, 2.0) if valid_scenes[page_idx].duration > 0 else 3.0
            shot = valid_scenes[page_idx].motion if hasattr(valid_scenes[page_idx], 'motion') else random.choice(_KB_MOTIONS)
        else:
            page_duration = 3.0
            shot = random.choice(_KB_MOTIONS)

        page_duration = max(page_duration, 2.0)

        if not vid_path.exists():
            vf = _build_scene_vf(page_duration, shot)
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(page_file),
                "-t", str(page_duration),
                "-vf", vf,
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p", "-r", str(VIDEO_FPS),
                str(vid_path),
            ]
            run_command(cmd, f"第 {page_idx+1} 頁 KB[{shot}] ({page_duration:.1f}s)")

        if vid_path.exists():
            page_videos.append((vid_path, page_duration))
            log(f"✅ 第 {page_idx+1} 頁完成 ({page_duration:.1f}s, {shot})")

    if not page_videos:
        log("❌ 無頁面視頻可合併")
        return None

    # ── 用 xfade 轉場合成（fade 0.5 秒） ──
    combined_video = Path(config.output_dir) / "combined_video.mp4"
    fade_dur = 0.5

    if len(page_videos) == 1:
        # 只有一段，直接 copy
        import shutil
        shutil.copy2(str(page_videos[0][0]), str(combined_video))
        log(f"✅ 視頻已合併: {combined_video}")
        return combined_video

    # 多段 xfade chain
    # ffmpeg -i a.mp4 -i b.mp4 -i c.mp4 ...
    #   -filter_complex "[0][1]xfade=transition=fade:duration=0.5:offset=X[v01]; [v01][2]xfade=..."
    inputs = []
    for vf, _ in page_videos:
        inputs.extend(["-i", str(vf)])

    offsets = []
    cumul = 0.0
    for i in range(len(page_videos) - 1):
        cumul += page_videos[i][1] - fade_dur
        offsets.append(cumul)

    filter_parts = []
    n = len(page_videos)
    for i in range(n - 1):
        src1 = f"[{i}]" if i == 0 else f"[v{i-1:02d}]"
        src2 = f"[{i+1}]"
        out = f"[v{i:02d}]" if i < n - 2 else "[vout]"
        offset = offsets[i]
        filter_parts.append(
            f"{src1}{src2}xfade=transition=fade:duration={fade_dur}:offset={offset:.2f}{out}"
        )

    filter_complex = ";".join(filter_parts)

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(VIDEO_FPS),
        str(combined_video),
    ]

    if run_command(cmd, "合併視頻（xfade 轉場）", timeout=600):
        log(f"✅ 視頻已合併（含轉場）: {combined_video}")
        return combined_video

    # fallback: simple concat
    log("⚠️ xfade 失敗，回落 concat")
    list_file = Path(config.output_dir) / "concat_list.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for vf, _ in page_videos:
            f.write(f"file '{vf.absolute()}'\n")
    cmd2 = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file), "-c", "copy",
        str(combined_video),
    ]
    if run_command(cmd2, "合併視頻（fallback）"):
        log(f"✅ 視頻已合併: {combined_video}")
        return combined_video
    return None


# ============================================================
# Phase 6: 背景音樂
# ============================================================

def generate_background_music(config):
    """用 Fal AI Music 生成背景音樂"""
    import fal_client

    from stories.music_presets import MUSIC_PRESETS
    preset = MUSIC_PRESETS.get(config.music_style, MUSIC_PRESETS["gentle_emotional"])
    music_prompt = preset["prompt"]

    output_dir = Path(config.output_dir)
    music_path = output_dir / "background_music.mp3"

    if music_path.exists():
        log("⏭️  背景音樂已存在,跳過")
        return music_path

    total_duration = sum(s.duration for s in config.scenes)
    log(f"🎵 生成背景音樂 ({config.music_style}: {preset['mood']})...")

    try:
        result = fal_client.subscribe(
            "fal-ai/music/generate",
            arguments={
                "prompt": music_prompt,
                "duration": min(total_duration + 10, 180),
                "make_spatial_audio": False,
            },
            with_logs=True,
        )
        music_url = result["audio"]["url"]
        download(music_url, music_path)
        log(f"✅ 背景音樂完成: {music_path}")
        return music_path

    except Exception as e:
        log(f"❌ 背景音樂生成失敗: {e}")
        return None


def merge_audio_video(config, video_path, output_path):
    """合併視頻 + TTS 旁白 + 背景音樂"""
    log("🎵 合併音頻與視頻...")

    audio_dir = Path(config.output_dir) / "audio"
    music_path = Path(config.output_dir) / "background_music.mp3"

    # 合併所有 TTS 音頻
    audio_files = sorted([
        audio_dir / f"scene_{s.id:02d}_audio.mp3"
        for s in config.scenes
        if (audio_dir / f"scene_{s.id:02d}_audio.mp3").exists()
    ])

    if not audio_files:
        log("❌ 無 TTS 音頻可合併")
        return False

    audio_combined = Path(config.output_dir) / "narration_combined.mp3"
    if len(audio_files) == 1:
        audio_combined = audio_files[0]
    else:
        audio_list = Path(config.output_dir) / "audio_list.txt"
        with open(audio_list, "w", encoding="utf-8") as f:
            for af in audio_files:
                f.write(f"file '{af.absolute()}'\n")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(audio_list), "-c:a", "libmp3lame",
            str(audio_combined),
        ]
        run_command(cmd, "合併旁白音頻")

    # 視頻 + 旁白 + BGM 三合一
    if music_path.exists():
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_combined),
            "-i", str(music_path),
            "-filter_complex",
            "[1:a]volume=1.0[narr];[2:a]volume=0.25[bgm];"
            "[narr][bgm]amix=inputs=2:duration=first:dropout_transition=2[dub]",
            "-map", "0:v", "-map", "[dub]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]
        if run_command(cmd, "合併視頻+旁白+BGM"):
            log(f"✅ 最終影片: {output_path}")
            return True
        log("⚠️  BGM 混合失敗，回落無 BGM")

    # 回落：視頻 + 旁白（無 BGM）
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_combined),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(output_path),
    ]
    if run_command(cmd, "合併視頻與音頻"):
        log(f"✅ 最終影片: {output_path}")
        return True
    return False


# ============================================================
# Phase 7: 字幕
# ============================================================

def wrap_chinese(text: str, width: int = 20) -> str:
    """中文字幕自動換行"""
    if len(text) <= width:
        return text
    result = []
    for i in range(0, len(text), width):
        result.append(text[i:i + width])
    return "\n".join(result)


def srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def add_subtitles(config, video_path, font, output_path):
    """SRT UTF-8 with BOM — 繁體中文字幕"""
    log("📝 添加繁體字幕...")

    srt_path = Path(config.output_dir) / "subtitles.srt"

    # 按 scene 計算累計時長
    cumul = 0.0
    lines = []
    for i, scene in enumerate(config.scenes):
        duration = max(scene.duration, 2.0) if scene.duration > 0 else 3.0
        start_time = cumul
        end_time = cumul + duration
        cumul = end_time

        subtitle_text = to_traditional(to_mandarin(scene.narration))

        lines.append(str(i + 1))
        lines.append(f"{srt_time(start_time)} --> {srt_time(end_time)}")
        lines.append(wrap_chinese(subtitle_text, 20))
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8-sig")

    srt_esc = str(srt_path.absolute()).replace("\\", "/").replace(":", "\\:")

    style = (
        f"FontName={font},FontSize=22,"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"BackColour=&H80000000,"
        f"BorderStyle=1,Outline=2,Shadow=1,"
        f"Alignment=2,MarginV=20"
    )
    vf = f"subtitles='{srt_esc}':charenc=UTF-8:force_style='{style}'"

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", vf, "-c:a", "copy",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        str(output_path),
    ]

    if run_command(cmd, "添加字幕"):
        log(f"✅ 字幕已添加: {output_path}")
        return True
    return False


# ============================================================
# 主流程 Main Pipeline
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="末日農場 - 韓漫風格分鏡製片系統")
    parser.add_argument("--config", required=True, help="劇本 config 檔案")
    args = parser.parse_args()

    print("=" * 60)
    print("🎬 末日農場 - 韓漫風格分鏡製片系統")
    print("=" * 60)

    log(f"📄 載入劇本: {args.config}")
    config = load_config(args.config)
    log(f"📋 標題: {config.title}")
    log(f"🎭 角色: {len(config.characters)} 個")
    log(f"🎬 場景: {len(config.scenes)} 個")
    log(f"🎵 音樂風格: {config.music_style}")

    if not FAL_KEY:
        raise RuntimeError("❌ 請先設定環境變數: export FAL_KEY=你嘅_key")
    os.environ["FAL_KEY"] = FAL_KEY

    install_dependencies()

    ensure_dir(config.output_dir)
    ensure_dir(Path(config.output_dir) / "characters")
    ensure_dir(Path(config.output_dir) / "scenes")
    ensure_dir(Path(config.output_dir) / "audio")
    ensure_dir(Path(config.output_dir) / "manga_pages")
    ensure_dir(Path(config.output_dir) / "page_videos")

    font = detect_chinese_font()
    log(f"🔤 中文字體: {font}")

    save_json(
        {
            "story_id": config.story_id,
            "title": config.title,
            "music_style": config.music_style,
            "scenes": [
                {"id": s.id, "speaker": s.speaker, "narration": s.narration,
                 "shot_type": s.shot_type, "characters_in_scene": s.characters_in_scene}
                for s in config.scenes
            ]
        },
        Path(config.output_dir) / "script.json"
    )

    # ===== Phase 1: 角色 Reference Images =====
    log(f"\n{'='*50}")
    log("🎭 Phase 1: 生成角色 Reference Images")
    log("=" * 50)
    generate_character_images(config)

    # ===== Phase 2: 場景圖片 (Flux Pro) =====
    log(f"\n{'='*50}")
    log("🖼️  Phase 2: 生成場景圖片 (Flux Pro + LoRA)")
    log("=" * 50)
    generate_scene_images(config)

    # ===== Phase 3: TTS =====
    log(f"\n{'='*50}")
    log("🔊 Phase 3: 生成旁白 (TTS)")
    log("=" * 50)
    generate_tts(config)

    # ===== Phase 4: 漫畫分鏡頁 =====
    log(f"\n{'='*50}")
    log("📖 Phase 4: 生成漫畫分鏡頁")
    log("=" * 50)
    generate_manga_pages(config, font)

    # ===== Phase 5: 漫畫頁 → 視頻 =====
    log(f"\n{'='*50}")
    log("🎬 Phase 5: 漫畫頁合成視頻")
    log("=" * 50)
    combined_video = concat_manga_pages(config, font)

    if not combined_video:
        log("❌ 視頻合成失敗")
        return

    # ===== Phase 6: 背景音樂 =====
    log(f"\n{'='*50}")
    log("🎵 Phase 6: 生成背景音樂")
    log("=" * 50)
    generate_background_music(config)

    # ===== Phase 7: 合併音頻 + 視頻 =====
    log(f"\n{'='*50}")
    log("🎵 Phase 7: 合併視頻與音頻")
    log("=" * 50)

    final_video = Path(config.output_dir) / f"{config.story_id}_final.mp4"
    merge_audio_video(config, str(combined_video), str(final_video))

    # ===== Phase 8: 字幕 =====
    if final_video.exists():
        log(f"\n{'='*50}")
        log("📝 Phase 8: 添加字幕")
        log("=" * 50)
        final_with_subs = Path(config.output_dir) / f"{config.story_id}_with_subtitles.mp4"
        add_subtitles(config, str(final_video), font, str(final_with_subs))

    # ===== 完成 =====
    log("\n" + "=" * 60)
    print("🎉🎉🎉 製作完成! 🎉🎉🎉")
    print("=" * 60)
    print(f"\n📁 輸出目錄: {config.output_dir}")
    for f in sorted(Path(config.output_dir).rglob("*")):
        if f.is_file():
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"   - {f.relative_to(config.output_dir)} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
