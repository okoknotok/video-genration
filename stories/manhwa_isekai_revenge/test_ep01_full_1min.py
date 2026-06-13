"""
《破滅者》S1E01 測試版 - 10 個場景（足本 1 分鐘）
普通話配音 + 繁體字幕
"""
from stories.manhwa_isekai_revenge.S1_EP01_墜落 import STORY as EP01_STORY, StoryConfig, Scene, Character, KOREAN_MANHWA_STYLE

# 取前 16 個場景（覆蓋開場→成功→背叛→對質→決裂，足本 1 分鐘）
TEST_SCENES = EP01_STORY.scenes[:16]

STORY = StoryConfig(
    story_id="s1_ep01_full_1min",
    title="破滅者 S1E01 足本測試（1 分鐘）",
    characters=[
        Character(
            id="linche",
            name="林澈",
            gender="male",
            age_range="mid_20s",
            appearance_prompt="young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, lean athletic build, small scar near right eye corner, wearing dark tactical jacket",
            personality="冷靜、聰明、善良但即將被背叛",
            voice_id="male-qn-jingying",
            voice_speed=0.95,
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
            voice_speed=0.9,
            voice_pitch=-2,
        ),
        Character(
            id="zhouweiming",
            name="周偉明",
            gender="male",
            age_range="mid_20s",
            appearance_prompt="",
            personality="奸詐、貪婪",
            voice_id="male-qn-jingying",
            voice_speed=1.0,
            voice_pitch=0,
        ),
        Character(
            id="fangshiyun",
            name="方詩韻",
            gender="female",
            age_range="mid_20s",
            appearance_prompt="",
            personality="冷漠、心機",
            voice_id="female-tianmei",
            voice_speed=1.0,
            voice_pitch=0,
        ),
    ],
    scenes=TEST_SCENES,
    music_style="epic_dark",
)
