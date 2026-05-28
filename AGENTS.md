# ReadAfterMe — English shadowing practice app

## Architecture

- **Backend**: Python 3.12 + FastAPI (`app/`) with REST API routes in `app/api/routes.py`. Run via `uv run python run.py`.
- **Frontend**: React SPA (`frontend/`) — served by FastAPI as static files (SPA catch-all at `/`)
- **Core logic** in `core/`: ASR (whisper.cpp), audio (ffmpeg), alignment, translation, scoring.

## Critical external dependencies

- **whisper.cpp**: binary at `/tmp/whisper.cpp/build/bin/whisper-cli`, model at `/tmp/whisper.cpp/models/ggml-small.en.bin`. Hardcoded in `core/asr.py` and `core/scoring.py`. Must be present at runtime.
- **espeak-ng**: used in `core/phonemes.py` for IPA phoneme conversion in pronunciation scoring.
- **ffmpeg** / **ffprobe**: used for audio extraction + duration. Must be on `PATH`.
- **uv**: package manager. `uv.lock` and `pyproject.toml` at repo root. Mirror at `https://mirrors.aliyun.com/pypi/simple/`.
- **espeak-ng**: used in `core/phonemes.py` for IPA phoneme conversion in pronunciation scoring.
- **Levenshtein** C extension: used in `core/align.py` and `core/scoring.py` for WER calculation.

## Scoring

Three-dimension scoring inspired by [Echoic](https://github.com/xialeistudio/echoic):
- **Pronunciation** (0-100, weight 0.5): WER 35% + CER 25% + PER 40%, calibrated by age profile
- **Fluency** (0-100, weight 0.3): rate penalty (30%) + gap penalty (70%), Echoic-style
- **Completeness** (0-100, weight 0.2): fraction of reference words spoken
- **Overall**: pronunciation×0.5 + fluency×0.3 + completeness×0.2

Age profiles (`core/scoring.py:PROFILES`): adult (strict), teen, **child (default)**, beginner — each adjusts strictness, ideal rate, gap threshold, and calibration curve.

## Commands

- `uv run python run.py` — start backend dev server on port 9004 (default; override via `PORT` env var). Hot reload via uvicorn `reload=True`.
- `uv run ruff check app/ core/ kivy_app/` — lint all Python code
- `cd frontend && npm run build` — build React frontend (outputs to `frontend/dist/`)
- `cd frontend && npx tsc --noEmit` — TypeScript check

## Quirks

- Translation has a multi-backend fallback chain: googletrans → MyMemory API → empty strings.
- ASR output JSON sidecar file pattern: `{audio_path}.json`.
- `data/` is gitignored; `data/videos.json` is the metadata DB (created at runtime).
- `pyproject.toml` has `required-environments` restricting to `linux x86_64`.
- Frontend React app mounts `frontend/dist/` at `/assets`; SPA catch-all serves `index.html` for all non-API, non-asset routes.
- Audio recording: browser `MediaRecorder` API (webm/opus).
- `.python-version` pins CPython 3.12.
- Score persistence: saved as JSON in `data/scores/{video_id}.json` per sentence.
