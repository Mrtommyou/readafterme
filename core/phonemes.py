"""Phoneme conversion for pronunciation scoring via espeak-ng."""

import os
import re
import subprocess
from pathlib import Path

# Persistent espeak-ng installation
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_ESPEAK_BIN = _DATA_DIR / "bin/espeak-ng"
_ESPEAK_LIB = _DATA_DIR / "lib"
_ESPEAK_DATA = _DATA_DIR / "espeak-ng-data"

_ENV = os.environ.copy()
_ENV["ESPEAK_DATA_PATH"] = str(_ESPEAK_DATA)
_ENV["LD_LIBRARY_PATH"] = str(_ESPEAK_LIB)


def text_to_phonemes(text: str) -> str:
    """Convert English text to IPA phoneme string using espeak-ng.

    Args:
        text: English text to convert.

    Returns:
        Space-separated phoneme string, e.g. "h əl ˈə ʊ w ˈɜː l d".
    """
    result = subprocess.run(
        [str(_ESPEAK_BIN), "-q", "--ipa=3", "-x", text],
        capture_output=True, text=True,
        timeout=30, env=_ENV,
    )
    raw = result.stdout.strip()
    phonemes = re.sub(r"\s+", " ", raw).strip()
    return phonemes


def phoneme_error_rate(ref_phonemes: str, hyp_phonemes: str) -> float:
    """Compute Phoneme Error Rate between reference and hypothesis.

    Returns 0.0 (perfect) to 1.0 (completely wrong).
    """
    from Levenshtein import distance as lev_dist

    ref = ref_phonemes.split()
    hyp = hyp_phonemes.split()

    if not ref:
        return 0.0 if not hyp else 1.0

    d = lev_dist(" ".join(ref), " ".join(hyp))
    return d / len(ref)


def phoneme_accuracy(ref_phonemes: str, hyp_phonemes: str) -> float:
    """Convert PER to accuracy score 0-100."""
    per = phoneme_error_rate(ref_phonemes, hyp_phonemes)
    return round(max(0.0, (1.0 - per) * 100.0), 1)
