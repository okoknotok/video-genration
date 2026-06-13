"""代替原本 proxy.py：直接用官方 fal-client 連 fal.ai。"""
import os
import requests
import config

os.environ["FAL_KEY"] = config.FAL_KEY

try:
    import fal_client
except ImportError:
    raise SystemExit("請先安裝：pip install fal-client")

if not config.FAL_KEY:
    print("⚠️  未偵測到 FAL_KEY，請先執行： export FAL_KEY='你的key'")


def _on_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in (update.logs or []):
            msg = log.get("message", "")
            if msg:
                print("    ", msg)


def run(model, arguments, with_logs=True):
    """同步行一個 fal model（內部自動處理 queue + polling，長任務都得）。"""
    return fal_client.subscribe(
        model,
        arguments=arguments,
        with_logs=with_logs,
        on_queue_update=_on_update if with_logs else None,
    )


def upload_file(path):
    """上載本地檔到 fal storage，回傳 public URL。"""
    return fal_client.upload_file(path)


def download(url, dest_path):
    r = requests.get(url, stream=True, timeout=600)
    r.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return dest_path
