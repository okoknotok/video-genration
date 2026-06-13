"""
《破滅者》第一季 第一集：墜落
時長：11-12 分鐘
主題：背叛 → 死亡 → 穿越 → 覺醒

節奏：快 → 慢 → 爆發
"""

from dataclasses import dataclass, field
from typing import List, Literal, Optional

# ── 韓漫風格 ──────────────────────────────────────
KOREAN_MANHWA_STYLE = (
    "korean manhwa style, clean bold lineart, cel-shaded coloring, "
    "vibrant colors, high contrast lighting, sharp edges, "
    "detailed anime-style facial features, expressive eyes, "
    "dynamic composition, dramatic poses, "
    "professional webtoon illustration, high quality manhwa art"
)

# ── 角色外貌（同 LoRA 配合）──────────────────────
LINCHE_APPEARANCE = (
    "young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, "
    "lean athletic build, small scar near right eye corner, wearing dark tactical jacket"
)

# ══════════════════════════════════════════════════
# 🎭 角色
# ══════════════════════════════════════════════════

@dataclass
class Character:
    id: str
    name: str
    gender: Literal["male", "female", "other"]
    age_range: str
    appearance_prompt: str = ""
    personality: str = ""
    voice_id: str = "male-qn-jingying"
    voice_speed: float = 1.0
    voice_pitch: float = 0
    ref_image_url: Optional[str] = None

