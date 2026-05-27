"""REST API routes for ReadAfterMe."""

import json
import uuid
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse

from app.schemas import Sentence, VideoInfo, ProcessResult, ScoreResult, HistoryItem
from core.audio import extract_audio, get_audio_duration
from core.asr import transcribe
from core.translate import translate_batch
from core.scoring import score_recording as score_user_recording

router = APIRouter()

# ── File paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"
DB_FILE = DATA_DIR / "videos.json"


def _load_db() -> dict:
    """Load video metadata database."""
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"videos": []}


def _save_db(db: dict):
    """Save video metadata database."""
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2))


# ── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for processing.

    Steps:
    1. Save uploaded file
    2. Extract audio (16kHz mono WAV)
    3. Run ASR to get sentence segments
    4. Translate each segment to Chinese
    5. Save metadata
    """
    # Validate file type
    if not file.filename or not any(
        file.filename.lower().endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]
    ):
        raise HTTPException(400, "Unsupported file format. Supported: mp4, avi, mov, mkv, webm")

    # Generate unique ID
    video_id = str(uuid.uuid4())[:8]

    # Save uploaded file (original may be HEVC — will transcode below)
    video_path = UPLOAD_DIR / f"{video_id}_{file.filename}"
    content = await file.read()
    video_path.write_bytes(content)

    # Transcode to H.264 for browser compatibility
    transcode_path = video_path.with_suffix(".h264.mp4")
    try:
        import subprocess as sp
        sp.run(
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

    # Extract audio
    audio_path = AUDIO_DIR / f"{video_id}.wav"
    try:
        extract_audio(str(video_path), str(audio_path))
    except Exception as e:
        video_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Audio extraction failed: {e}")

    # Get duration
    try:
        duration = get_audio_duration(str(audio_path))
    except Exception:
        duration = 0.0

    # Run ASR
    try:
        segments = transcribe(str(audio_path), language="en")
    except Exception as e:
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)
        raise HTTPException(500, f"ASR failed: {e}")

    if not segments:
        # Fallback: return a single segment
        segments = [{"start": 0.0, "end": duration, "text": ""}]

    # Translate segments
    texts = [seg["text"] for seg in segments if seg["text"].strip()]
    if texts:
        try:
            translations = await translate_batch(texts)
        except Exception:
            translations = texts  # Fallback to original text
    else:
        translations = []

    # Build sentence list
    sentences = []
    for i, seg in enumerate(segments):
        zh = translations[i] if i < len(translations) else ""
        sentences.append(
            Sentence(
                en=seg["text"],
                zh=zh,
                start=seg["start"],
                end=seg["end"],
            )
        )

    # Format duration string
    mins = int(duration // 60)
    secs = int(duration % 60)
    dur_str = f"{mins}:{secs:02d}"

    # Save metadata
    db = _load_db()
    db["videos"].append({
        "id": video_id,
        "name": file.filename,
        "duration": dur_str,
        "duration_sec": duration,
        "status": "已处理",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sentences": [s.model_dump() for s in sentences],
    })
    _save_db(db)

    return ProcessResult(video_id=video_id, sentences=sentences)


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
    file: UploadFile = File(...),
):
    """Score a user recording against a reference sentence.

    1. Save user recording
    2. Transcribe user audio
    3. Compare with reference (WER + timing)
    4. Return scores
    """
    # Get reference sentence
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
    finally:
        raw_path.unlink(missing_ok=True)

    # Score: let scoring module handle transcription + timing
    scores = score_user_recording(ref_text, str(wav_path), ref_duration)

    return ScoreResult(**scores)


# ── History ──────────────────────────────────────────────────────────────────

@router.get("/history")
async def get_history():
    """Get practice history for all videos."""
    db = _load_db()
    history = []
    for v in db["videos"]:
        sentences = v.get("sentences", [])
        history.append(HistoryItem(
            date=v.get("created_at", "").split(" ")[0],
            video=v["name"],
            sentences=len(sentences),
            score=85.0,  # Placeholder — real scoring data would come from practice sessions
        ))
    return {"history": history}
