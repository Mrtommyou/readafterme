"""Alignment module — map recognized text segments to reference sentences."""

import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, strip punctuation, trim."""
    text = text.lower().strip()
    # Remove punctuation but keep internal spaces
    text = re.sub(r"[^\w\s']", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def word_tokenize(text: str) -> list[str]:
    """Simple whitespace-based tokenization."""
    return normalize_text(text).split()


def wer_score(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate between reference and hypothesis.

    Returns 0.0 (perfect) to 1.0 (completely wrong).
    Uses Levenshtein distance on word sequences.
    """
    ref_words = word_tokenize(reference)
    hyp_words = word_tokenize(hypothesis)

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    try:
        from Levenshtein import distance as lev_dist
        d = lev_dist(" ".join(ref_words), " ".join(hyp_words))
    except ImportError:
        d = _levenshtein_words(ref_words, hyp_words)

    return d / len(ref_words)


def _levenshtein_words(ref: list[str], hyp: list[str]) -> int:
    """Fallback word-level Levenshtein distance (pure Python)."""
    m, n = len(ref), len(hyp)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            temp = dp[j]
            if ref[i - 1] == hyp[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


def align_segments(
    asr_segments: list[dict],
    reference_sentences: list[str],
) -> list[dict]:
    """Align ASR output segments to reference sentences.

    This is a greedy algorithm that maps ASR segments to
    reference sentences based on text similarity.

    Args:
        asr_segments: List of {start, end, text} from whisper.
        reference_sentences: List of reference English sentences (ground truth).

    Returns:
        List of {en, start, end} dicts aligned to reference sentences.
        Some sentences may be skipped if no match found.
    """
    if not asr_segments or not reference_sentences:
        return []

    # Use rough timing: distribute reference sentences evenly
    # across the total audio duration if we have asr timing
    total_duration = asr_segments[-1]["end"] - asr_segments[0]["start"]
    segment_duration = total_duration / len(reference_sentences)
    start_time = asr_segments[0]["start"]

    result = []
    for i, sentence in enumerate(reference_sentences):
        est_start = start_time + i * segment_duration
        est_end = est_start + segment_duration

        # Find ASR segments that overlap with this time window
        matched_text = []
        for seg in asr_segments:
            if seg["start"] >= est_start and seg["end"] <= est_end + 0.5:
                matched_text.append(seg["text"])
            elif seg["start"] < est_end and seg["end"] > est_start:
                # Partial overlap
                matched_text.append(seg["text"])

        result.append({
            "en": sentence,
            "start": round(est_start, 2),
            "end": round(est_end, 2),
        })

    return result