@dataclass
class Scene:
    id: int
    speaker: str
    narration: str
    scene_prompt: str
    characters_in_scene: List[str] = field(default_factory=list)
    location: str = ""
    shot_type: Literal["wide_shot", "medium_shot", "close_up", "over_shoulder", "cowork_shot", "pov_shot"] = "medium_shot"
    motion: Literal["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "static"] = "zoom_in"
    time_of_day: Literal["morning", "noon", "sunset", "night", "dramatic"] = "night"
    outfit: str = ""
    duration: float = 0.0
    ref_image_url: str = ""

@dataclass
class StoryConfig:
    story_id: str
    title: str
    characters: List[Character]
    scenes: List[Scene]
    music_style: str = "epic_dark"
    global_seed: int = 42
    output_subdir: str = ""
    _output_dir: str = ""
    def __post_init__(self):
        if not self.output_subdir:
            self.output_subdir = self.story_id
        self._output_dir = f"cache/{self.output_subdir}"
    @property
    def output_dir(self) -> str:
        return self._output_dir

# ══════════════════════════════════════════════════
# 📖 第一集：墜落
# ══════════════════════════════════════════════════

STORY = StoryConfig(
    story_id="s1_ep01_fall",
    title="破滅者 S1E01：墜落",
    
    characters=[
        Character(
            id="linche",
            name="林澈",
            gender="male",
            age_range="mid_20s",
            appearance_prompt=LINCHE_APPEARANCE,
            personality="冷靜、聰明、善良但即將被背叛",
            voice_id="male-qn-jingying",
            voice_speed=1.0,
            voice_pitch=0,
        ),
        Character(
            id="narrator",
            name="旁白",
            gender="male",
            age_range="mature",
            appearance_prompt="",
            personality="低沉、懸疑、引人入勝",
            voice_id="presenter_male",
            voice_speed=0.95,
            voice_pitch=-2,
        ),
    ],
    
    scenes=[
        # ── 開場：城市夜景（30 秒）──────────────
        Scene(
            id=1,
            speaker="narrator",
            narration="呢個世界，唔會因為你善良就保護你。",
            scene_prompt=f"Modern city skyline at night, neon lights reflecting on glass skyscrapers, rain falling, cinematic wide shot, {KOREAN_MANHWA_STYLE}",
            location="city_night",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="night",
        ),
        Scene(
            id=2,
            speaker="narrator",
            narration="林澈曾經以為，只要努力，就能改變命運。",
            scene_prompt=f"Young Korean man standing alone on rooftop, looking at city lights, contemplative expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="rooftop",
            shot_type="medium_shot",
            motion="zoom_in",
            time_of_day="night",
        ),
        
        # ── 公司成功（1 分鐘）──────────────────
        Scene(
            id=3,
            speaker="narrator",
            narration="28 歲，白手興家，佢嘅科技公司即將上市。",
            scene_prompt=f"Modern tech company office, sleek design, employees celebrating, champagne, {KOREAN_MANHWA_STYLE}",
            location="office",
            shot_type="wide_shot",
            motion="pan_left",
            time_of_day="noon",
        ),
        Scene(
            id=4,
            speaker="linche",
            narration="多謝大家，呢一切係我哋一齊努力嘅成果。",
            scene_prompt=f"Handsome young Korean CEO giving speech, confident smile, holding champagne glass, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=5,
            speaker="narrator",
            narration="佢最信任嘅拍檔周偉明，一直企喺佢身邊。",
            scene_prompt=f"Two Korean men shaking hands, one is the CEO, other is his partner, both smiling, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="cowork_shot",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=6,
            speaker="narrator",
            narration="仲有佢嘅未婚妻方詩韻，温柔体贴，人人羨慕。",
            scene_prompt=f"Beautiful Korean woman hugging young CEO, loving expression, elegant dress, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        
        # ── 發現背叛（2 分鐘）──────────────────
        Scene(
            id=7,
            speaker="narrator",
            narration="但係，幸福往往只係表象。",
            scene_prompt=f"Dark corridor in office building, shadows, ominous atmosphere, {KOREAN_MANHWA_STYLE}",
            location="office_corridor",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="night",
        ),
        Scene(
            id=8,
            speaker="narrator",
            narration="上市前夜，林澈無意中聽到咗一個對話。",
            scene_prompt=f"Young Korean man standing outside closed door, listening intently, shocked expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office_corridor",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=9,
            speaker="narrator",
            narration="「技術已經轉移到離岸公司，上市之後我哋就可以套現走人。」",
            scene_prompt=f"Shadowy figures talking in dimly lit room, conspiratorial atmosphere, {KOREAN_MANHWA_STYLE}",
            location="office_room",
            shot_type="over_shoulder",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=10,
            speaker="linche",
            narration="……偉明？",
            scene_prompt=f"Close-up of young Korean man's face, eyes wide with disbelief, tears forming, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office_corridor",
            shot_type="close_up",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=11,
            speaker="narrator",
            narration="佢嘅拍檔、佢嘅未婚妻、佢嘅恩師——三個人，聯手背叛咗佢。",
            scene_prompt=f"Split screen showing three shadowy figures, ominous lighting, {KOREAN_MANHWA_STYLE}",
            location="abstract",
            shot_type="wide_shot",
            motion="zoom_out",
            time_of_day="dramatic",
        ),
        
        # ── 對質（2 分鐘）────────────────────
        Scene(
            id=12,
            speaker="linche",
            narration="你哋……點解？",
            scene_prompt=f"Young Korean man confronting his partners, angry and hurt expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="medium_shot",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=13,
            speaker="narrator",
            narration="周偉明笑咗。嗰種笑，係勝利者嘅笑。",
            scene_prompt=f"Arrogant Korean man smirking, cold eyes, expensive suit, {KOREAN_MANHWA_STYLE}",
            location="office",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=14,
            speaker="narrator",
            narration="「林澈，你太天真。呢個世界，善良係弱點。」",
            scene_prompt=f"Arrogant Korean man speaking condescendingly, gesturing dismissively, {KOREAN_MANHWA_STYLE}",
            location="office",
            shot_type="medium_shot",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=15,
            speaker="linche",
            narration="詩韻……你都係？",
            scene_prompt=f"Young Korean man looking at woman with pleading eyes, heartbroken expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="close_up",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=16,
            speaker="narrator",
            narration="方詩韻望住佢，眼神冷漠。",
            scene_prompt=f"Beautiful Korean woman with cold expression, looking away, no emotion, {KOREAN_MANHWA_STYLE}",
            location="office",
            shot_type="close_up",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=17,
            speaker="narrator",
            narration="「我從來都冇愛過你。你只係我嘅跳板。」",
            scene_prompt=f"Beautiful Korean woman speaking coldly, slight smirk, {KOREAN_MANHWA_STYLE}",
            location="office",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=18,
            speaker="linche",
            narration="……好。我記住你哋。",
            scene_prompt=f"Young Korean man with tears streaming down face, but eyes burning with rage, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="office",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        
        # ── 被推下樓（1 分鐘）────────────────
        Scene(
            id=19,
            speaker="narrator",
            narration="佢衝上天台，想冷靜一下。但佢唔知，呢個係陷阱。",
            scene_prompt=f"Young Korean man running up stairs to rooftop, desperate expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="staircase",
            shot_type="medium_shot",
            motion="pan_up",
            time_of_day="night",
        ),
        Scene(
            id=20,
            speaker="narrator",
            narration="一個黑影從後面向佢行嚟。",
            scene_prompt=f"Dark silhouette approaching from behind, menacing presence, rooftop at night, {KOREAN_MANHWA_STYLE}",
            location="rooftop",
            shot_type="wide_shot",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=21,
            speaker="narrator",
            narration="「阿標，處理佢。」",
            scene_prompt=f"Muscular man in black tactical gear, scarred face, cold expression, {KOREAN_MANHWA_STYLE}",
            location="rooftop",
            shot_type="medium_shot",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=22,
            speaker="narrator",
            narration="林澈轉過身，見到嘅係一隻手。",
            scene_prompt=f"Close-up of hand pushing, motion blur, {KOREAN_MANHWA_STYLE}",
            location="rooftop",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=23,
            speaker="linche",
            narration="——！！",
            scene_prompt=f"Young Korean man falling backward, shocked expression, arms reaching out, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="rooftop_edge",
            shot_type="medium_shot",
            motion="zoom_out",
            time_of_day="night",
        ),
        
        # ── 墜落 + 回憶（1 分鐘）─────────────
        Scene(
            id=24,
            speaker="narrator",
            narration="風聲。只有風聲。",
            scene_prompt=f"Night sky with city lights blurred, falling perspective, motion blur, {KOREAN_MANHWA_STYLE}",
            location="falling",
            shot_type="pov_shot",
            motion="pan_down",
            time_of_day="night",
        ),
        Scene(
            id=25,
            speaker="narrator",
            narration="佢嘅人生，走馬燈一樣閃過。",
            scene_prompt=f"Flashback montage, warm memories fading to cold reality, {KOREAN_MANHWA_STYLE}",
            location="abstract",
            shot_type="wide_shot",
            motion="zoom_out",
            time_of_day="dramatic",
        ),
        Scene(
            id=26,
            speaker="linche",
            narration="如果……如果我可以再嚟一次……",
            scene_prompt=f"Young Korean man's face in slow motion falling, tears floating, determined eyes, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="falling",
            shot_type="close_up",
            motion="static",
            time_of_day="night",
        ),
        
        # ── 死亡 + 黑暗（30 秒）──────────────
        Scene(
            id=27,
            speaker="narrator",
            narration="砰。",
            scene_prompt=f"Black screen with red splatter effect, abstract, {KOREAN_MANHWA_STYLE}",
            location="abstract",
            shot_type="wide_shot",
            motion="static",
            time_of_day="dramatic",
        ),
        Scene(
            id=28,
            speaker="narrator",
            narration="黑暗。無盡嘅黑暗。",
            scene_prompt=f"Pure black void, abstract, minimal, {KOREAN_MANHWA_STYLE}",
            location="void",
            shot_type="wide_shot",
            motion="static",
            time_of_day="dramatic",
        ),
        Scene(
            id=29,
            speaker="narrator",
            narration="但係，喺黑暗深處，有一雙眼亮起。",
            scene_prompt=f"Two glowing red eyes appearing in darkness, mysterious, {KOREAN_MANHWA_STYLE}",
            location="void",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="dramatic",
        ),
        
        # ── 穿越到異世界（1 分鐘）────────────
        Scene(
            id=30,
            speaker="narrator",
            narration="「你……想唔想再活一次？」",
            scene_prompt=f"Mysterious glowing portal in darkness, ethereal light, {KOREAN_MANHWA_STYLE}",
            location="void",
            shot_type="wide_shot",
            motion="zoom_in",
            time_of_day="dramatic",
        ),
        Scene(
            id=31,
            speaker="linche",
            narration="……邊個？",
            scene_prompt=f"Young Korean man floating in void, confused but alert, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="void",
            shot_type="medium_shot",
            motion="static",
            time_of_day="dramatic",
        ),
        Scene(
            id=32,
            speaker="narrator",
            narration="「我可以俾你第二次機會。但代價係——你要幫我毀滅一個世界。」",
            scene_prompt=f"Ethereal figure made of light and shadow, offering hand, {KOREAN_MANHWA_STYLE}",
            location="void",
            shot_type="wide_shot",
            motion="zoom_in",
            time_of_day="dramatic",
        ),
        Scene(
            id=33,
            speaker="linche",
            narration="毀滅世界？……好。只要我可以返去報仇。",
            scene_prompt=f"Young Korean man with determined expression, eyes glowing red, accepting deal, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="void",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="dramatic",
        ),
        
        # ── 醒嚟（1 分鐘）───────────────────
        Scene(
            id=34,
            speaker="narrator",
            narration="光。刺眼嘅光。",
            scene_prompt=f"Bright sunlight through forest canopy, magical forest, ethereal atmosphere, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="wide_shot",
            motion="zoom_out",
            time_of_day="morning",
        ),
        Scene(
            id=35,
            speaker="linche",
            narration="……呢度係邊？",
            scene_prompt=f"Young Korean man lying on grass in magical forest, waking up, confused expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="medium_shot",
            motion="static",
            time_of_day="morning",
        ),
        Scene(
            id=36,
            speaker="narrator",
            narration="佢發現自己身處一片陌生嘅森林。空氣中充滿魔力。",
            scene_prompt=f"Magical forest with glowing plants, floating particles, fantasy atmosphere, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="morning",
        ),
        Scene(
            id=37,
            speaker="linche",
            narration="我……未死？",
            scene_prompt=f"Young Korean man looking at his hands, checking if he's alive, amazed expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="close_up",
            motion="static",
            time_of_day="morning",
        ),
        
        # ── 發現破滅之眼（1 分鐘）────────────
        Scene(
            id=38,
            speaker="narrator",
            narration="突然，佢嘅右眼劇痛。",
            scene_prompt=f"Young Korean man clutching his right eye, pain expression, red glow emanating from eye, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="morning",
        ),
        Scene(
            id=39,
            speaker="narrator",
            narration="當佢睜開眼，世界變咗。",
            scene_prompt=f"POV shot with red cracks appearing on trees and rocks, showing weaknesses, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="pov_shot",
            motion="static",
            time_of_day="morning",
        ),
        Scene(
            id=40,
            speaker="linche",
            narration="呢啲……裂痕係咩？",
            scene_prompt=f"Young Korean man looking at red cracks on tree, amazed and curious, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="medium_shot",
            motion="zoom_in",
            time_of_day="morning",
        ),
        Scene(
            id=41,
            speaker="narrator",
            narration="佢觸踫咗樹上嘅裂痕。",
            scene_prompt=f"Hand touching glowing red crack on tree, magical energy, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="close_up",
            motion="static",
            time_of_day="morning",
        ),
        Scene(
            id=42,
            speaker="narrator",
            narration="棵樹……碎咗。",
            scene_prompt=f"Tree shattering into pieces, magical explosion, debris flying, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="wide_shot",
            motion="zoom_out",
            time_of_day="morning",
        ),
        Scene(
            id=43,
            speaker="linche",
            narration="……我可以睇到弱點。",
            scene_prompt=f"Young Korean man with glowing red right eye, looking at his hand, realization, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="morning",
        ),
        
        # ── 結尾（30 秒）───────────────────
        Scene(
            id=44,
            speaker="narrator",
            narration="林澈明白咗。呢個能力，係為咗毀滅而生。",
            scene_prompt=f"Young Korean man standing in destroyed forest clearing, red eye glowing, determined expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_destroyed",
            shot_type="medium_shot",
            motion="zoom_in",
            time_of_day="morning",
        ),
        Scene(
            id=45,
            speaker="linche",
            narration="周偉明、方詩韻、陳教授……你哋等住。",
            scene_prompt=f"Close-up of young Korean man's face, one eye glowing red, cold determined expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_destroyed",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="morning",
        ),
        Scene(
            id=46,
            speaker="linche",
            narration="我會返嚟。一個一個，慢慢嚟。",
            scene_prompt=f"Young Korean man walking away into forest, back view, ominous atmosphere, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="morning",
        ),
        Scene(
            id=47,
            speaker="narrator",
            narration="破滅者，覺醒。",
            scene_prompt=f"Title card: 破滅者, red glowing text, dark background, {KOREAN_MANHWA_STYLE}",
            location="abstract",
            shot_type="wide_shot",
            motion="static",
            time_of_day="dramatic",
        ),
    ],
    
    music_style="epic_dark",
)
