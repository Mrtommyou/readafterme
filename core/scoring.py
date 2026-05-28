"""Scoring module — comprehensive pronunciation, fluency, and timing evaluation."""

import json
import math
import subprocess
from pathlib import Path

from Levenshtein import distance as lev_dist


def _transcribe_user_audio(audio_path: str) -> str:
    """Transcribe user recording using whisper.cpp for WER comparison.

    Returns the transcribed text string.
    """
    whisper_cli = "/tmp/whisper.cpp/build/bin/whisper-cli"
    model = "/tmp/whisper.cpp/models/ggml-tiny.en.bin"

    json_path = audio_path + ".json"
    Path(json_path).unlink(missing_ok=True)

    cmd = [
        whisper_cli, "-m", model,
        "-f", audio_path, "-l", "en", "-t", "4", "-oj",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"whisper.cpp failed: {result.stderr.strip()}")

    if not Path(json_path).exists():
        return ""

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    texts = []
    for seg in data.get("transcription", []):
        texts.append(seg.get("text", "").strip())

    return " ".join(texts)


def _normalize(s: str) -> str:
    """Normalize text for comparison."""
    import re
    s = s.lower().strip()
    s = re.sub(r"[^\w\s']", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _word_accuracy(reference: str, hypothesis: str) -> float:
    """Compute word accuracy from WER. Returns 0-100 score."""
    ref_words = _normalize(reference).split()
    hyp_words = _normalize(hypothesis).split()

    if not ref_words:
        return 100.0 if not hyp_words else 0.0

    d = lev_dist(" ".join(ref_words), " ".join(hyp_words))
    wer = d / len(ref_words)
    accuracy = max(0.0, (1.0 - wer) * 100.0)
    return round(accuracy, 1)


def _fluency_score(reference_duration: float, user_duration: float) -> float:
    """Score fluency based on speaking rate similarity.

    If user takes similar time to reference, fluency is high.
    Too fast or too slow both reduce score.
    """
    if reference_duration <= 0:
        return 50.0

    ratio = user_duration / reference_duration
    # Ideal ratio = 1.0 (same duration)
    # Penalize exponentially as ratio deviates
    if ratio <= 0:
        return 0.0

    score = 100.0 * math.exp(-((math.log(ratio) ** 2) / (2 * 0.3**2)))
    return round(min(100.0, score), 1)


def _timing_score(reference_duration: float, user_duration: float) -> float:
    """Score timing match between reference and user recording.

    Uses absolute duration difference with a tolerance.
    """
    if reference_duration <= 0:
        return 50.0

    diff = abs(user_duration - reference_duration)
    # Within 20% tolerance = full marks, then decays
    tolerance = reference_duration * 0.2
    if diff <= tolerance:
        return 100.0

    score = 100.0 * max(0.0, 1.0 - (diff - tolerance) / reference_duration)
    return round(score, 1)


def score_recording(
    reference_text: str,
    user_audio_path: str,
    reference_duration: float,
) -> dict:
    """Score a user's recording against the reference.

    Args:
        reference_text: The original English sentence text.
        user_audio_path: Path to the user's WAV recording.
        reference_duration: Duration of the original audio segment in seconds.

    Returns:
        Dict with keys: pronunciation, fluency, timing, overall
        All scores are 0-100.
    """
    # 1. Transcribe user audio
    user_text = _transcribe_user_audio(user_audio_path)

    # 2. Pronunciation score (based on WER)
    pronunciation = _word_accuracy(reference_text, user_text)

    # 3. Get user audio duration
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0", user_audio_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        user_duration = float(result.stdout.strip())
    except Exception:
        user_duration = reference_duration

    # 4. Fluency score
    fluency = _fluency_score(reference_duration, user_duration)

    # 5. Timing score
    timing = _timing_score(reference_duration, user_duration)

    # 6. Overall: weighted combination
    overall = round(
        pronunciation * 0.5 + fluency * 0.25 + timing * 0.25, 1
    )

    return {
        "pronunciation": pronunciation,
        "fluency": fluency,
        "timing": timing,
        "overall": overall,
    }
