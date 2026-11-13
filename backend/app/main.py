"""Fleet Control API entry point.

The frontend is plain HTML, CSS, and JavaScript, served by this app, so
there is no separate dev server or proxy to configure.

SCRUM-21 adds the database, the health check, and the first API routers.
Register them before the static mount so they take precedence.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="Fleet Control",
    version="0.1.0",
    description="Patrol operations console for security robots.",
)

# API routers mount here from SCRUM-21 onwards, before the static files.
# app.include_router(api_router, prefix="/api/v1")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
