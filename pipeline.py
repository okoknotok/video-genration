"""核心引擎：劇本 → 圖 → TTS → 選擇性輕微動畫 → ffmpeg 剪成一條 MP4。
可直接 import generate_video()，亦可 CLI：python pipeline.py --prompt "..." """
import os
import re
import json
import time
import shutil
import tempfile
import subprocess
import config
import fal_helpers as fal

W, H, FPS = config.VIDEO_WIDTH, config.VIDEO_HEIGHT, config.VIDEO_FPS


# ============ 角色庫 ============
def load_characters():
    if os.path.exists(config.CHARACTERS_DB):
        with open(config.CHARACTERS_DB, encoding="utf-8") as f:
            return json.load(f)
    return []


def find_character(name):
    for c in load_characters():
        if c.get("name") == name:
            return c
    return None


# ============ 1. 劇本 ============
def generate_script(story_prompt, scene_count=12, tone="爽快霸道"):
    chars = load_characters()
    char_list = "、".join(f"{c['name']}（{c.get('description','')}）" for c in chars) or "由 AI 自行創建"
    prompt = f"""你係韓漫爽文短劇編劇。根據大綱，寫 {scene_count} 場戲，語氣{tone}。
已有角色：{char_list}
每場戲必須有：scene_id, character, description（英文視覺描述）, narration（中文旁白）, dialogue（中文對白，可空）, animate（true/false）, motion（英文輕微動作描述；animate=false 時填 ""）。
重要：韓漫以靜態分鏡為主，只有約 30% 高潮/轉折場景先 animate:true，動作要克制輕微（微風、眨眼、呼吸、衣角飄）。
只回 JSON array，唔好任何其他文字。
故事大綱：{story_prompt}"""

    result = fal.run(config.LLM_ENDPOINT,
                     {"model": config.LLM_MODEL, "prompt": prompt, "max_tokens": 8000},
                     with_logs=False)
    text = result.get("output") or result.get("response") or ""
    m = re.search(r"\[[\s\S]*\]", text)
    if not m:
        raise RuntimeError("LLM 冇回傳 JSON：" + text[:200])
    scenes = json.loads(m.group(0))
    for i, s in enumerate(scenes):
        s.setdefault("scene_id", i + 1)
        s["animate"] = bool(s.get("animate"))
        s.setdefault("motion", "")
        s.setdefault("character", "")
        s.setdefault("narration", "")
        s.setdefault("dialogue", "")
    return scenes


# ============ 2. 圖片（自動套角色 LoRA）============
def _img_size():
    return "landscape_16_9" if W >= H else "portrait_16_9"


def generate_image(scene, style_key):
    style = config.IMAGE_STYLES.get(style_key, config.IMAGE_STYLES["manhwa"])
    base = f"{style}, {scene['description']}"
    char = find_character(scene.get("character", ""))
    if char and char.get("lora_url"):
        result = fal.run("fal-ai/flux-lora", {
            "prompt": f"{char.get('trigger_word','')}, {base}",
            "loras": [{"path": char["lora_url"], "scale": 1.0}],
            "image_size": _img_size(),
            "num_inference_steps": 28,
        }, with_logs=False)
    else:
        result = fal.run("fal-ai/flux/dev", {
            "prompt": base,
            "image_size": _img_size(),
        }, with_logs=False)
    return result["images"][0]["url"]


# ============ 3. TTS（失敗自動轉靜音，唔會搞死成條 pipeline）============
def generate_tts(text, voice_id, dest):
    if not text.strip():
        return None
    try:
        result = fal.run(config.TTS_MODEL, {
            "text": text,
            "voice_setting": {"voice_id": voice_id, "speed": 1.0},
        }, with_logs=False)
        url = (result.get("audio") or {}).get("url") or result.get("audio_url")
        if not url:
            return None
        fal.download(url, dest)
        return dest
    except Exception as e:
        print(f"    ⚠️ TTS 失敗（用靜音代替）：{e}")
        return None


