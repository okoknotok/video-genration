"""
《破滅者》S1E01 測試版 - 前 5 個場景（約 1 分鐘）
"""
from stories.manhwa_isekai_revenge.S1_EP01_墜落 import STORY, StoryConfig, Scene, Character, KOREAN_MANHWA_STYLE

# 只取前 5 個場景做測試
TEST_SCENES = STORY.scenes[:5]

STORY = StoryConfig(
    story_id="s1_ep01_test_1min",
    title="破滅者 S1E01 測試（1 分鐘）",
    characters=[
        Character(
            id="linche",
            name="林澈",
            gender="male",
            age_range="mid_20s",
            appearance_prompt="young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, lean athletic build, small scar near right eye corner, wearing dark tactical jacket",
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
    scenes=TEST_SCENES,
    music_style="epic_dark",
)
