"""
《破滅者》第一季 第二集：獸人
時長：11-12 分鐘
主題：異世界生存 + 第一次戰鬥 + 破滅之眼 Lv.1 覺醒 + 遇到鐵柱

節奏：探索 → 危機 → 爆發 → 結盟
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
    time_of_day: Literal["morning", "noon", "sunset", "night", "dramatic"] = "morning"
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
    story_id="s1_ep02_beastman",
    title="破滅者 S1E02：獸人",
    characters=[
        Character(
            id="linche",
            name="林澈",
            gender="male",
            age_range="mid_20s",
            appearance_prompt="young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, lean athletic build, small scar near right eye corner, wearing dark tactical jacket",
            personality="冷靜、計算、逐漸覺醒",
            voice_id="male-qn-jingying",
            voice_speed=1.0,
            voice_pitch=0,
        ),
        Character(
            id="tiezhu",
            name="鐵柱",
            gender="male",
            age_range="late_20s",
            appearance_prompt="tall muscular beastman warrior, rough rugged face with sharp canine teeth, short spiky brown hair, wolf-like ears on top of head, scarred arms, wearing crude leather armor and fur cloak",
            personality="直率、忠誠、重情義",
            voice_id="male-qn-qingse",
            voice_speed=1.0,
            voice_pitch=2,
        ),
        Character(
            id="narrator",
            name="旁白",
            gender="male",
            age_range="mature",
            appearance_prompt="",
            personality="低沉、懸疑",
            voice_id="presenter_male",
            voice_speed=0.95,
            voice_pitch=-2,
        ),
    ],
    scenes=[
        # ── 開場回顧（30 秒）──────────────
        Scene(
            id=1,
            speaker="narrator",
            narration="上一集，林澈被背叛、被殺害、然後穿越到異世界。",
            scene_prompt=f"Young Korean man falling through portal, red eye glowing, dark fantasy atmosphere, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="void",
            shot_type="wide_shot",
            motion="pan_down",
            time_of_day="dramatic",
        ),
        Scene(
            id=2,
            speaker="narrator",
            narration="佢獲得咗『破滅之眼』——睇穿一切弱點嘅能力。",
            scene_prompt=f"Young Korean man's right eye glowing red, cracks appearing on surroundings, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="morning",
        ),

        # ── 森林探索（1 分鐘）──────────────
        Scene(
            id=3,
            speaker="narrator",
            narration="林澈喺森林行咗成日，仲未見到任何人類。",
            scene_prompt=f"Dense magical forest, glowing mushrooms, floating particles, lone figure walking, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="noon",
        ),
        Scene(
            id=4,
            speaker="linche",
            narration="呢度嘅空氣……充滿魔力。我感覺到身體變輕咗。",
            scene_prompt=f"Young Korean man looking at his hands, magical energy flowing around him, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=5,
            speaker="narrator",
            narration="突然，遠處傳來戰鬥聲。",
            scene_prompt=f"Sound waves visual effect, forest path, distant battle, {KOREAN_MANHWA_STYLE}",
            location="forest",
            shot_type="wide_shot",
            motion="zoom_in",
            time_of_day="noon",
        ),

        # ── 遇到鐵柱（2 分鐘）──────────────
        Scene(
            id=6,
            speaker="narrator",
            narration="林澈見到一個半獸人，被三隻魔狼圍攻。",
            scene_prompt=f"Muscular beastman warrior fighting three shadow wolves, claws and teeth bared, forest clearing, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="wide_shot",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=7,
            speaker="tiezhu",
            narration="嚟啊！你哋呢班畜生！",
            scene_prompt=f"Beastman warrior roaring, swinging crude axe, blood on fur, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=8,
            speaker="narrator",
            narration="鐵柱——狼族獸人，已經戰鬥咗三個鐘頭。佢筋疲力盡。",
            scene_prompt=f"Exhausted beastman warrior on one knee, breathing heavily, surrounded by wolves, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=9,
            speaker="linche",
            narration="……幫唔幫？",
            scene_prompt=f"Young Korean man watching from behind tree, conflicted expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_edge",
            shot_type="close_up",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=10,
            speaker="narrator",
            narration="前世嘅林澈會猶豫。但而家……",
            scene_prompt=f"Young Korean man's face hardening, eyes turning cold, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_edge",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=11,
            speaker="linche",
            narration="佢有弱點。我睇到。",
            scene_prompt=f"POV shot with red cracks appearing on wolf's body, showing weak points, {KOREAN_MANHWA_STYLE}",
            location="forest_clearing",
            shot_type="pov_shot",
            motion="static",
            time_of_day="noon",
        ),

        # ── 第一次戰鬥（2 分鐘）────────────
        Scene(
            id=12,
            speaker="narrator",
            narration="林澈衝出去，右手觸踫狼嘅頸部裂痕。",
            scene_prompt=f"Young Korean man dashing forward, hand reaching for wolf's neck, red glow, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="pan_right",
            time_of_day="noon",
        ),
        Scene(
            id=13,
            speaker="narrator",
            narration="砰。狼嘅頸骨折斷。一擊必殺。",
            scene_prompt=f"Shadow wolf collapsing, neck shattered, magical red explosion, {KOREAN_MANHWA_STYLE}",
            location="forest_clearing",
            shot_type="wide_shot",
            motion="zoom_out",
            time_of_day="noon",
        ),
        Scene(
            id=14,
            speaker="tiezhu",
            narration="……你係咩人？",
            scene_prompt=f"Shocked beastman warrior staring at young Korean man, wide eyes, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=15,
            speaker="linche",
            narration="唔好問。專心打。",
            scene_prompt=f"Young Korean man with cold expression, right eye glowing red, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=16,
            speaker="narrator",
            narration="第二隻狼撲過嚟。林澈側身避開，手刀切向佢嘅脊椎裂痕。",
            scene_prompt=f"Dynamic action shot, young man dodging wolf attack, hand striking spine, red glow, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="pan_right",
            time_of_day="noon",
        ),
        Scene(
            id=17,
            speaker="narrator",
            narration="又係一擊。",
            scene_prompt=f"Second wolf falling, spine broken, dust rising, {KOREAN_MANHWA_STYLE}",
            location="forest_clearing",
            shot_type="wide_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=18,
            speaker="narrator",
            narration="最後一隻狼逃走咗。",
            scene_prompt=f"Last shadow wolf running away into forest, scared, {KOREAN_MANHWA_STYLE}",
            location="forest_clearing",
            shot_type="wide_shot",
            motion="pan_left",
            time_of_day="noon",
        ),

        # ── 結盟（2 分鐘）────────────────
        Scene(
            id=19,
            speaker="tiezhu",
            narration="多謝你救我！我叫鐵柱，狼族獸人！",
            scene_prompt=f"Beastman warrior bowing gratefully, big grin, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=20,
            speaker="linche",
            narration="……林澈。",
            scene_prompt=f"Young Korean man looking away, still cold, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="close_up",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=21,
            speaker="tiezhu",
            narration="你嗰隻眼……好恐怖！但好型！",
            scene_prompt=f"Beastman warrior pointing at Korean man's glowing red eye, excited expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu", "linche"],
            location="forest_clearing",
            shot_type="cowork_shot",
            motion="zoom_in",
            time_of_day="noon",
        ),
        Scene(
            id=22,
            speaker="linche",
            narration="……你知唔知附近有城鎮？",
            scene_prompt=f"Young Korean man asking question, still maintaining distance, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="static",
            time_of_day="noon",
        ),
        Scene(
            id=23,
            speaker="tiezhu",
            narration="有！往東行半日就到『灰石鎮』！我帶你去！",
            scene_prompt=f"Beastman warrior pointing east, enthusiastic, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="pan_right",
            time_of_day="noon",
        ),
        Scene(
            id=24,
            speaker="linche",
            narration="……隨你。",
            scene_prompt=f"Young Korean man walking away, slight smirk, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_clearing",
            shot_type="medium_shot",
            motion="pan_right",
            time_of_day="noon",
        ),

        # ── 路上對話（1 分鐘）────────────
        Scene(
            id=25,
            speaker="tiezhu",
            narration="你係邊度嚟？點解著成咁奇怪？",
            scene_prompt=f"Two figures walking through forest, beastman talking excitedly, Korean man listening, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu", "linche"],
            location="forest_path",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="sunset",
        ),
        Scene(
            id=26,
            speaker="linche",
            narration="……好遠嘅地方。你唔會明。",
            scene_prompt=f"Young Korean man looking at sunset, melancholic expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="forest_path",
            shot_type="close_up",
            motion="static",
            time_of_day="sunset",
        ),
        Scene(
            id=27,
            speaker="tiezhu",
            narration="我明！我都被部落趕出嚟！我哋都係孤獨嘅人！",
            scene_prompt=f"Beastman warrior with sad expression, looking down, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="forest_path",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="sunset",
        ),
        Scene(
            id=28,
            speaker="narrator",
            narration="林澈望住鐵柱。佢見到一種嘢——忠誠。",
            scene_prompt=f"Young Korean man looking at beastman with slight softening of expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche", "tiezhu"],
            location="forest_path",
            shot_type="cowork_shot",
            motion="static",
            time_of_day="sunset",
        ),

        # ── 破滅之眼 Lv.1 覺醒（1 分鐘）──
        Scene(
            id=29,
            speaker="narrator",
            narration="夜晚，佢哋紮營。林澈獨自練習能力。",
            scene_prompt=f"Night campfire, young Korean man standing alone, right eye glowing, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="camp",
            shot_type="medium_shot",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=30,
            speaker="linche",
            narration="我感覺到……呢隻眼仲有更多可能性。",
            scene_prompt=f"Close-up of glowing red eye, magical runes appearing around it, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="camp",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),
        Scene(
            id=31,
            speaker="narrator",
            narration="佢集中精神，眼前景象開始變化。",
            scene_prompt=f"POV shot showing detailed cracks on rock, glowing red, revealing internal structure, {KOREAN_MANHWA_STYLE}",
            location="camp",
            shot_type="pov_shot",
            motion="static",
            time_of_day="night",
        ),
        Scene(
            id=32,
            speaker="linche",
            narration="『破滅之眼 Lv.1：裂痕』——我可以看到物理弱點。",
            scene_prompt=f"Young Korean man with fully glowing red eye, confident expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="camp",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="night",
        ),

        # ── 結尾（30 秒）────────────────
        Scene(
            id=33,
            speaker="narrator",
            narration="第二日，佢哋到達灰石鎮。",
            scene_prompt=f"Medieval fantasy town, stone buildings, bustling market, {KOREAN_MANHWA_STYLE}",
            location="greystone_town",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="morning",
        ),
        Scene(
            id=34,
            speaker="tiezhu",
            narration="歡迎嚟到灰石鎮！呢度有冒險者公會！",
            scene_prompt=f"Beastman warrior gesturing at town gate, excited, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["tiezhu"],
            location="greystone_town_gate",
            shot_type="medium_shot",
            motion="static",
            time_of_day="morning",
        ),
        Scene(
            id=35,
            speaker="linche",
            narration="冒險者公會……我需要變強。我需要資源。我需要……返去嘅方法。",
            scene_prompt=f"Young Korean man looking at town with determined expression, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche"],
            location="greystone_town_gate",
            shot_type="close_up",
            motion="zoom_in",
            time_of_day="morning",
        ),
        Scene(
            id=36,
            speaker="narrator",
            narration="破滅者嘅旅程，正式開始。",
            scene_prompt=f"Two figures walking into medieval town, epic wide shot, {KOREAN_MANHWA_STYLE}",
            characters_in_scene=["linche", "tiezhu"],
            location="greystone_town",
            shot_type="wide_shot",
            motion="pan_right",
            time_of_day="morning",
        ),
        Scene(
            id=37,
            speaker="narrator",
            narration="下集預告：灰石鎮冒險者公會，林澈將面對第一個正式任務。",
            scene_prompt=f"Title card with guild emblem, dark fantasy atmosphere, {KOREAN_MANHWA_STYLE}",
            location="abstract",
            shot_type="wide_shot",
            motion="static",
            time_of_day="dramatic",
        ),
    ],
    music_style="epic_dark",
)
