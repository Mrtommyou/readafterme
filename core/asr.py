"""ASR module — whisper.cpp wrapper via subprocess.

Uses a pre-compiled whisper.cpp binary for transcription.
Designed for CPU-only, works on musl/Alpine.
"""

import json
import subprocess
from pathlib import Path

# Path to whisper.cpp binary and model (persistent storage)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
WHISPER_CLI = _DATA_DIR / "bin/whisper-cli"
WHISPER_MODEL = _DATA_DIR / "models/ggml-tiny.en.bin"

# Ensure these exist
if not WHISPER_CLI.exists():
    raise RuntimeError(f"whisper-cli not found at {WHISPER_CLI}")
if not WHISPER_MODEL.exists():
    raise RuntimeError(f"whisper model not found at {WHISPER_MODEL}")


def transcribe(
    audio_path: str,
    *,
    language: str = "en",
    threads: int = 4,
    print_progress: bool = False,
    max_len: int = 60,
    split_on_word: bool = True,
) -> list[dict]:
    """Transcribe audio file using whisper.cpp.

    Args:
        audio_path: Path to 16kHz mono WAV file.
        language: Language code (default: "en").
        threads: CPU threads for inference.
        print_progress: Whether to print progress lines.
        max_len: Maximum segment length in characters.
        split_on_word: Split segments on word boundaries.

    Returns:
        List of dicts: [{start, end, text}, ...] with times in seconds.
    """
    # whisper.cpp -oj writes JSON to a sidecar file: {audio_path}.json
    json_path = audio_path + ".json"

    cmd = [
        str(WHISPER_CLI),
        "-m", str(WHISPER_MODEL),
        "-f", audio_path,
        "-l", language,
        "-t", str(threads),
        "-ml", str(max_len),
        "-oj",                          # output JSON to sidecar file
    ]
    if split_on_word:
        cmd.append("-sow")

    # Remove stale sidecar before running
    Path(json_path).unlink(missing_ok=True)

    # Run whisper.cpp
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"whisper.cpp failed: {result.stderr.strip()}")

    # Read JSON from sidecar file (whisper.cpp -oj writes to {input}.json)
    if not Path(json_path).exists():
        raise RuntimeError(f"whisper.cpp did not produce output at {json_path}")

    data = json.loads(Path(json_path).read_text(encoding="utf-8"))

    segments = []
    for seg in data.get("transcription", []):
        offsets = seg.get("offsets", {})
        start_ms = offsets.get("from", 0)
        end_ms = offsets.get("to", 0)
        segments.append({
            "start": start_ms / 1000.0,          # ms → seconds
            "end": end_ms / 1000.0,
            "text": seg.get("text", "").strip(),
        })

    return segments


def transcribe_segments(
    audio_paths: list[str],
    *,
    language: str = "en",
    threads: int = 4,
) -> list[list[dict]]:
    """Transcribe multiple audio files (one per sentence segment).

    Each file gets its own whisper run. This is slower but gives
    better timing per sentence.

    Args:
        audio_paths: List of WAV file paths (one per sentence).
        language: Language code.

    Returns:
        List of transcription results, one per input file.
    """
    results = []
    for path in audio_paths:
        segs = transcribe(path, language=language, threads=threads)
        results.append(segs)
    return results
