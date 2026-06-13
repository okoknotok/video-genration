# 🏗️ 架構說明 (Architecture)

## 系統架構圖

```
用戶輸入（劇本 config / prompt）
          │
          ▼
   ┌─────────────┐
   │  劇本生成    │  Claude 3.5 Sonnet (fal-ai/any-llm)
   │  Script Gen  │  → JSON array of scenes
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  角色圖片    │  Flux Pro + LoRA (自訂角色一致性)
   │  Character   │  → 1024x1024 reference images
   │  Images      │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  場景圖片    │  Flux Dev + Anime LoRA + IP-Adapter + ControlNet
   │  Scene Gen   │  → 1024x576 scene images
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  TTS 配音    │  MiniMax speech-02-turbo
   │  Voice Over  │  → MP3 audio per scene
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  漫畫排版    │  Pillow (Python Imaging)
   │  Manga Layout│  → 1920x1080 full-page panels
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  動畫生成    │  Ken Burns / LTX / MiniMax / Kling
   │  Animation   │  → MP4 clips (可選)
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  背景音樂    │  fal-ai/music/generate
   │  BGM         │  → MP3
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │  剪片合成    │  ffmpeg (xfade轉場 + 字幕燒入)
   │  Final Cut   │  → 最終 MP4
   └─────────────┘
```

## 核心模組

| 檔案 | 功能 | 依賴 |
|------|------|------|
| `main.py` | Config-driven pipeline（完整版） | fal-client, Pillow, ffmpeg |
| `pipeline.py` | Prompt-to-video（簡化版） | config, fal_helpers |
| `characters.py` | 角色 LoRA 訓練 + DB 管理 | fal-client |
| `config.py` | 全域設定 + 模型定義 | — |
| `fal_helpers.py` | fal.ai API 連接 | fal-client |
| `lora_creator.py` | 互動式 LoRA 角色建立 | config, fal_helpers |
| `batch_train_lora.py` | 批量 LoRA 訓練 | characters.py |
| `batch_train_safe.py` | 安全批量訓練（檢查狀態） | characters.py |

## 資料流

```
stories/my_story.py (STORY config)
    │
    ├── characters[]  → characters.py (LoRA lookup)
    │                     → characters.json (DB)
    │
    ├── scenes[]      → scene generation (Flux Pro)
    │                     → TTS (MiniMax)
    │                     → manga layout (Pillow)
    │                     → animation (optional)
    │
    └── music_style   → BGM generation (fal-ai/music)
    
    Output: cache/{story_id}/{story_id}_with_subtitles.mp4
```

## 角色系統

角色分三級（慳錢用）：

| 級別 | LoRA | 變化圖 | 成本 |
|------|------|--------|------|
| ⭐ 主角 (protagonist) | ✅ 1000步 | 8張 | ~$2 |
| 🔹 副角 (supporting) | ✅ 800步 | 6張 | ~$1.5 |
| · 配角 (minor) | ❌ | 0張 | ~$0.03 |

LoRA 流程：
1. Flux Dev 生成 hero image
2. Flux Pro Kontext 生成多角度變化圖
3. 打包 zip → fal-ai/flux-lora-fast-training
4. 下載 .safetensors → characters.json

## 粵語 → 普通話轉換

main.py 內建 `_YUE_TO_MANDARIN` 轉換表：
- TTS 配音：自動將粵語口語轉普通話書面語
- 字幕：自動轉繁體中文
- 可選裝 `opencc` 做繁簡轉換
