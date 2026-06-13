# 🛠️ 設定指南 (Setup Guide)

## 1. 環境要求

- Python 3.10+
- ffmpeg（剪片用）
- Cursor / VS Code（推薦）

## 2. 安裝

```bash
# 進入專案目錄
cd ai-film-studio

# 安裝 Python 套件
pip install -r requirements.txt

# 安裝 ffmpeg
# WSL/Ubuntu:
sudo apt install -y ffmpeg fonts-noto-cjk && fc-cache -fv
# Mac:
brew install ffmpeg
```

## 3. API Key

```bash
cp .env.example .env
# 編輯 .env
FAL_KEY=***
```

取得 FAL_KEY：https://fal.ai/settings

## 4. 用 Cursor 開啟

```bash
cursor /path/to/ai-film-studio
```

## 5. 中文字體（字幕/對話框用）

```bash
# 字體已附帶喺 fonts/ 資料夾
mkdir -p ~/.fonts
cp fonts/NotoSansSC-Regular.ttf ~/.fonts/
fc-cache -fv

# 驗證
fc-list :lang=zh
```

## 6. 常見問題

**Q: FAL_KEY 無效？**
→ 去 fal.ai/settings 重新生成 key

**Q: ffmpeg 搵唔到？**
→ `sudo apt install ffmpeg` 或 `brew install ffmpeg`

**Q: 中文字體顯示唔到？**
→ 確認 `fc-list :lang=zh` 有輸出，冇嘅話裝 fonts-noto-cjk

**Q: characters.json 搵唔到？**
→ 跑一次 `python characters.py create` 就會自動生成
