#!/usr/bin/env python3
"""
安全批量訓練角色 - 會檢查現有狀態，避免重複 call
"""
import sys
import json
import subprocess
from pathlib import Path

CHARACTERS_DIR = Path("characters")

def check_character_status(name):
    """檢查角色狀態"""
    char_dir = CHARACTERS_DIR / name
    if not char_dir.exists():
        return "not_started"
    
    done_file = char_dir / "DONE"
    lock_file = char_dir / ".training.lock"
    
    if done_file.exists():
        return "completed"
    if lock_file.exists():
        return "training"
    return "not_started"

def train_character_safely(config):
    """安全訓練單個角色"""
    name = config["name"]
    status = check_character_status(name)
    
    if status == "completed":
        print(f"✅ {name} 已經完成，跳過")
        return True
    elif status == "training":
        print(f"⏳ {name} 訓練中，跳過")
        return True
    else:
        print(f"🚀 開始訓練 {name}...")
        config_json = json.dumps(config, ensure_ascii=False)
        result = subprocess.run(
            ["python3", "-u", "train_character.py", config_json],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {name} 完成")
            return True
        else:
            print(f"❌ {name} 失敗: {result.stderr}")
            return False

if __name__ == "__main__":
    # 從 stdin 讀取角色配置
    characters = json.load(sys.stdin)
    
    print(f"📋 準備訓練 {len(characters)} 個角色")
    print("=" * 60)
    
    success = 0
    for char in characters:
        if train_character_safely(char):
            success += 1
    
    print("=" * 60)
    print(f"🎉 完成 {success}/{len(characters)} 個角色")
