#!/usr/bin/env python3
"""
批量訓練重要角色（LoRA）- 安全版，會檢查現有狀態
"""
import sys
import json
import subprocess
from pathlib import Path

CHARACTERS_DIR = Path("characters")

def check_status(name):
    char_dir = CHARACTERS_DIR / name
    if not char_dir.exists():
        return "not_started"
    if (char_dir / "DONE").exists():
        return "completed"
    if (char_dir / ".training.lock").exists():
        return "training"
    return "not_started"

# LoRA 重要角色（仇人）
LORA_CHARS = [
    {
        "name": "阿標",
        "trigger": "ohwx_ahbiu",
        "prompt": "Korean man, early 30s, muscular build, short cropped hair, scar on left cheek, wearing black tactical vest, intimidating expression, bodyguard/mercenary aura, manhwa style, high quality, detailed face",
        "role": "protagonist"
    },
    {
        "name": "陳教授",
        "trigger": "ohwx_chenprof",
        "prompt": "Korean man, late 50s, grey hair neatly combed back, glasses, wearing white lab coat over dress shirt, scholarly but sinister expression, university professor aura, manhwa style, high quality, detailed face",
        "role": "protagonist"
    },
    {
        "name": "黑影人",
        "trigger": "ohwx_heiyingren",
        "prompt": "mysterious figure, gender ambiguous, wearing dark hooded cloak, face mostly in shadow with only glowing red eyes visible, ominous presence, dark energy aura, manhwa style, high quality, mysterious atmosphere",
        "role": "protagonist"
    }
]

print("🎭 檢查 LoRA 角色狀態...")
to_train = []
for char in LORA_CHARS:
    status = check_status(char["name"])
    if status == "completed":
        print(f"  ✅ {char['name']} 已完成")
    elif status == "training":
        print(f"  ⏳ {char['name']} 訓練中")
    else:
        print(f"  🚀 {char['name']} 需要訓練")
        to_train.append(char)

if not to_train:
    print("🎉 所有 LoRA 角色已完成！")
    sys.exit(0)

print(f"\n📋 準備訓練 {len(to_train)} 個 LoRA 角色")
print("=" * 60)

success = 0
for char in to_train:
    print(f"\n🚀 開始 {char['name']}...")
    config_json = json.dumps(char, ensure_ascii=False)
    result = subprocess.run(
        ["python3", "-u", "train_character.py", config_json],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"✅ {char['name']} 完成")
        success += 1
    else:
        print(f"❌ {char['name']} 失敗")
        print(result.stderr[:200])

print("=" * 60)
print(f"🎉 LoRA 角色：{success}/{len(to_train)} 完成")