# ============ 4. 動畫（只動標記場景，輕微）============
def _motion_prompt(scene, strength):
    core = (scene.get("motion") or "").strip() or "gentle ambient motion"
    lvl = ("moderate movement, smooth natural motion" if strength == "中等"
           else "very subtle minimal movement, slight breeze, soft breathing, slow blink, cinemagraph, mostly still")
    return f"{core}, {lvl}"


def animate_scene(image_url, scene, model_key, strength, dest):
    m = config.VIDEO_MODELS.get(model_key)
    if not m or not m["fal_id"]:
        return None
    args = {"image_url": image_url, "prompt": _motion_prompt(scene, strength)}
    args.update(m.get("extra", {}))
    if model_key == "kling":
        args["cfg_scale"] = 0.3 if strength == "輕微" else 0.5
    try:
        result = fal.run(m["fal_id"], args)
        url = (result.get("video") or {}).get("url") or result.get("video_url")
        if not url:
            return None
        fal.download(url, dest)
        return dest
    except Exception as e:
        print(f"    ⚠️ 動畫失敗（改用靜態）：{e}")
        return None


# ============ 5. ffmpeg ============
def check_ffmpeg():
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError("搵唔到 ffmpeg / ffprobe，請先安裝 ffmpeg")


def run_ffmpeg(args):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + args
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, p.stdout, p.stderr)
    return p


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def make_silent_audio(duration, dest):
    run_ffmpeg(["-f", "lavfi", "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", f"{duration:.3f}", "-c:a", "aac", "-b:a", "128k", dest])
    return dest


