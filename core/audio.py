"""Audio extraction module — video to 16kHz mono WAV via ffmpeg."""

import subprocess
import os
from pathlib import Path


def extract_audio(video_path: str, output_path: str) -> str:
    """Extract audio from video file as 16kHz mono WAV.

    Args:
        video_path: Path to input video file.
        output_path: Path for output WAV file (must end in .wav).

    Returns:
        Path to the extracted WAV file.

    Raises:
        FileNotFoundError: If video_path doesn't exist or ffmpeg is not found.
        RuntimeError: If ffmpeg extraction fails.
    """
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # ffmpeg: extract audio, 16kHz sample rate, mono channel, 16-bit PCM WAV
    cmd = [
        "ffmpeg",
        "-y",                     # overwrite output
        "-i", str(video),        # input file
        "-vn",                    # no video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",          # 16kHz sample rate
        "-ac", "1",              # mono
        "-f", "wav",             # WAV format
        str(output),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.strip()}")

    return str(output)


def get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        audio_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
    return float(result.stdout.strip())


def slice_audio(audio_path: str, output_dir: str, segments: list[dict]) -> list[str]:
    """Slice audio into segments by start/end times.

    Args:
        audio_path: Path to full WAV file.
        output_dir: Directory for slice output files.
        segments: List of {start: float, end: float} dicts.

    Returns:
        List of paths to sliced WAV files.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, seg in enumerate(segments):
        start = seg["start"]
        end = seg["end"]
        duration = end - start
        out_path = out_dir / f"seg_{i:04d}.wav"

        cmd = [
            "ffmpeg",
            "-y",
            "-i", audio_path,
            "-ss", str(start),
            "-t", str(duration),
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            "-f", "wav",
            str(out_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        paths.append(str(out_path))

    return paths
