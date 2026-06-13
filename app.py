"""
AI Film Studio Web App
Two modes: 🎬 Cinematic (full pipeline) / ⚡ Shorts (fast vertical)
"""
import os
import sys
import json
import uuid
import time
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from flask import Flask, render_template, request, jsonify, send_from_directory, Response

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
JOBS_DIR = BASE_DIR / "jobs"
JOBS_DIR.mkdir(exist_ok=True)

# In-memory job store
jobs = {}
jobs_lock = threading.Lock()


# ============================================================
# Models & Styles Config
# ============================================================

MODES = {
    "cinematic": {
        "name": "🎬 Cinematic",
        "desc": "完整 pipeline — LoRA 角色一致性、漫畫分鏡、長片",
        "models": {
            "ken-burns": {"label": "Ken Burns（靜態）", "cost": "免費", "speed": "即時"},
            "ltx": {"label": "LTX Video", "cost": "~$0.02/5s", "speed": "快"},
            "minimax": {"label": "MiniMax Live", "cost": "~$0.30/5s", "speed": "中"},
            "kling": {"label": "Kling", "cost": "~$0.50/5s", "speed": "慢"},
        },
        "styles": {
            "manhwa": "韓漫風格",
            "cinematic": "電影寫實",
            "anime": "日式動畫",
            "cdrama": "中國古風",
        },
        "aspect": "16:9",
        "resolution": "1920x1080",
    },
    "shorts": {
        "name": "⚡ Shorts",
        "desc": "快速 60 秒直向短片 — YouTube Shorts / IG Reels / TikTok",
        "models": {
            "ken-burns": {"label": "Ken Burns（靜態）", "cost": "免費", "speed": "即時"},
            "seedance-lite": {"label": "Seedance Lite（即夢）", "cost": "~$0.08/5s", "speed": "快"},
            "seedance-pro": {"label": "Seedance Pro", "cost": "~$0.25/5s", "speed": "中"},
            "minimax": {"label": "MiniMax Live", "cost": "~$0.30/5s", "speed": "中"},
            "kling": {"label": "Kling", "cost": "~$0.50/5s", "speed": "慢"},
        },
        "styles": {
            "realistic": "真人寫實",
            "cinematic": "電影質感",
            "dark_moody": "暗黑懸疑",
            "bright_vibrant": "明亮活力",
            "vintage": "復古懷舊",
        },
        "aspect": "9:16",
        "resolution": "1080x1920",
    },
}

VOICE_OPTIONS = {
    "f1": "少女音（女）",
    "f2": "甜美音（女）",
    "m1": "青澀青年（男）",
    "m2": "旁白男聲",
    "m3": "磁性男聲",
}


