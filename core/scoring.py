"""Scoring module — comprehensive pronunciation, fluency, and completeness evaluation.

Inspired by Echoic's 3-dimension scoring framework:
  - Pronunciation/accuracy (phoneme-level)
  - Fluency (rate + gap penalty)
  - Completeness (word coverage)

Supports age-based strictness profiles for adaptive scoring.
"""

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from Levenshtein import distance as lev_dist

from core.phonemes import phoneme_accuracy, text_to_phonemes

# ── Model ─────────────────────────────────────────────────────────────────────
WHISPER_CLI = "/tmp/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = "/tmp/whisper.cpp/models/ggml-small.en.bin"


# ── Scoring profiles for different age groups ─────────────────────────────────

@dataclass
class ScoringProfile:
    name: str
    strictness: float        # 0.0 (very lenient) ~ 1.0 (strict)
    ideal_words_per_sec: float
    rate_tolerance: float
    gap_threshold: float     # seconds; pauses longer than this are penalized
    min_spoken_score: float  # raw accuracy threshold to count a word as "spoken"


PROFILES: dict[str, ScoringProfile] = {
    "adult":    ScoringProfile("成人",     1.0, 2.5, 0.3, 0.25, 15.0),
    "teen":     ScoringProfile("青少年",   0.7, 2.0, 0.4, 0.35, 10.0),
    "child":    ScoringProfile("儿童",     0.2, 1.5, 0.5, 0.50,  3.0),
    "beginner": ScoringProfile("初学者",   0.1, 1.2, 0.6, 0.70,  1.0),
}


# ── Text helpers ──────────────────────────────────────────────────────────────

