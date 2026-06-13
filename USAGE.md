# 📖 使用指南 (Usage Guide)

## 方式 A：Config-Driven Pipeline（完整控制）

### 1. 建立劇本

```bash
cp stories/story_template.py stories/my_story.py
```

編輯 `stories/my_story.py`：

```python
from stories.story_template import StoryConfig, Character, Scene

STORY = StoryConfig(
    story_id="my_story_01",
    title="我的故事",
    characters=[
        Character(
            id="hero",
            name="陳浩",
            gender="male",
            age_range="early_30s",
            appearance_prompt="Asian man, short black hair, leather jacket...",
            voice_id="Chinese_Mature_Male_Narrator",
        ),
    ],
    scenes=[
        Scene(
            id=1,
            speaker="narrator",
            narration="故事開始...",
            scene_prompt="A dark city street at night, cinematic...",
            characters_in_scene=["hero"],
            motion="zoom_in",
        ),
    ],
    music_style="epic_cinematic",
)
```

### 2. 生成影片

```bash
python main.py --config stories/my_story.py
```

輸出：`cache/my_story_01/my_story_01_with_subtitles.mp4`

---

## 方式 B：Prompt-to-Video（快速原型）

```bash
# 基本用法
python pipeline.py --prompt "女主重生回到被退婚前一年，誓要打臉渣男" --scenes 12

# 指定模型
python pipeline.py --prompt "..." --model minimax --style manhwa

# 加背景音樂
python pipeline.py --prompt "..." --bgm bgm.mp3

# 全部靜態（最慳錢）
python pipeline.py --prompt "..." --model ken-burns --scope none
```

### 參數說明

```
--prompt     故事大綱（必填）
--scenes     場景數量（預設 12）
--tone       語氣風格（預設 "爽快霸道"）
--style      圖片風格：manhwa / cinematic / anime / cdrama
--voice      語音：f1(少女) / f2(甜美) / m1(青年) / m2(旁白)
--model      動畫模型：ken-burns / ltx / minimax / kling
--scope      動畫範圍：ai(只動AI標記) / all(全部動) / none(全部靜態)
--strength   動作強度：輕微 / 中等
--bgm        背景音樂檔案路徑
--name       輸出檔名
```

---

## 角色管理

```bash
# 互動建立角色
python characters.py create

# 批量建立（從 JSON）
python characters.py create-batch batch_config.json

# 列出所有角色
python characters.py list

# 查看角色詳情
python characters.py preview 陳默

# 刪除角色
python characters.py delete 陳默

# 匯出角色資料
python characters.py export
```

### 角色 JSON 格式

```json
{
  "characters": [
    {
      "name": "陳默",
      "trigger_word": "ohwx_chenmo",
      "description": "25yo asian man, short black hair, sharp jawline, wearing dark suit",
      "role": "protagonist",
      "personality": "冷酷、復仇心切",
      "voice_id": "male-qn-jingying",
      "style": "manhwa"
    }
  ]
}
```

---

## LoRA 訓練（簡化版）

```bash
# 互動模式
python lora_creator.py

# CLI 模式
python lora_creator.py 林澈 ohwx_linche "20yo asian man, messy hair, hoodie" manhwa
```

---

## 已有劇本

### 異世界復仇系列 (manhwa_isekai_revenge)

```bash
# S1E01 墜落（47 scenes）
python main.py --config stories/manhwa_isekai_revenge/S1_EP01_墜落.py

# S1E02 獸人（37 scenes）
python main.py --config stories/manhwa_isekai_revenge/S1_EP02_獸人.py

# S1E03 灰石鎮（34 scenes）
python main.py --config stories/manhwa_isekai_revenge/S1_EP03_灰石鎮.py
```

---

## 進階用法

### 批量訓練角色

```bash
python batch_train_lora.py
```

### 安全批量訓練（檢查狀態，避免重複）

```bash
cat batch_config.json | python batch_train_safe.py
```

### 自訂音樂風格

編輯 `stories/music_presets.py`：

```python
MUSIC_PRESETS["my_style"] = {
    "prompt": "Your custom music prompt...",
    "mood": "自訂風格",
}
```

---

## 輸出結構

```
cache/{story_id}/
├── script.json              # 劇本 JSON
├── characters/              # 角色 reference images
│   └── {char_id}.png
├── scenes/                  # 場景圖片
│   └── scene_01_image.png
├── audio/                   # TTS 音頻
│   └── scene_01_audio.mp3
├── manga_pages/             # 漫畫排版頁
│   └── page_01.png
├── page_videos/             # 各頁影片
│   └── page_01.mp4
├── combined_video.mp4       # 合併影片（無字幕）
├── background_music.mp3     # 背景音樂
├── {story_id}_final.mp4     # 最終影片（無字幕）
└── {story_id}_with_subtitles.mp4  # ✅ 最終成品（含字幕）
```

---

## 成本估算

| 項目 | 成本 |
|------|------|
| 角色 LoRA（主角） | ~$2/人 |
| 角色 LoRA（副角） | ~$1.5/人 |
| 場景圖片（Flux Dev） | ~$0.01/張 |
| TTS（MiniMax） | ~$0.01/場景 |
| 動畫（MiniMax） | ~$0.30/5秒 |
| 動畫（Kling） | ~$0.50/5秒 |
| 背景音樂 | ~$0.10 |
| **12場景短片（全靜態）** | **~$0.50** |
| **12場景短片（30%動畫）** | **~$3-5** |
| **47場景完整集（全靜態）** | **~$2** |
