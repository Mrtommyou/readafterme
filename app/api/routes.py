"""REST API routes for ReadAfterMe."""

import json
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas import HistoryItem, ScoreResult, Sentence, VideoInfo
from core.asr import transcribe
from core.audio import extract_audio, get_audio_duration
from core.scoring import score_recording as score_user_recording
from core.translate import translate_batch

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}

# ── File paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"
SCORES_DIR = DATA_DIR / "scores"
DB_FILE = DATA_DIR / "videos.json"


def _load_db() -> dict:
    """Load video metadata database."""
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"videos": []}


def _save_db(db: dict):
    """Save video metadata database."""
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2))


# ── Background processing ────────────────────────────────────────────────────

processing_tasks: dict[str, dict] = {}


async def _process_video_background(video_id: str, filename: str, video_path: Path):
    """Run transcoding, ASR, translation in background. Updates DB when done."""
    audio_path = AUDIO_DIR / f"{video_id}.wav"
    import asyncio

    try:
        # Step 1: Extract audio from original file (before transcode — clean audio)
        processing_tasks[video_id]["step"] = "提取音频中..."
        await asyncio.to_thread(extract_audio, str(video_path), str(audio_path))
        duration = await asyncio.to_thread(get_audio_duration, str(audio_path))

        # Step 2: Transcode to H.264 for browser playback
        processing_tasks[video_id]["step"] = "转码中..."
        transcode_path = video_path.with_suffix(".h264.mp4")
        try:
            import subprocess as sp
            await asyncio.to_thread(
                sp.run,
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "128k",
                 "-movflags", "+faststart",
                 str(transcode_path)],
                capture_output=True, timeout=300,
            )
            video_path.unlink()
            transcode_path.rename(video_path)
        except Exception:
            transcode_path.unlink(missing_ok=True)

        # Step 3: Run ASR
        processing_tasks[video_id]["step"] = "语音识别中..."
        segments = await asyncio.to_thread(transcribe, str(audio_path), language="en")
        if not segments:
            segments = [{"start": 0.0, "end": duration, "text": ""}]

        # Step 4: Translate
        processing_tasks[video_id]["step"] = "翻译中..."
        texts = [seg["text"] for seg in segments if seg["text"].strip()]
        if texts:
            try:
                translations = await translate_batch(texts)
            except Exception:
                translations = texts
        else:
            translations = []

        # Build sentence list, skip music segments
        sentences = []
        for i, seg in enumerate(segments):
            text = seg["text"].strip()
            if not text or "[Music]" in text or "[music]" in text:
                continue
            zh = translations[i] if i < len(translations) else ""
            s = Sentence(en=text, zh=zh, start=seg["start"], end=seg["end"])
            sentences.append(s.model_dump())

        mins = int(duration // 60)
        secs = int(duration % 60)

        db = _load_db()
        for v in db["videos"]:
            if v["id"] == video_id:
                v["duration"] = f"{mins}:{secs:02d}"
                v["duration_sec"] = duration
                v["status"] = "已处理"
                v["sentences"] = sentences
                break
        _save_db(db)

        processing_tasks[video_id]["step"] = "完成"
        processing_tasks[video_id]["done"] = True

    except Exception as e:
        processing_tasks[video_id]["step"] = f"失败: {e}"
        processing_tasks[video_id]["error"] = str(e)

        db = _load_db()
        db["videos"] = [v for v in db["videos"] if v["id"] != video_id]
        _save_db(db)


# ── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video — returns immediately, processes in background."""
    if not file.filename or not any(
        file.filename.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    ):
        raise HTTPException(400, "Unsupported file format. Supported: mp4, avi, mov, mkv, webm")

    video_id = str(uuid.uuid4())[:8]
    video_path = UPLOAD_DIR / f"{video_id}_{file.filename}"
    content = await file.read()
    video_path.write_bytes(content)

    # Create DB entry with processing status
    db = _load_db()
    db["videos"].append({
        "id": video_id,
        "name": file.filename,
        "duration": "",
        "duration_sec": 0,
        "status": "处理中",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sentences": [],
    })
    _save_db(db)

    # Track processing progress
    processing_tasks[video_id] = {"step": "队列中...", "done": False, "error": None}

    # Launch background processing
    import asyncio
    asyncio.create_task(_process_video_background(video_id, file.filename, video_path))

    return {"video_id": video_id, "status": "处理中"}


@router.get("/videos/{video_id}/status")
async def get_video_status(video_id: str):
    """Get processing status for a video."""
    info = processing_tasks.get(video_id)
    if info:
        return {
            "video_id": video_id,
            "status": "处理中",
            "step": info["step"],
            "done": info["done"],
            "error": info.get("error"),
        }
    # Check if already processed
    db = _load_db()
    for v in db["videos"]:
        if v["id"] == video_id:
            return {"video_id": video_id, "status": v["status"], "step": "完成", "done": True}
    raise HTTPException(404, "Video not found")


# ── List Videos ──────────────────────────────────────────────────────────────

@router.get("/videos")
async def list_videos():
    """List all uploaded and processed videos."""
    db = _load_db()
    videos = []
    for v in db["videos"]:
        videos.append(VideoInfo(
            id=v["id"],
            name=v["name"],
            duration=v.get("duration", "0:00"),
            status=v["status"],
        ))
    return {"videos": videos}


# ── Get Sentences ────────────────────────────────────────────────────────────

@router.get("/videos/{video_id}/file")
async def get_video_file(video_id: str):
    """Serve the uploaded video file."""
    db = _load_db()
    for v in db["videos"]:
        if v["id"] == video_id:
            video_path = UPLOAD_DIR / f'{video_id}_{v["name"]}'
            if video_path.exists():
                return FileResponse(str(video_path), media_type="video/mp4")
            raise HTTPException(404, "Video file not found")
    raise HTTPException(404, "Video not found")


@router.get("/videos/{video_id}/sentences")
async def get_sentences(video_id: str):
    """Get processed sentences for a video."""
    db = _load_db()
    for v in db["videos"]:
        if v["id"] == video_id:
            sentences = [Sentence(**s) for s in v.get("sentences", [])]
            return {
                "video_id": video_id,
                "video_name": v["name"],
                "sentences": sentences,
            }
    raise HTTPException(404, "Video not found")


# ── Score Recording ─────────────────────────────────────────────────────────

@router.post("/score")
async def score_recording(
    video_id: str = Form(...),
    sentence_index: int = Form(...),
    age_group: str = Form("child"),
    file: UploadFile = File(...),
):
    """Score a user recording against a reference sentence.

    1. Save user recording
    2. Transcribe user audio with small.en model
    3. Evaluate on 3 dimensions: pronunciation, fluency, completeness
    4. Return calibrated scores based on age_group strictness
    """
    db = _load_db()
    video = None
    for v in db["videos"]:
        if v["id"] == video_id:
            video = v
            break

    if not video:
        raise HTTPException(404, "Video not found")

    sentences = video.get("sentences", [])
    if sentence_index < 0 or sentence_index >= len(sentences):
        raise HTTPException(400, "Invalid sentence index")

    ref = sentences[sentence_index]
    ref_text = ref["en"]
    ref_duration = ref["end"] - ref["start"]

    # Save raw user recording (webm from browser MediaRecorder)
    user_audio_dir = AUDIO_DIR / f"user_{video_id}"
    user_audio_dir.mkdir(parents=True, exist_ok=True)
    raw_path = user_audio_dir / f"sentence_{sentence_index:04d}.webm"
    wav_path = user_audio_dir / f"sentence_{sentence_index:04d}.wav"

    content = await file.read()
    raw_path.write_bytes(content)

    # Convert to 16kHz mono WAV for whisper.cpp
    try:
        from core.audio import extract_audio
        extract_audio(str(raw_path), str(wav_path))
    except Exception as e:
        raw_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Audio conversion failed: {e}")

    # Score with age-appropriate profile
    scores = score_user_recording(ref_text, str(wav_path), ref_duration, age_group)

    return ScoreResult(**scores)


# ── Save / Load Recordings ───────────────────────────────────────────────────

@router.post("/recordings")
async def save_recording(
    video_id: str = Form(...),
    sentence_index: int = Form(...),
    file: UploadFile = File(...),
):
    """Save a user recording for a specific sentence (without scoring)."""
    user_audio_dir = AUDIO_DIR / f"user_{video_id}"
    user_audio_dir.mkdir(parents=True, exist_ok=True)
    recording_path = user_audio_dir / f"sentence_{sentence_index:04d}.webm"
    content = await file.read()
    recording_path.write_bytes(content)
    return {"url": f"/api/recordings/{video_id}/{sentence_index}/file"}


@router.get("/recordings/{video_id}/{sentence_index}/file")
async def get_recording(video_id: str, sentence_index: int):
    """Serve a saved user recording."""
    recording_path = AUDIO_DIR / f"user_{video_id}" / f"sentence_{sentence_index:04d}.webm"
    if not recording_path.exists():
        raise HTTPException(404, "Recording not found")
    return FileResponse(str(recording_path), media_type="audio/webm")


# ── Save / Load Scores ───────────────────────────────────────────────────────

@router.post("/recordings/score")
async def save_score(data: dict):
    """Save a score result for a specific sentence."""
    video_id = data.get("video_id")
    sentence_idx = data.get("sentence_index")
    score = data.get("score")
    if not video_id or sentence_idx is None or not score:
        raise HTTPException(400, "Missing required fields")

    SCORES_DIR.mkdir(parents=True, exist_ok=True)
    scores_file = SCORES_DIR / f"{video_id}.json"
    scores = json.loads(scores_file.read_text()) if scores_file.exists() else {}
    scores[str(sentence_idx)] = score
    scores_file.write_text(json.dumps(scores, ensure_ascii=False))
    return {"ok": True}


@router.get("/recordings/{video_id}/scores")
async def get_scores(video_id: str):
    """Get all saved scores for a video."""
    scores_file = SCORES_DIR / f"{video_id}.json"
    if scores_file.exists():
        return json.loads(scores_file.read_text())
    return {}


# ── History ──────────────────────────────────────────────────────────────────

@router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and all associated data."""
    db = _load_db()
    video = None
    for v in db["videos"]:
        if v["id"] == video_id:
            video = v
            break

    if not video:
        raise HTTPException(404, "Video not found")

    # Remove video file
    video_path = UPLOAD_DIR / f'{video_id}_{video["name"]}'
    video_path.unlink(missing_ok=True)

    # Remove audio file
    audio_path = AUDIO_DIR / f"{video_id}.wav"
    audio_path.unlink(missing_ok=True)

    # Remove scores
    scores_file = SCORES_DIR / f"{video_id}.json"
    scores_file.unlink(missing_ok=True)

    # Remove user recordings
    user_audio_dir = AUDIO_DIR / f"user_{video_id}"
    if user_audio_dir.exists():
        import shutil
        shutil.rmtree(str(user_audio_dir))

    # Remove from DB
    db["videos"] = [v for v in db["videos"] if v["id"] != video_id]
    _save_db(db)

    # Cancel any pending processing
    processing_tasks.pop(video_id, None)

    return {"ok": True}


@router.get("/history")
async def get_history():
    """Get practice history for all videos with real scores."""
    db = _load_db()
    history = []
    for v in db["videos"]:
        sentences = v.get("sentences", [])
        total = len(sentences)

        # Load real scores from saved score file
        scores_file = SCORES_DIR / f"{v['id']}.json"
        practiced = 0
        avg_score = 0.0
        if scores_file.exists():
            scores = json.loads(scores_file.read_text())
            practiced = len(scores)
            overalls = [s.get("overall", 0) for s in scores.values() if isinstance(s, dict)]
            avg_score = round(sum(overalls) / len(overalls), 1) if overalls else 0.0

        history.append(HistoryItem(
            date=v.get("created_at", "").split(" ")[0],
            video=v["name"],
            video_id=v["id"],
            sentences=total,
            practiced=practiced,
            avg_score=avg_score,
        ))
    return {"history": history}
