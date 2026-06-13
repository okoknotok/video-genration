"""
《破滅者》S1E01 30 秒測試版（前 8 scenes）
動畫風韓漫 + Ken Burns + 呼吸 + 轉場 + 調色
"""
from stories.manhwa_isekai_revenge.S1_EP01_墜落 import STORY as EP01_STORY, StoryConfig, Character

# 前 8 個 scene ≈ 30 秒
TEST_SCENES = EP01_STORY.scenes[:8]

STORY = StoryConfig(
    story_id="s1_ep01_30s_test",
    title="破滅者 S1E01 30 秒測試（動畫風 + 動態）",
    characters=[
        Character(
            id="linche",
            name="林澈",
            gender="male",
            age_range="mid_20s",
            appearance_prompt="young Korean man, mid 20s, sharp intense dark eyes, short messy black hair, lean athletic build, small scar near right eye corner, wearing dark tactical jacket",
            personality="冷靜、聰明、善良但即將被背叛",
            voice_id="male-qn-qingse",
            voice_speed=1.15,
            voice_pitch=0,
        ),
        Character(
            id="narrator",
            name="旁白",
            gender="male",
            age_range="mature",
            appearance_prompt="",
            personality="低沉、懸疑、引人入勝",
            voice_id="Chinese_Mature_Male_Narrator",
            voice_speed=1.15,
            voice_pitch=-2,
        ),
    ],
    scenes=TEST_SCENES,
    music_style="epic_dark",
)
