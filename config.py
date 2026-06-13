"""全域設定 + 模型登記表。所有『模型背後意義』寫晒喺呢度，WhatsApp bot 之後直接讀。"""
import os

# ---- API Key（用環境變數，唔好硬寫死）----
FAL_KEY = os.environ.get("FAL_KEY", "")

# ---- 路徑 ----
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "output")
TEMP_DIR = os.environ.get("TEMP_DIR", "temp")
CHARACTERS_DB = os.environ.get("CHARACTERS_DB", "characters.json")

# ---- 影片規格（16:9 橫向；想出直向短片改成 1080 x 1920）----
VIDEO_WIDTH = int(os.environ.get("VIDEO_WIDTH", "1280"))
VIDEO_HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "720"))
VIDEO_FPS = 30

# ---- LLM（劇本）。如果報錯，多數係呢個 model 名要改 ----
LLM_ENDPOINT = "fal-ai/any-llm"
LLM_MODEL = "anthropic/claude-3.5-sonnet"

# ---- 圖片風格 ----
IMAGE_STYLES = {
    "manhwa": "korean manhwa style, webtoon, clean lineart, soft cel shading",
    "cinematic": "cinematic photo, realistic, dramatic lighting, film grain",
    "anime": "japanese anime style, vibrant colors",
    "cdrama": "chinese ancient style, guofeng, elegant, hanfu",
}

# ---- TTS（MiniMax）。voice_id 如讀錯聲，改呢度 ----
TTS_MODEL = "fal-ai/minimax-tts/text-to-speech"
TTS_VOICES = {
    "f1": {"id": "female-shaonv",   "label": "少女音（女）"},
    "f2": {"id": "female-tianmei",  "label": "甜美音（女）"},
    "m1": {"id": "male-qn-qingse",  "label": "青澀青年（男）"},
    "m2": {"id": "presenter_male",  "label": "旁白男聲"},
}

# ---- image→video 模型登記表（核心）----
# 想加新 model（Wan / CogVideoX / Kling v2…）只要喺呢度加個 key。
VIDEO_MODELS = {
    "ken-burns": {
        "label": "Ken Burns（唔出真片）",
        "fal_id": None,
        "cost": "免費",
        "speed": "即時",
        "meaning": "唔會真係郁，只用 ffmpeg 幫靜態圖做緩慢縮放/平移營造鏡頭感。最平最快。",
        "best_for": "對白多、靜態為主嘅韓漫；想慳錢",
        "extra": {},
    },
    "ltx": {
        "label": "LTX Video",
        "fal_id": "fal-ai/ltx-video/image-to-video",
        "cost": "約 $0.02 / 5秒",
        "speed": "快（10–30秒）",
        "meaning": "開源輕量 image→video，平又快，動作較簡單。啱大量場景輕微郁動。",
        "best_for": "想平想快、輕微動作",
        "extra": {},
    },
    "minimax": {
        "label": "MiniMax Live",
        "fal_id": "fal-ai/minimax/video-01-live/image-to-video",
        "cost": "約 $0.30 / 5秒",
        "speed": "中（1–3分鐘）",
        "meaning": "專為插畫/動漫/韓漫角色『活起來』調校，會自然眨眼、頭髮飄、呼吸。最啱韓漫。",
        "best_for": "韓漫角色輕微生動（最推薦）",
        "extra": {"prompt_optimizer": True},
    },
    "kling": {
        "label": "Kling Standard",
        "fal_id": "fal-ai/kling-video/v1/standard/image-to-video",
        "cost": "約 $0.50 / 5秒",
        "speed": "慢（3–8分鐘）",
        "meaning": "畫質最靚、動作最自然，但最慢最貴。留俾真正需要明顯動作嘅高潮場。",
        "best_for": "高潮/打鬥/明顯動作場",
        "extra": {"duration": "5"},
    },
}


def explain_models() -> str:
    """俾 WhatsApp 直接 send 出嚟嘅『模型意義』文字。"""
    out = ["🎞️ 動畫模型（image→video）選擇：\n"]
    for key, m in VIDEO_MODELS.items():
        out.append(f"【{key}】{m['label']}")
        out.append(f"  • 意義：{m['meaning']}")
        out.append(f"  • 價錢：{m['cost']}｜速度：{m['speed']}")
        out.append(f"  • 最啱：{m['best_for']}\n")
    return "\n".join(out)
