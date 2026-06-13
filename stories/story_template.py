"""
故事配置模板 / Story Config Template
複製呢個檔案嚟建立新劇本

【使用方法】
cp stories/story_template.py stories/story_01.py
# 然後編輯 story_01.py 入面嘅內容

【必填欄位】
- title: 劇本標題
- characters: 角色列表（最少1個）
- scenes: 場景列表（最少1個）
- music_style: 背景音樂風格

【可選欄位】
- output_dir: 自定義輸出資料夾（預設 cache/{story_id}/）
- global_seed: 全域隨機種子（預設42）
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# ════════════════════════════════════════════════════════════
# 🎬 背景音樂風格 Presets
# ════════════════════════════════════════════════════════════

# 音樂 Presets 已移至 stories/music_presets.py

# ════════════════════════════════════════════════════════════
# 🎭 角色定義 dataclass
# ════════════════════════════════════════════════════════════

@dataclass
class Character:
    """角色定義"""
    id: str                           # 角色唯一ID（如 "protagonist", "villain"）
    name: str                         # 角色名稱（中文）
    gender: Literal["male", "female", "other"]  # 性別
    age_range: str                    # 年齡範圍（如 "early_30s", "late_20s"）
    
    # 外貌描述（英文，俾 Flux 生成 reference image）
    appearance_prompt: str = ""
    
    #  Personality traits（可選，用嚟生成更一致嘅角色）
    personality: str = ""
    
    # 語音設定（可選）
    voice_id: str = "Chinese_Mature_Male_Narrator"  # MiniMax voice ID
    voice_speed: float = 1.0
    voice_pitch: float = 0
    
    # 內部計算欄位（唔使填）
    ref_image_url: Optional[str] = None  # 快取嘅 reference URL


# ════════════════════════════════════════════════════════════
# 🎬 場景定義 dataclass
# ════════════════════════════════════════════════════════════

@dataclass
class Scene:
    """場景定義"""
    id: int                           # 場景編號（由1開始）
    speaker: str                      # 角色ID（台詞講者）
    
    narration: str                    # 該角色嘅台詞 / 旁白（中文）
    scene_prompt: str                 # 場景視覺描述（英文，俾 AI 生圖）
    
    # 場景入面出現嘅角色（用於 Nano Banana，保持角色一致性）
    characters_in_scene: List[str] = field(default_factory=list)
    
    # 場景一致性
    location: str = ""                # 場景位置（如 "home_living_room"）
    background_ref: str = ""          # 背景 reference image URL（與其他 scene 共用）
    
    # 鏡頭
    shot_type: Literal[
        "wide_shot", "medium_shot", "close_up", "over_shoulder",
        "cowork_shot", "pov_shot"
    ] = "medium_shot"
    
    # Ken Burns 動作
    motion: Literal[
        "zoom_in", "zoom_out",
        "pan_left", "pan_right",
        "pan_up", "pan_down",
        "static"
    ] = "zoom_in"
    
    # 環境
    time_of_day: Literal["morning", "noon", "sunset", "night", "dramatic"] = "noon"
    outfit: str = ""                  # 角色呢個場景著咩衫（與其他 scene 共用）
    
    # 內部計算欄位（唔使填）
    duration: float = 0.0             # 自動由 TTS 時長決定
    ref_image_url: str = ""          # 呢個 scene 嘅背景 image URL


# ════════════════════════════════════════════════════════════
# 📋 Story Config（主要config class）
# ════════════════════════════════════════════════════════════

@dataclass
class StoryConfig:
    """完整劇本配置"""
    
    # --- 必填欄位 ---
    story_id: str                     # 唯一識別碼（如 "story_01"）
    title: str                        # 劇本標題
    characters: List[Character]       # 角色列表
    scenes: List[Scene]               # 場景列表
    
    # --- 音樂設定 ---
    music_style: str = "gentle_emotional"  # music_presets 入面嘅 key
    
    # --- 可選欄位 ---
    global_seed: int = 42             # 全域隨機種子（保持可重現性）
    output_subdir: str = ""           # 自定義輸出子資料夾（預設 story_id）
    
    # --- 內部欄位（自動計算）---
    _output_dir: str = ""            # 內部用，唔使填
    
    def __post_init__(self):
        if not self.output_subdir:
            self.output_subdir = self.story_id
        self._output_dir = f"cache/{self.output_subdir}"
    
    @property
    def output_dir(self) -> str:
        return self._output_dir


# ════════════════════════════════════════════════════════════
# 📝 範例 Story Config（末日農場 - 序章）
# ════════════════════════════════════════════════════════════

STORY = StoryConfig(
    story_id="apocalypse_farm_pilot",
    title="末日農場 · 序章",
    
    # --- 角色 ---
    characters=[
        Character(
            id="survivor",
            name="陳浩",
            gender="male",
            age_range="early_30s",
            appearance_prompt=(
                "Portrait photo of an Asian man in his early 30s, short messy black hair, "
                "slight stubble, wearing a worn brown leather jacket over a grey sweater, "
                "weathered face with determined eyes, strong jawline, "
                "neutral dark background, professional photography, 8K, photorealistic"
            ),
            personality="堅毅、沉默寡言、但內心火熱",
            voice_id="Chinese_Mature_Male_Narrator",
            voice_speed=1.0,
            voice_pitch=-1,
        ),
        Character(
            id="narrator",
            name="旁白",
            gender="male",
            age_range="mature",
            appearance_prompt=None,  # 旁白冇樣
            personality="磁性低沉、引發懸念",
            voice_id="Chinese_Mature_Male_Narrator",
            voice_speed=0.95,
            voice_pitch=-2,
        ),
    ],
    
    # --- 場景 ---
    scenes=[
        Scene(
            id=1,
            speaker="narrator",
            narration="末日降臨的第三年，世界已經面目全非。",
            scene_prompt=(
                "A desolate post-apocalyptic city street, gray sky, dead leaves blowing in the wind, "
                "abandoned cars, collapsed buildings, cinematic mood, dramatic lighting, photorealistic, 8K"
            ),
            motion="zoom_in",
        ),
        Scene(
            id=2,
            speaker="narrator",
            narration="大部分人已經放棄，但我冇。因為我知道一個秘密——我的農場，在深山裡面，還有一片綠洲。",
            scene_prompt=(
                "A lone survivor walking slowly through ruins, silhouette against dusty orange sky, "
                "mysterious atmosphere, cinematic wide shot, photorealistic"
            ),
            motion="pan_right",
        ),
        Scene(
            id=3,
            speaker="narrator",
            narration="三年，我一個人，建立咗呢度。你問我點解可以生存？因為我唔只靠雙手。",
            scene_prompt=(
                "A secret hidden farm in the mountains, golden wheat fields under sunlight, "
                "lush green vegetables, peaceful oasis, vibrant colors contrast with previous scene, "
                "beautiful landscape photography, photorealistic"
            ),
            motion="zoom_in",
        ),
        Scene(
            id=4,
            speaker="survivor",
            narration="我靠的是決心。末日？笑咗。遲早有一日，會有人知道我的名字。",
            scene_prompt=(
                "A strong determined person looking up at the sky, close-up face shot, "
                "eyes showing inner light and determination, confident expression, "
                "dramatic lighting from above, photorealistic"
            ),
            characters_in_scene=["survivor"],
            motion="zoom_out",
        ),
        Scene(
            id=5,
            speaker="narrator",
            narration="呢個，只係開始。",
            scene_prompt=(
                "Wide panoramic view of a thriving farm at sunrise, golden hour lighting, "
                "lush fields, small wooden house, peaceful countryside, "
                "volumetric lighting, cinematic landscape, photorealistic"
            ),
            motion="pan_left",
        ),
    ],
    
    # --- 音樂 ---
    music_style="epic_cinematic",
)