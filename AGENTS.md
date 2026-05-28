# ReadAfterMe — English shadowing practice app

## Architecture

- **Backend**: Python 3.12 + FastAPI (`app/`) with REST API routes in `app/api/routes.py`. Run via `uv run python run.py`.
- **Frontend**: Kivy app (`kivy_app/`) — Buildozer for Android APK
- **Core logic** in `core/`: ASR (whisper.cpp), audio (ffmpeg), alignment, translation, scoring.

## Critical external dependencies

- **whisper.cpp**: binary at `/tmp/whisper.cpp/build/bin/whisper-cli`, model at `/tmp/whisper.cpp/models/ggml-tiny.en.bin`. Hardcoded in `core/asr.py` and `core/scoring.py`. Must be present at runtime.
- **ffmpeg** / **ffprobe**: used for audio extraction + duration. Must be on `PATH`.
- **uv**: package manager. `uv.lock` and `pyproject.toml` at repo root. Mirror at `https://mirrors.aliyun.com/pypi/simple/`.
- **Levenshtein** C extension: used in `core/align.py` and `core/scoring.py` for WER calculation.

## Commands

- `uv run python run.py` — start backend dev server on port 9004 (default; override via `PORT` env var). Hot reload via uvicorn `reload=True`.
- `uv run ruff check kivy_app/` — lint Kivy app code
- `cd kivy_app && buildozer android debug` — build Android APK

## Quirks

- Translation has a multi-backend fallback chain: googletrans → MyMemory API → empty strings.
- ASR output JSON sidecar file pattern: `{audio_path}.json`.
- `data/` is gitignored; `data/videos.json` is the metadata DB (created at runtime).
- `pyproject.toml` has `required-environments` restricting to `linux x86_64`.
- Kivy app API server URL set via env var `API_URL` (default `http://localhost:9004`). On Android emulator use `http://10.0.2.2:9004`.
- `kivy_app/buildozer.spec` has Android build config. APK builds via CI on push to `main`.
- Audio recording: Android uses `android.media.MediaRecorder` via pyjnius; desktop uses `sounddevice`.
- `.python-version` pins CPython 3.12.