def clip_from_image(image_path, audio_path, duration, dest):
    """靜態圖 + Ken Burns 輕微縮放。先升 2 倍解析度令縮放唔會 jitter/糊。"""
    frames = max(int(duration * FPS), 1)
    sw, sh = W * 2, H * 2
    vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
          f"crop={sw}:{sh},"
          f"zoompan=z='min(zoom+0.0008,1.18)':d={frames}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")
    run_ffmpeg(["-loop", "1", "-i", image_path, "-i", audio_path,
                "-filter:v", vf, "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                "-r", str(FPS), "-t", f"{duration:.3f}", "-pix_fmt", "yuv420p", dest])
    return dest


def clip_from_video(video_path, audio_path, duration, dest):
    """動畫片：片短過旁白就 loop 填滿，長過就 cut。"""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},setsar=1,fps={FPS},format=yuv420p")
    run_ffmpeg(["-stream_loop", "-1", "-i", video_path, "-i", audio_path,
                "-filter:v", vf, "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                "-r", str(FPS), "-t", f"{duration:.3f}", "-pix_fmt", "yuv420p", dest])
    return dest


def concat_clips(clip_paths, dest):
    work = os.path.dirname(os.path.abspath(clip_paths[0]))
    list_file = os.path.join(work, "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            ap = os.path.abspath(p).replace("'", r"'\''")
            f.write(f"file '{ap}'\n")
    try:
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", dest])
    except subprocess.CalledProcessError:
        run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_file,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                    "-r", str(FPS), "-pix_fmt", "yuv420p", dest])
    return dest


def add_bgm(video_path, bgm_path, dest, volume=0.15):
    run_ffmpeg(["-i", video_path, "-stream_loop", "-1", "-i", bgm_path,
                "-filter_complex",
                f"[1:a]volume={volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", dest])
    return dest


# ============ 主流程 ============
def generate_video(story_prompt, scene_count=12, tone="爽快霸道", style="manhwa",
                   voice="f1", animation_model="minimax", animate_scope="ai",
                   motion_strength="輕微", bgm_path=None, output_name=None, progress_cb=None):
    """
    animate_scope: 'ai'=只動 AI 標記場景(預設) / 'all'=全部都動 / 'none'=全部靜態
    回傳：最終 mp4 路徑
    """
    def log(msg):
        print(msg)
        if progress_cb:
            try: progress_cb(msg)
            except Exception: pass

    check_ffmpeg()
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    work = tempfile.mkdtemp(prefix="job_", dir=config.TEMP_DIR)

    voice_id = config.TTS_VOICES.get(voice, list(config.TTS_VOICES.values())[0])["id"]
    use_video = animation_model != "ken-burns" and animate_scope != "none"

    log("📝 生成劇本中…")
    scenes = generate_script(story_prompt, scene_count, tone)
    anim_marked = sum(1 for s in scenes if s["animate"])
    log(f"✅ 劇本完成：{len(scenes)} 場，其中 {anim_marked} 場標記會動")

    clips = []
    for idx, scene in enumerate(scenes, 1):
        sid = scene["scene_id"]
        log(f"🎬 [{idx}/{len(scenes)}] 場 {sid}：生成圖片…")
        try:
            image_url = generate_image(scene, style)
        except Exception as e:
            log(f"    ❌ 圖片失敗，跳過呢場：{e}")
            continue
        img_path = os.path.join(work, f"s{sid}.png")
        fal.download(image_url, img_path)

        text = (scene.get("narration", "") + " " + scene.get("dialogue", "")).strip()
        audio_path = os.path.join(work, f"s{sid}.mp3")
        got_audio = generate_tts(text, voice_id, audio_path) if text else None
        if got_audio:
            dur = max(ffprobe_duration(audio_path) + 0.5, 2.0)
        else:
            dur = 3.0
            make_silent_audio(dur, audio_path)

        will_anim = use_video and (animate_scope == "all" or scene["animate"])
        video_path = None
        if will_anim:
            log(f"    🎞️ 場 {sid}：{animation_model} 動畫生成中（較慢，耐心等）…")
            video_path = animate_scene(image_url, scene, animation_model,
                                       motion_strength, os.path.join(work, f"s{sid}_raw.mp4"))

        clip_path = os.path.join(work, f"clip_{idx:04d}.mp4")
        try:
            if video_path:
                clip_from_video(video_path, audio_path, dur, clip_path)
                log(f"    ✅ 場 {sid}：動畫片段完成")
            else:
                clip_from_image(img_path, audio_path, dur, clip_path)
                log(f"    ✅ 場 {sid}：靜態(Ken Burns)片段完成")
            clips.append(clip_path)
        except subprocess.CalledProcessError as e:
            log(f"    ❌ 場 {sid} ffmpeg 失敗，跳過：{(e.stderr or '')[:200]}")

    if not clips:
        raise RuntimeError("冇任何片段成功生成")

    log("🔗 用 ffmpeg 合併所有片段…")
    name = output_name or f"video_{int(time.time())}"
    raw_out = os.path.join(work, "merged.mp4")
    concat_clips(clips, raw_out)

    final_out = os.path.join(config.OUTPUT_DIR, f"{name}.mp4")
    if bgm_path and os.path.exists(bgm_path):
        log("🎵 加背景音樂…")
        add_bgm(raw_out, bgm_path, final_out)
    else:
        shutil.move(raw_out, final_out)

    shutil.rmtree(work, ignore_errors=True)
    log(f"🎉 完成！輸出：{final_out}")
    return final_out


# ============ CLI ============
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="韓漫爽文影片生成")
    p.add_argument("--prompt", required=True, help="故事大綱")
    p.add_argument("--scenes", type=int, default=12)
    p.add_argument("--tone", default="爽快霸道")
    p.add_argument("--style", default="manhwa", choices=list(config.IMAGE_STYLES))
    p.add_argument("--voice", default="f1", choices=list(config.TTS_VOICES))
    p.add_argument("--model", default="minimax", choices=list(config.VIDEO_MODELS))
    p.add_argument("--scope", default="ai", choices=["ai", "all", "none"])
    p.add_argument("--strength", default="輕微", choices=["輕微", "中等"])
    p.add_argument("--bgm", default=None)
    p.add_argument("--name", default=None)
    a = p.parse_args()
    generate_video(a.prompt, a.scenes, a.tone, a.style, a.voice,
                   a.model, a.scope, a.strength, a.bgm, a.name)
