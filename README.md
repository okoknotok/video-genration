# 🎬 AI Film Studio — 全自動 AI 影片生成系統

從劇本到成片，一鍵生成韓漫風格短劇。

## 功能

- 📝 **劇本生成** — Claude LLM 自動生成分鏡劇本
- 🎨 **圖片生成** — Flux Pro + LoRA 自訂角色一致性
- 🔊 **TTS 配音** — MiniMax 語音合成（台灣腔/普通話）
- 🎬 **動畫生成** — Ken Burns / LTX / MiniMax / Kling 四種模型
- 🎵 **背景音樂** — AI 生成配樂
- 📖 **漫畫分鏡** — 自動排版成漫畫頁 + 對話框
- ✂️ **剪片合成** — ffmpeg 自動合成最終影片

## 快速開始

```bash
# 1. 安裝依賴
pip install -r requirements.txt
sudo apt install ffmpeg  # Mac: brew install ffmpeg

# 2. 設定 API Key
cp .env.example .env
# 編輯 .env，填入 FAL_KEY（從 https://fal.ai/settings 取得）

# 3. 生成角色 LoRA（一次過，約 $2/角色）
python characters.py create

# 4. 生成影片
python main.py --config stories/story_01.py
```

## 資料夾結構

```
ai-film-studio/
├── main.py                  # 主程式（config-driven pipeline）
├── pipeline.py              # 簡化版 pipeline（prompt → 影片）
├── characters.py            # 角色管理系統（LoRA 訓練）
├── config.py                # 全域設定 + 模型定義
├── fal_helpers.py           # fal.ai API 連接層
├── lora_creator.py          # 互動式 LoRA 角色建立
├── batch_train_lora.py      # 批量 LoRA 訓練
├── batch_train_safe.py      # 安全批量訓練（檢查狀態）
├── stories/
│   ├── story_template.py    # 劇本模板
│   ├── music_presets.py     # 背景音樂風格
│   └── manhwa_isekai_revenge/  # 異世界復仇系列
│       ├── OUTLINE.md       # 故事大綱
│       ├── S1_EP01_墜落.py  # 第1集（47 scenes）
│       ├── S1_EP02_獸人.py  # 第2集（37 scenes）
│       └── S1_EP03_灰石鎮.py # 第3集（34 scenes）
├── characters_data/         # 角色資料庫（自動生成）
├── fonts/                   # 中文字體
├── output/                  # 生成輸出
├── cache/                   # 快取檔案
└── .env                     # API Key（唔好 commit）
```

## 兩種使用方式

### 方式 A：Config-Driven（main.py）
完整控制每個場景、角色、鏡頭。適合已有劇本。

```bash
python main.py --config stories/manhwa_isekai_revenge/S1_EP01_墜落.py
```

### 方式 B：Prompt-to-Video（pipeline.py）
LLM 自動生成劇本，快速原型。

```bash
python pipeline.py --prompt "女主重生回到被退婚前一年" --scenes 12 --model minimax
```

## 動畫模型選擇

| 模型 | 價錢 | 速度 | 適合 |
|------|------|------|------|
| ken-burns | 免費 | 即時 | 靜態為主，最慳錢 |
| ltx | ~$0.02/5秒 | 快 | 輕微動作 |
| minimax | ~$0.30/5秒 | 中 | 韓漫角色生動（推薦）|
| kling | ~$0.50/5秒 | 慢 | 高潮/打鬥場景 |

## 更多文檔

- [SETUP.md](SETUP.md) — 安裝設定步驟
- [ARCHITECTURE.md](ARCHITECTURE.md) — 系統架構 + 模組說明
- [USAGE.md](USAGE.md) — 詳細使用指南 + 所有參數
