"""FastAPI application entry point."""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.config import settings
from app.database import init_db
import app.models  # noqa: F401 — register models with Base.metadata

app = FastAPI(
    title="合同管理系统-评测",
    version="0.0.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Register routers
from app.routers import auth as auth_router  # noqa: E402
from app.routers import users as users_router  # noqa: E402
from app.routers import contracts as contracts_router  # noqa: E402
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(contracts_router.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.0.1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.on_event("startup")
def on_startup():
    """Initialize database and ensure upload directory exists on startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    init_db()