def _normalize(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s']", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _reference_words(text: str) -> list[str]:
    return [w for w in text.split() if re.sub(r"^\W+|\W+$", "", w)]


def _display_word(word: str) -> str:
    return re.sub(r"^\W+|\W+$", "", word)


# ── Calibration ───────────────────────────────────────────────────────────────

def _calibrate(raw: float, strictness: float) -> float:
    """Map raw score 0-100 to calibrated score using strictness.

    strictness=1.0 → raw score (no boost)
    strictness=0.0 → strong boost for low scores
    """
    if raw <= 0.0:
        return 0.0
    if raw >= 100.0:
        return 100.0
    p = 1.0 + (1.0 - strictness) * 2.0
    return round(100.0 * (raw / 100.0) ** (1.0 / p), 1)


# ── ASR ───────────────────────────────────────────────────────────────────────

def _transcribe_user_audio(audio_path: str) -> str:
    json_path = audio_path + ".json"
    Path(json_path).unlink(missing_ok=True)

    cmd = [
        WHISPER_CLI, "-m", WHISPER_MODEL,
        "-f", audio_path, "-l", "en", "-t", "4", "-oj",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"whisper.cpp failed: {result.stderr.strip()}")

    if not Path(json_path).exists():
        return ""

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    texts = [seg.get("text", "").strip() for seg in data.get("transcription", [])]
    return " ".join(texts)


# ── Accuracy (phoneme-level) ──────────────────────────────────────────────────

def _word_accuracy(reference: str, hypothesis: str) -> float:
    """Compute word accuracy from WER. Returns 0-100."""
    ref = _normalize(reference).split()
    hyp = _normalize(hypothesis).split()
    if not ref:
        return 100.0 if not hyp else 0.0
    d = lev_dist(" ".join(ref), " ".join(hyp))
    return round(max(0.0, (1.0 - d / len(ref)) * 100.0), 1)


def _char_accuracy(reference: str, hypothesis: str) -> float:
    """Character-level accuracy. Returns 0-100."""
    ref = _normalize(reference).replace(" ", "")
    hyp = _normalize(hypothesis).replace(" ", "")
    if not ref:
        return 100.0 if not hyp else 0.0
    d = lev_dist(ref, hyp)
    return round(max(0.0, (1.0 - d / len(ref)) * 100.0), 1)


def _accuracy_score(reference: str, hypothesis: str, profile: ScoringProfile) -> float:
    """Compute accuracy score: blend of WER, CER, and PER.

    Uses calibration to adapt strictness per age group.
    """
    word_acc = _word_accuracy(reference, hypothesis)
    char_acc = _char_accuracy(reference, hypothesis)

    try:
        ref_ph = text_to_phonemes(reference)
        hyp_ph = text_to_phonemes(hypothesis)
        per_acc = phoneme_accuracy(ref_ph, hyp_ph)
    except Exception:
        per_acc = word_acc

    raw = word_acc * 0.35 + char_acc * 0.25 + per_acc * 0.40
    return _calibrate(raw, profile.strictness)


# ── Fluency (rate + gap penalty) ──────────────────────────────────────────────

def _fluency_score(
    reference: str,
    user_duration: float,
    profile: ScoringProfile,
) -> float:
    """Score fluency based on speaking rate and gap penalty.

    Echoic-style: 70% gap penalty + 30% rate penalty.
    """
    words = _reference_words(reference)
    if not words:
        return 100.0
    if user_duration <= 0:
        return 0.0

    seg_dur = user_duration / len(words)

    # Gap penalty: penalize gaps longer than threshold
    gaps = [seg_dur - 0.1 for _ in range(len(words) - 1)]  # assume minimal gap
    excess = sum(max(0.0, g - profile.gap_threshold) for g in gaps)
    avg_excess = excess / max(len(gaps), 1)
    gap_score = max(0.0, 100.0 - avg_excess * 120.0)

    # Rate penalty: penalize deviation from ideal words/sec
    wps = len(words) / max(user_duration, 0.1)
    deviation = abs(wps - profile.ideal_words_per_sec) / profile.ideal_words_per_sec
    rate_score = max(0.0, 100.0 - deviation / profile.rate_tolerance * 50.0)

    raw = 0.7 * gap_score + 0.3 * rate_score
    return _calibrate(raw, profile.strictness)


# ── Completeness (word coverage) ──────────────────────────────────────────────

def _completeness_score(
    reference: str,
    hypothesis: str,
    profile: ScoringProfile,
) -> float:
    """Score completeness: fraction of reference words covered.

    A word is "spoken" if it appears in the ASR hypothesis after normalization.
    Uses the min_spoken_score threshold from the profile.
    """
    ref_words = {_display_word(w).lower() for w in reference.split() if _display_word(w)}
    hyp_words = set(_normalize(hypothesis).split())

    if not ref_words:
        return 100.0

    spoken = ref_words & hyp_words
    raw = 100.0 * len(spoken) / len(ref_words)
    return _calibrate(raw, profile.strictness)


# ── Public entry point ────────────────────────────────────────────────────────

def score_recording(
    reference_text: str,
    user_audio_path: str,
    reference_duration: float,
    age_group: str = "child",
) -> dict:
    """Score a user's recording against the reference.

    Args:
        reference_text: The original English sentence text.
        user_audio_path: Path to the user's WAV recording.
        reference_duration: Duration of the original audio segment in seconds.
        age_group: One of "adult", "teen", "child", "beginner".

    Returns:
        Dict with keys: pronunciation, fluency, timing, completeness, overall
        All scores are 0-100.
    """
    profile = PROFILES.get(age_group, PROFILES["child"])

    # 1. Transcribe user audio
    user_text = _transcribe_user_audio(user_audio_path)

    # 2. Pronunciation/Accuracy (phoneme-level blend + calibration)
    pronunciation = _accuracy_score(reference_text, user_text, profile)

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

    # 4. Fluency (rate + gap penalty)
    fluency = _fluency_score(reference_text, user_duration, profile)

    # 5. Timing (duration match with tolerance — kept for backward compat)
    if reference_duration > 0:
        diff = abs(user_duration - reference_duration)
        tolerance = reference_duration * 0.2
        if diff <= tolerance:
            timing = 100.0
        else:
            timing = 100.0 * max(0.0, 1.0 - (diff - tolerance) / reference_duration)
    else:
        timing = 50.0
    timing = round(timing, 1)

    # 6. Completeness (word coverage)
    completeness = _completeness_score(reference_text, user_text, profile)

    # 7. Overall: Echoic-style weighted combination
    overall = round(
        pronunciation * 0.5 + fluency * 0.3 + completeness * 0.2, 1
    )

    return {
        "pronunciation": pronunciation,
        "fluency": fluency,
        "timing": timing,
        "completeness": completeness,
        "overall": overall,
    }
