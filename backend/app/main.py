"""Fleet Control API entry point.

The frontend is plain HTML, CSS, and JavaScript, served by this app, so
there is no separate dev server or proxy to configure.

API routers are registered before the static mount so they take precedence.
The SQLite schema is created on startup; ``create_all`` is idempotent.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Fleet Control",
    version="1.0.0",
    description="Patrol operations console for security robots.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
