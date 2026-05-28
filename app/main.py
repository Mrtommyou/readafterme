"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router

# Project root
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIO_DIR = DATA_DIR / "audio"
FRONTEND_DIR = ROOT / "frontend" / "dist"

# Ensure data directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title="ReadAfterMe",
    description="English shadowing practice app",
    version="0.1.0",
)

# CORS — allow all origins (mobile app + dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes (must come before catch-all)
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Serve frontend SPA ────────────────────────────────────────────────────

if FRONTEND_DIR.exists():
    # Static assets (JS, CSS, images)
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIR / "assets")),
        name="assets",
    )

    # Root → index.html
    @app.get("/")
    async def read_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"), media_type="text/html")

    # SPA catch-all for client-side routes (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Let API and health routes be handled above
        path = "/" + full_path
        if path.startswith("/api/") or path == "/health":
            raise HTTPException(404)
        # Serve existing static files (favicon, etc.)
        file = FRONTEND_DIR / full_path
        if file.exists() and file.is_file():
            return FileResponse(str(file))
        # Everything else → SPA
        index = FRONTEND_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index), media_type="text/html")
        raise HTTPException(404)