# ============================================================
# Routes
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config")
def get_config():
    return jsonify({
        "modes": MODES,
        "voices": VOICE_OPTIONS,
    })


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.json
    mode = data.get("mode", "shorts")
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "請輸入故事大綱或主題"}), 400

    job_id = str(uuid.uuid4())[:8]
    job = {
        "id": job_id,
        "mode": mode,
        "prompt": prompt,
        "status": "queued",
        "progress": 0,
        "logs": [],
        "created_at": datetime.now().isoformat(),
        "settings": {
            "model": data.get("model", "ken-burns"),
            "style": data.get("style", "realistic" if mode == "shorts" else "manhwa"),
            "scenes": data.get("scenes", 6 if mode == "shorts" else 12),
            "voice": data.get("voice", "m2"),
            "tone": data.get("tone", "懸疑緊張"),
            "animate_scope": data.get("animate_scope", "ai"),
            "motion_strength": data.get("motion_strength", "輕微"),
        },
        "output": None,
        "error": None,
    }

    with jobs_lock:
        jobs[job_id] = job

    # Save job to disk
    _save_job(job)

    # Start generation in background thread
    thread = threading.Thread(target=_run_pipeline, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/api/status/<job_id>")
def get_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/stream/<job_id>")
def stream_logs(job_id):
    def generate_stream():
        last_idx = 0
        for _ in range(600):  # 10 min max
            with jobs_lock:
                job = jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            # Send new logs
            logs = job.get("logs", [])
            if len(logs) > last_idx:
                for log in logs[last_idx:]:
                    yield f"data: {json.dumps({'log': log, 'progress': job['progress']})}\n\n"
                last_idx = len(logs)
            
            if job["status"] in ("done", "error"):
                yield f"data: {json.dumps({'status': job['status'], 'output': job.get('output'), 'error': job.get('error')})}\n\n"
                break
            
            time.sleep(0.5)
    
    return Response(generate_stream(), mimetype="text/event-stream")


@app.route("/api/jobs")
def list_jobs():
    job_list = []
    for jf in sorted(JOBS_DIR.glob("*.json"), reverse=True)[:20]:
        try:
            with open(jf, encoding="utf-8") as f:
                j = json.load(f)
            job_list.append({
                "id": j["id"],
                "mode": j["mode"],
                "prompt": j["prompt"][:80],
                "status": j["status"],
                "created_at": j["created_at"],
                "output": j.get("output"),
            })
        except:
            pass
    return jsonify(job_list)


@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory(str(OUTPUT_DIR), filename)


# ============================================================
# Pipeline Runner
# ============================================================

def _run_pipeline(job_id):
    with jobs_lock:
        job = jobs[job_id]
    
    def log(msg):
        with jobs_lock:
            job["logs"].append(msg)
        _save_job(job)
    
    def update_progress(pct):
        with jobs_lock:
            job["progress"] = pct
        _save_job(job)

    try:
        job["status"] = "running"
        _save_job(job)
        
        settings = job["settings"]
        mode = job["mode"]
        prompt = job["prompt"]
        
        # Import pipeline modules
        sys.path.insert(0, str(BASE_DIR))
        import config as cfg
        import fal_helpers as fal
        
        # Ensure FAL_KEY is set
        fal_key = os.environ.get("FAL_KEY", "")
        if not fal_key:
            # Try .env file
            env_path = BASE_DIR / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("FAL_KEY="):
                            fal_key = line.split("=", 1)[1].strip()
                            break
        if fal_key:
            os.environ["FAL_KEY"] = fal_key
            cfg.FAL_KEY = fal_key
        
        # ========== Phase 1: Generate Script ==========
        log("📝 Phase 1: 生成劇本...")
        update_progress(5)
        
        scene_count = settings["scenes"]
        tone = settings["tone"]
        
        if mode == "shorts":
            system_prompt = f"""You are a viral YouTube Shorts scriptwriter. Write a {scene_count}-scene script for a 60-second vertical short video.
Tone: {tone}
Requirements:
- Each scene should be 3-8 seconds
- Strong hook in first 3 seconds
- Vertical 9:16 format optimized
- No dialogue needed, just narration/voiceover
- End with a cliffhanger or punchline for rewatch
- Each scene needs: scene_id, description (English visual prompt), narration (Chinese), animate (true/false)
- About 30% scenes should animate:true
- Return ONLY a JSON array, no other text."""
        else:
            system_prompt = f"""You are a Korean manhwa drama scriptwriter. Write a {scene_count}-scene cinematic script.
Tone: {tone}
Requirements:
- Each scene needs: scene_id, description (English visual prompt), narration (Chinese), dialogue (Chinese, can be empty), animate (true/false), motion (English)
- About 30% scenes should animate:true with subtle motion
- Return ONLY a JSON array, no other text."""
        
        full_prompt = f"{system_prompt}\n\nStory/topic: {prompt}"
        
        result = fal.run(cfg.LLM_ENDPOINT, {
            "model": cfg.LLM_MODEL,
            "prompt": full_prompt,
            "max_tokens": 6000,
        }, with_logs=False)
        
        text = result.get("output") or result.get("response") or ""
        
        import re
        m = re.search(r"\[[\s\S]*\]", text)
        if not m:
            raise RuntimeError("LLM 冇回傳有效 JSON: " + text[:200])
        
        scenes = json.loads(m.group(0))
        for i, s in enumerate(scenes):
            s.setdefault("scene_id", i + 1)
            s["animate"] = bool(s.get("animate"))
        
        log(f"✅ 劇本完成: {len(scenes)} 場景")
        update_progress(15)
        
        # ========== Phase 2: Generate Images ==========
        log("🎨 Phase 2: 生成場景圖片...")
        
        work_dir = OUTPUT_DIR / f"job_{job_id}"
        work_dir.mkdir(parents=True, exist_ok=True)
        
        style_key = settings["style"]
        
        # Style prompts
        SHORTS_STYLES = {
            "realistic": "photorealistic, hyperrealistic, professional photography, 8K, sharp focus",
            "cinematic": "cinematic photo, dramatic lighting, film grain, movie still, 8K",
            "dark_moody": "dark moody atmosphere, low key lighting, shadows, mysterious, cinematic horror",
            "bright_vibrant": "bright vibrant colors, sunny, energetic, pop art influenced, vivid",
            "vintage": "vintage retro style, warm tones, film photography, nostalgic, 1970s aesthetic",
        }
        
        style_prompt = SHORTS_STYLES.get(style_key, cfg.IMAGE_STYLES.get(style_key, ""))
        
        # Vertical or horizontal
        if mode == "shorts":
            img_size = {"width": 768, "height": 1344}  # 9:16
        else:
            img_size = {"width": 1344, "height": 768}  # 16:9
        
        image_urls = []
        image_paths = []
        
        for idx, scene in enumerate(scenes):
            pct = 15 + int(35 * (idx + 1) / len(scenes))
            update_progress(pct)
            
            desc = scene.get("description", "")
            full_prompt_img = f"{style_prompt}, {desc}, high quality, detailed, no text, no words, no letters"
            
            log(f"  🖼️ 場景 {idx+1}/{len(scenes)}: 生成圖片...")
            
            try:
                if mode == "shorts":
                    # Use Flux Dev for speed
                    result = fal.run("fal-ai/flux/dev", {
                        "prompt": full_prompt_img,
                        "image_size": img_size,
                        "num_inference_steps": 25,
                    }, with_logs=False)
                else:
                    # Use Flux Pro for quality
                    result = fal.run("fal-ai/flux-pro/v1.1", {
                        "prompt": full_prompt_img,
                        "image_size": img_size,
                        "num_inference_steps": 40,
                        "guidance_scale": 3.5,
                    }, with_logs=False)
                
                url = result["images"][0]["url"]
                img_path = work_dir / f"scene_{idx+1:02d}.png"
                fal.download(url, str(img_path))
                image_urls.append(url)
                image_paths.append(str(img_path))
                log(f"  ✅ 場景 {idx+1} 圖片完成")
                
            except Exception as e:
                log(f"  ⚠️ 場景 {idx+1} 圖片失敗: {e}")
        
        if not image_paths:
            raise RuntimeError("所有場景圖片都失敗")
        
        log(f"✅ {len(image_paths)} 張圖片完成")
        update_progress(50)
        
        # ========== Phase 3: TTS ==========
        log("🔊 Phase 3: 生成 TTS 配音...")
        
        voice_key = settings["voice"]
        voice_id = cfg.TTS_VOICES.get(voice_key, {"id": "presenter_male"})["id"]
        
        audio_paths = []
        durations = []
        
        for idx, scene in enumerate(scenes):
            if idx >= len(image_paths):
                break
            
            pct = 50 + int(20 * (idx + 1) / len(scenes))
            update_progress(pct)
            
            text = (scene.get("narration", "") + " " + scene.get("dialogue", "")).strip()
            
            if not text:
                # Silent audio
                dur = 3.0
                audio_path = work_dir / f"scene_{idx+1:02d}_silent.mp3"
                _make_silent(dur, str(audio_path))
                audio_paths.append(str(audio_path))
                durations.append(dur)
                continue
            
            log(f"  🎙️ 場景 {idx+1}: TTS...")
            audio_path = work_dir / f"scene_{idx+1:02d}_audio.mp3"
            
            try:
                tts_result = fal.run(cfg.TTS_MODEL, {
                    "text": text,
                    "voice_setting": {"voice_id": voice_id, "speed": 1.0},
                }, with_logs=False)
                audio_url = (tts_result.get("audio") or {}).get("url") or tts_result.get("audio_url")
                if audio_url:
                    fal.download(audio_url, str(audio_path))
                    dur = _get_duration(str(audio_path))
                    if dur < 1:
                        dur = 3.0
                else:
                    dur = 3.0
                    _make_silent(dur, str(audio_path))
            except Exception as e:
                log(f"  ⚠️ TTS 失敗: {e}")
                dur = 3.0
                _make_silent(dur, str(audio_path))
            
            audio_paths.append(str(audio_path))
            durations.append(dur)
        
        log(f"✅ TTS 完成: {len(audio_paths)} 段音頻")
        update_progress(70)
        
        # ========== Phase 4: Animation (optional) ==========
        model_key = settings["model"]
        video_paths = [None] * len(image_paths)
        
        use_video = model_key != "ken-burns" and settings["animate_scope"] != "none"
        
        if use_video:
            log(f"🎬 Phase 4: 動畫生成 ({model_key})...")
            
            # Map shorts models
            FAL_MODEL_MAP = {
                "ken-burns": None,
                "ltx": "fal-ai/ltx-video/image-to-video",
                "minimax": "fal-ai/minimax/video-01-live/image-to-video",
                "kling": "fal-ai/kling-video/v1/standard/image-to-video",
                "seedance-lite": "fal-ai/seedance/v2/lite/image-to-video",
                "seedance-pro": "fal-ai/seedance/v2/pro/image-to-video",
            }
            
            fal_model_id = FAL_MODEL_MAP.get(model_key)
            
            if fal_model_id:
                for idx, scene in enumerate(scenes):
                    if idx >= len(image_urls):
                        break
                    
                    should_animate = (
                        settings["animate_scope"] == "all" or 
                        (settings["animate_scope"] == "ai" and scene.get("animate", False))
                    )
                    
                    if not should_animate:
                        continue
                    
                    pct = 70 + int(20 * (idx + 1) / len(scenes))
                    update_progress(pct)
                    
                    log(f"  🎞️ 場景 {idx+1}: {model_key} 動畫...")
                    
                    motion = scene.get("motion", "gentle ambient motion, subtle breathing, slight breeze")
                    strength = settings["motion_strength"]
                    lvl = "moderate movement" if strength == "中等" else "very subtle, mostly still, cinemagraph"
                    
                    try:
                        anim_args = {
                            "image_url": image_urls[idx],
                            "prompt": f"{motion}, {lvl}",
                        }
                        
                        if model_key == "kling":
                            anim_args["cfg_scale"] = 0.3
                            anim_args["duration"] = "5"
                        
                        anim_result = fal.run(fal_model_id, anim_args, with_logs=False)
                        video_url = (anim_result.get("video") or {}).get("url") or anim_result.get("video_url")
                        
                        if video_url:
                            vid_path = work_dir / f"scene_{idx+1:02d}_video.mp4"
                            fal.download(video_url, str(vid_path))
                            video_paths[idx] = str(vid_path)
                            log(f"  ✅ 場景 {idx+1} 動畫完成")
                    except Exception as e:
                        log(f"  ⚠️ 場景 {idx+1} 動畫失敗: {e}")
        
        log("✅ 動畫階段完成")
        update_progress(90)
        
        # ========== Phase 5: FFmpeg Assembly ==========
        log("✂️ Phase 5: FFmpeg 剪片合成...")
        
        if mode == "shorts":
            W, H, FPS = 1080, 1920, 30
        else:
            W, H, FPS = 1920, 1080, 30
        
        clips = []
        
        for idx in range(min(len(image_paths), len(audio_paths))):
            clip_path = work_dir / f"clip_{idx+1:04d}.mp4"
            dur = durations[idx] + 0.5 if idx < len(durations) else 3.5
            
            try:
                if video_paths[idx]:
                    # Video clip
                    _clip_from_video(video_paths[idx], audio_paths[idx], dur, str(clip_path), W, H, FPS)
                else:
                    # Ken Burns from image
                    _clip_from_image(image_paths[idx], audio_paths[idx], dur, str(clip_path), W, H, FPS)
                clips.append(str(clip_path))
            except Exception as e:
                log(f"  ⚠️ 場景 {idx+1} clip 失敗: {e}")
        
        if not clips:
            raise RuntimeError("冇任何 clip 成功")
        
        # Concat
        concat_list = work_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for cp in clips:
                f.write(f"file '{os.path.abspath(cp)}'\n")
        
        merged_path = work_dir / "merged.mp4"
        _run_ffmpeg([
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-c", "copy", str(merged_path)
        ])
        
        if not merged_path.exists():
            # Re-encode fallback
            _run_ffmpeg([
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-c:a", "aac", "-b:a", "128k", "-pix_fmt", "yuv420p",
                str(merged_path)
            ])
        
        final_path = work_dir / f"{job_id}_{'short' if mode == 'shorts' else 'film'}.mp4"
        merged_path.rename(final_path)
        
        output_url = f"/output/job_{job_id}/{final_path.name}"
        
        log(f"🎉 完成！影片: {output_url}")
        update_progress(100)
        
        job["status"] = "done"
        job["output"] = output_url
        job["scene_count"] = len(scenes)
        job["duration"] = sum(durations) if durations else 0
        _save_job(job)
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        log(f"❌ 錯誤: {e}")
        job["status"] = "error"
        job["error"] = error_msg
        _save_job(job)


# ============================================================
# FFmpeg Helpers
# ============================================================

import subprocess

def _run_ffmpeg(args):
    cmd = ["ffmpeg", "-y", "-loglevel", "error"] + args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {r.stderr[:500]}")
    return r

def _get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

def _make_silent(dur, dest):
    _run_ffmpeg([
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", f"{dur:.3f}", "-c:a", "aac", "-b:a", "128k", dest
    ])

def _clip_from_image(image_path, audio_path, duration, dest, W, H, FPS):
    frames = max(int(duration * FPS), 1)
    sw, sh = W * 2, H * 2
    vf = (f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
          f"crop={sw}:{sh},"
          f"zoompan=z='min(zoom+0.0008,1.15)':d={frames}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"s={W}x{H}:fps={FPS},setsar=1,format=yuv420p")
    _run_ffmpeg([
        "-loop", "1", "-i", image_path, "-i", audio_path,
        "-filter:v", vf, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-r", str(FPS), "-t", f"{duration:.3f}", "-pix_fmt", "yuv420p", dest
    ])

def _clip_from_video(video_path, audio_path, duration, dest, W, H, FPS):
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
          f"crop={W}:{H},setsar=1,fps={FPS},format=yuv420p")
    _run_ffmpeg([
        "-stream_loop", "-1", "-i", video_path, "-i", audio_path,
        "-filter:v", vf, "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-r", str(FPS), "-t", f"{duration:.3f}", "-pix_fmt", "yuv420p", dest
    ])

def _save_job(job):
    path = JOBS_DIR / f"{job['id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(job, f, ensure_ascii=False, indent=2)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("🎬 AI Film Studio Web")
    print(f"   http://localhost:8080")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8080, debug=False)
