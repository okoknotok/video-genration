"""
《破滅者》第一季 第三集：灰石鎮
時長：11-12 分鐘
主題：冒險者公會 + 遇到卡爾 + 第一個任務 + 被小看 → 打臉

節奏：日常 → 衝突 → 爆發 → 建立聲望
"""
from dataclasses import dataclass, field
from typing import List, Literal, Optional

KOREAN_MANHWA_STYLE = (
    "korean webtoon style, manhwa art, semi-realistic, soft cel shading, "
    "detailed facial features, cinematic Korean drama lighting, pinterest aesthetic"
)

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
    time_of_day: Literal["morning", "noon", "sunset", "night", "dramatic"] = "noon"
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

STORY = StoryConfig(
    story_id="s1_ep03_greystone",
    title="破滅者 S1E03：灰石鎮",
    characters=[
        Character(id="linche", name="林澈", gender="male", age_range="mid_20s",
            appearance_prompt="young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, lean athletic build, small scar near right eye corner, wearing dark tactical jacket",
            voice_id="male-qn-jingying"),
        Character(id="tiezhu", name="鐵柱", gender="male", age_range="late_20s",
            appearance_prompt="tall muscular beastman warrior, rough rugged face with sharp canine teeth, short spiky brown hair, wolf-like ears, wearing crude leather armor",
            voice_id="male-qn-qingse", voice_pitch=2),
        Character(id="karl", name="卡爾", gender="male", age_range="late_50s",
            appearance_prompt="grizzled veteran warrior, one eye with eyepatch over left eye, short grey beard, weathered tough face, wearing worn plate armor with battle scars",
            voice_id="Chinese_Mature_Male_Narrator", voice_speed=0.9),
        Character(id="narrator", name="旁白", gender="male", age_range="mature",
            appearance_prompt="", voice_id="presenter_male", voice_speed=0.95, voice_pitch=-2),
    ],
    scenes=[
        # ── 入城（1 分鐘）──
        Scene(id=1, speaker="narrator",
            narration="灰石鎮，邊境小鎮，冒險者嘅聚集地。",
            scene_prompt=f"Medieval fantasy town bustling with people, stone buildings, market stalls, {KOREAN_MANHWA_STYLE}",
            location="greystone_town", shot_type="wide_shot", motion="pan_right", time_of_day="morning"),
        Scene(id=2, speaker="narrator",
            narration="林澈同鐵柱行入城鎮，即刻引嚟目光。",
            scene_prompt=f"Young Korean man and beastman warrior walking through town market, people staring, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche", "tiezhu"], location="greystone_town",
            shot_type="wide_shot", motion="pan_right", time_of_day="morning"),
        Scene(id=3, speaker="tiezhu",
            narration="呢度嘅人成日望我……因為我係獸人。",
            scene_prompt=f"Beastman warrior looking uncomfortable, townspeople staring with suspicion, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"], location="greystone_town",
            shot_type="medium_shot", motion="static", time_of_day="morning"),
        Scene(id=4, speaker="linche",
            narration="唔理佢哋。目標係公會。",
            scene_prompt=f"Young Korean man walking forward with purpose, ignoring stares, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="greystone_town",
            shot_type="medium_shot", motion="pan_right", time_of_day="morning"),

        # ── 公會註冊（2 分鐘）──
        Scene(id=5, speaker="narrator",
            narration="灰石鎮冒險者公會——一個充滿戰鬥氣息嘅地方。",
            scene_prompt=f"Interior of adventurer's guild hall, wooden tables, maps on walls, warriors drinking, {KOREAN_MANHWA_STYLE}",
            location="guild_hall", shot_type="wide_shot", motion="pan_right", time_of_day="noon"),
        Scene(id=6, speaker="narrator",
            narration="接待員睇住林澈，忍唔住笑。",
            scene_prompt=f"Female receptionist behind counter, smirking at young Korean man, {KOREAN_MANHWA_STYLE}",
            location="guild_hall", shot_type="medium_shot", motion="static", time_of_day="noon"),
        Scene(id=7, speaker="narrator",
            narration="「你？冒險者？你連把劍都冇。」",
            scene_prompt=f"Receptionist laughing mockingly, other adventurers laughing in background, {KOREAN_MANHWA_STYLE}",
            location="guild_hall", shot_type="medium_shot", motion="zoom_in", time_of_day="noon"),
        Scene(id=8, speaker="linche",
            narration="我唔需要劍。",
            scene_prompt=f"Young Korean man with calm confident expression, slight smirk, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="guild_hall",
            shot_type="close_up", motion="static", time_of_day="noon"),
        Scene(id=9, speaker="narrator",
            narration="全場靜咗一秒。然後更大聲笑。",
            scene_prompt=f"Guild hall with adventurers laughing loudly, mocking atmosphere, {KOREAN_MANHWA_STYLE}",
            location="guild_hall", shot_type="wide_shot", motion="zoom_out", time_of_day="noon"),

        # ── 卡爾出現（1 分鐘）──
        Scene(id=10, speaker="narrator",
            narration="一個獨眼老兵從角落行出嚟。",
            scene_prompt=f"Grizzled one-eyed veteran warrior stepping from shadows, imposing presence, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["karl"], location="guild_hall",
            shot_type="medium_shot", motion="pan_right", time_of_day="noon"),
        Scene(id=11, speaker="karl",
            narration="夠膽講呢句嘅人，唔係傻就係有實力。你係邊種？",
            scene_prompt=f"One-eyed veteran staring intensely at young Korean man, testing gaze, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["karl"], location="guild_hall",
            shot_type="close_up", motion="zoom_in", time_of_day="noon"),
        Scene(id=12, speaker="linche",
            narration="試下咪知。",
            scene_prompt=f"Young Korean man meeting veteran's gaze without flinching, confident, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="guild_hall",
            shot_type="close_up", motion="static", time_of_day="noon"),
        Scene(id=13, speaker="karl",
            narration="哈！好。我係卡爾，呢度嘅會長。俾你一個機會。",
            scene_prompt=f"One-eyed veteran grinning, slapping table, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["karl"], location="guild_hall",
            shot_type="medium_shot", motion="static", time_of_day="noon"),

        # ── 第一個任務（2 分鐘）──
        Scene(id=14, speaker="karl",
            narration="鎮外礦洞有隻石化巨蜥，已經殺咗三個冒險者。搞掂佢，你就正式加入。",
            scene_prompt=f"Old warrior pointing at map showing mine cave location, serious expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["karl"], location="guild_hall",
            shot_type="medium_shot", motion="static", time_of_day="noon"),
        Scene(id=15, speaker="narrator",
            narration="其他冒險者竊竊私語：「石化巨蜥？嗰隻 B 級魔獸？佢實死。」",
            scene_prompt=f"Adventurers whispering to each other, worried and mocking expressions, {KOREAN_MANHWA_STYLE}",
            location="guild_hall", shot_type="medium_shot", motion="static", time_of_day="noon"),
        Scene(id=16, speaker="linche",
            narration="走。",
            scene_prompt=f"Young Korean man turning to leave, determined expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="guild_hall",
            shot_type="medium_shot", motion="pan_right", time_of_day="noon"),
        Scene(id=17, speaker="tiezhu",
            narration="等等我！我同你一齊去！",
            scene_prompt=f"Beastman warrior running after Korean man, excited, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"], location="guild_hall",
            shot_type="medium_shot", motion="pan_right", time_of_day="noon"),

        # ── 礦洞戰鬥（3 分鐘）──
        Scene(id=18, speaker="narrator",
            narration="礦洞深處，黑暗而潮濕。",
            scene_prompt=f"Dark mine cave, dripping water, glowing crystals on walls, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="wide_shot", motion="pan_right", time_of_day="dramatic"),
        Scene(id=19, speaker="narrator",
            narration="石化巨蜥——三米長，全身覆蓋住石頭般嘅鱗甲。",
            scene_prompt=f"Giant stone-scaled lizard monster in dark cave, glowing yellow eyes, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="wide_shot", motion="zoom_in", time_of_day="dramatic"),
        Scene(id=20, speaker="tiezhu",
            narration="好大！我頂住佢，你搵機會！",
            scene_prompt=f"Beastman warrior charging at giant lizard with axe, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"], location="mine_cave",
            shot_type="medium_shot", motion="pan_right", time_of_day="dramatic"),
        Scene(id=21, speaker="narrator",
            narration="鐵柱嘅斧頭砍落鱗甲上面——完全冇用。",
            scene_prompt=f"Axe bouncing off stone scales, sparks flying, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="close_up", motion="static", time_of_day="dramatic"),
        Scene(id=22, speaker="narrator",
            narration="巨蜥尾巴一掃，鐵柱飛咗出去。",
            scene_prompt=f"Beastman warrior being thrown by lizard tail, crashing into wall, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"], location="mine_cave",
            shot_type="wide_shot", motion="pan_left", time_of_day="dramatic"),
        Scene(id=23, speaker="linche",
            narration="……弱點。",
            scene_prompt=f"Young Korean man activating red eye, scanning monster, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="mine_cave",
            shot_type="close_up", motion="zoom_in", time_of_day="dramatic"),
        Scene(id=24, speaker="narrator",
            narration="破滅之眼啟動。巨蜥全身嘅裂痕一目了然。",
            scene_prompt=f"POV shot with red cracks overlaying lizard body, weak point glowing at underbelly, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="pov_shot", motion="static", time_of_day="dramatic"),
        Scene(id=25, speaker="linche",
            narration="腹部，第三塊鱗同第四塊之間。",
            scene_prompt=f"Close-up of glowing red crack between scales on lizard belly, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="close_up", motion="zoom_in", time_of_day="dramatic"),
        Scene(id=26, speaker="narrator",
            narration="林澈衝前，巨蜥張開口想咬佢。",
            scene_prompt=f"Young Korean man dodging lizard bite, rolling under its body, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="mine_cave",
            shot_type="medium_shot", motion="pan_right", time_of_day="dramatic"),
        Scene(id=27, speaker="narrator",
            narration="佢嘅右手掌直插巨蜥腹部嘅裂痕。",
            scene_prompt=f"Hand piercing into glowing red crack on lizard underbelly, magical energy burst, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="mine_cave",
            shot_type="close_up", motion="zoom_in", time_of_day="dramatic"),
        Scene(id=28, speaker="narrator",
            narration="破滅。",
            scene_prompt=f"Giant lizard shattering from inside, explosion of stone scales and magical energy, {KOREAN_MANHWA_STYLE}",
            location="mine_cave", shot_type="wide_shot", motion="zoom_out", time_of_day="dramatic"),
        Scene(id=29, speaker="narrator",
            narration="巨蜥……碎咗。一掌。",
            scene_prompt=f"Young Korean man standing amidst shattered monster remains, right eye glowing, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="mine_cave",
            shot_type="medium_shot", motion="static", time_of_day="dramatic"),

        # ── 打臉 + 結尾（1 分鐘）──
        Scene(id=30, speaker="tiezhu",
            narration="……你太強了吧！！",
            scene_prompt=f"Beastman warrior on ground, jaw dropped, shocked expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"], location="mine_cave",
            shot_type="medium_shot", motion="static", time_of_day="dramatic"),
        Scene(id=31, speaker="narrator",
            narration="佢哋帶住巨蜥嘅核心返到公會。全場沉默。",
            scene_prompt=f"Young Korean man placing glowing monster core on guild counter, everyone staring in shock, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="guild_hall",
            shot_type="wide_shot", motion="zoom_in", time_of_day="night"),
        Scene(id=32, speaker="karl",
            narration="一掌碎石化巨蜥……你唔係普通冒險者。",
            scene_prompt=f"One-eyed veteran staring at monster core, then at Korean man, impressed, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["karl"], location="guild_hall",
            shot_type="close_up", motion="zoom_in", time_of_day="night"),
        Scene(id=33, speaker="linche",
            narration="我只係想變強。",
            scene_prompt=f"Young Korean man with cold expression, turning to leave, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"], location="guild_hall",
            shot_type="medium_shot", motion="pan_right", time_of_day="night"),
        Scene(id=34, speaker="narrator",
            narration="從今日開始，灰石鎮多咗一個傳說——『紅眼嘅男人』。",
            scene_prompt=f"Title card with red eye symbol, dark atmosphere, {KOREAN_MANHWA_STYLE}",
            location="abstract", shot_type="wide_shot", motion="static", time_of_day="dramatic"),
    ],
    music_style="epic_dark",
)
