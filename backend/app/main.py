"""FastAPI application entry point."""

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
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
from app.routers import attachments as attachments_router  # noqa: E402
app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(contracts_router.router)
app.include_router(attachments_router.router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    """Add Cache-Control: no-cache to HTML responses for browser verification."""
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        response.headers["Cache-Control"] = "no-cache"
    return response


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


# Serve frontend static files (SPA)
FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    base_path = settings.BASE_PATH.rstrip("/")

    @app.get(f"{base_path}/healthz", include_in_schema=False)
    def base_health_check():
        """Health check under BASE_PATH for deployment."""
        return {
            "status": "ok",
            "version": "0.0.1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    app.mount(
        f"{base_path}/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="frontend_assets",
    )

    @app.get(f"{base_path}/{{path:path}}", include_in_schema=False)
    @app.get(f"{base_path}", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_frontend(path: str = ""):
        """Serve frontend index.html for all SPA routes under BASE_PATH."""
        if not path or path == "index.html":
            target = FRONTEND_DIST / "index.html"
        else:
            target = FRONTEND_DIST / path
        if not target.exists() or not target.is_relative_to(FRONTEND_DIST):
            target = FRONTEND_DIST / "index.html"
        if not target.exists():
            return Response(content="index.html not found", status_code=404)
        return Response(
            content=target.read_bytes(),
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )
