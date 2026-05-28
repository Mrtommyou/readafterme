# ReadAfterMe — English shadowing practice app

## Architecture

- **Backend**: Python 3.12 + FastAPI (`app/`). REST API routes at `app/api/routes.py`. Main entry: `app/main.py`.
- **Frontend**: React SPA (`frontend/`) with Tailwind CSS v4 + Vite. Served by FastAPI as static files.
- **Core logic** in `core/`: ASR (whisper.cpp), audio (ffmpeg), scoring, phonemes, translation, alignment.

## Critical external dependencies

- **whisper.cpp**: binary at `/tmp/whisper.cpp/build/bin/whisper-cli`. **Two models used:**
  - `ggml-tiny.en.bin` — video transcription (`core/asr.py`). Fast.
  - `ggml-small.en.bin` — user recording scoring (`core/scoring.py`). More accurate.
  Both hardcoded via `Path` globals. Must exist at runtime.
- **espeak-ng**: IPA phoneme conversion for pronunciation scoring (`core/phonemes.py`). Must be on `PATH`.
- **ffmpeg** / **ffprobe**: audio extraction, slicing, duration. Must be on `PATH`.
- **uv**: package manager. Mirror at `https://mirrors.aliyun.com/pypi/simple/`.
- **Levenshtein** C extension: WER/CER/PER calculation (`core/scoring.py`, `core/align.py`).

## Scoring

Three-dimension scoring inspired by [Echoic](https://github.com/xialeistudio/echoic):
- **Pronunciation** (0–100, weight 0.5): WER 35% + CER 25% + PER 40%, calibrated by age/strictness curve
- **Fluency** (0–100, weight 0.3): rate penalty (30%) + gap penalty (70%)
- **Completeness** (0–100, weight 0.2): fraction of reference words spoken
- **Overall**: `pronunciation×0.5 + fluency×0.3 + completeness×0.2`
- **Timing** (returned but not in overall): duration match within 20% tolerance

Age profiles (`core/scoring.py:PROFILES`): adult (strict), teen, **child (default)**, beginner — each adjusts strictness, ideal words/sec, gap threshold, and calibration curve.

Scoring flow: user `.webm` → whisper.cpp (small.en) → text → WER/CER + espeak-ng IPA → PER → calibrated scores.

## Commands

| Action | Command |
|--------|---------|
| Start dev server | `uv run python run.py` (port 9004, hot reload) |
| Start HTTPS | `bash run_https.sh` (auto-gen self-signed cert + build frontend) |
| Lint Python | `uv run ruff check app/ core/` |
| Build frontend | `cd frontend && npm run build` (outputs to `frontend/dist/`) |
| TS check | `cd frontend && npx tsc --noEmit` |
| Dev frontend | `cd frontend && npm run dev` (port 9005, proxies `/api` → 9004) |

## Data

- `data/videos.json` — metadata DB (JSON array, gitignored). Created at runtime.
- `data/uploads/` — raw uploaded videos (transcoded to H.264).
- `data/audio/` — extracted 16kHz mono WAV files for ASR.
- `data/scores/{video_id}.json` — per-sentence score persistence, keyed by sentence index.
- `data/models/` — downloaded whisper models (SymLink from `/tmp/whisper.cpp/models/` on this machine).

## Key routes (`/api`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/videos` | List all videos (with processing status) |
| POST | `/upload` | Upload video (returns immediately, processes in background) |
| GET | `/videos/{id}/sentences` | Sentences + translations |
| GET | `/videos/{id}/file` | Video file stream |
| GET | `/videos/{id}/status` | Processing progress |
| DELETE | `/videos/{id}` | Delete video + all associated data |
| POST | `/recordings` | Save user recording |
| GET | `/recordings/{video_id}/{idx}/file` | Load saved recording |
| POST | `/recordings/score` | Persist a score result |
| GET | `/recordings/{video_id}/scores` | Get all scores for a video |
| POST | `/score` | Score a single recording (accepts `age_group` FormData field) |
| GET | `/history` | History with real avg scores from saved data |

## Quirks & gotchas

- **Frontend routing**: `/assets` is mounted as StaticFiles. SPA catch-all serves `index.html` for all non-`/api/`, non-asset routes.
- **Video processing** runs in background via `asyncio.create_task`. Order matters: **extract audio first** (clean), **then transcode video** (H.264). Transcoding before extraction re-encodes audio and degrades ASR quality.
- **[Music] segments** from whisper are filtered out — they don't appear in the sentence list.
- **Translation** uses `translators` library with fallback chain: youdao → bing → alibaba → empty strings. No API key needed.
- **Age group** defaults to `child` on frontend (`age_group=child` in score FormData). Override for adult/teen/beginner scoring.
- **Recording**: browser `MediaRecorder` API (webm/opus). Auto-stops at sentence duration + 1s.
- **Score persistence**: scores auto-save to `data/scores/{video_id}.json` after every recording.
- **kivy_app/** directory is abandoned code (previous Kivy/Buildozer attempt). Not used by the running app. Can be ignored.
- **`pyproject.toml`** has `required-environments = ["sys_platform == 'linux' and platform_machine == 'x86_64'"]` — will fail on macOS/Windows.
- `main.py` at repo root is a stub (`print("Hello")`) — not the entry point. Real entry is `run.py`.
- SSL certs auto-detected at `certs/cert.pem` + `certs/key.pem` if present. Override via `SSL_CERT` / `SSL_KEY` env vars.
