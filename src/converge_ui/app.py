from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from converge_ui.api.auth import AuthMiddleware, init_auth
from converge_ui.api.routes import router
from converge_ui.config.settings import load_settings
from converge_ui.logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="converge-ui", version="0.3.0")
    app.state.frontend_dist_dir = settings.frontend_dist_dir
    app.include_router(router)

    ui_dir = _resolve_ui_dir(settings.frontend_dist_dir, settings.frontend_fallback_dir)
    assets_dir = ui_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False, response_model=None)
    @app.get("/operations", include_in_schema=False, response_model=None)
    @app.get("/reviews", include_in_schema=False, response_model=None)
    @app.get("/compliance", include_in_schema=False, response_model=None)
    @app.get("/jobs/{job_id}", include_in_schema=False, response_model=None)
    @app.get("/intents/{intent_id}", include_in_schema=False, response_model=None)
    def spa_shell(job_id: str | None = None):
        index_file = ui_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse(
            {
                "status": "frontend_unavailable",
                "detail": "UI bundle not found. Build frontend/ or use the fallback shell.",
            },
            status_code=503,
        )

    # Middleware — last added = outermost (processed first)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    init_auth()

    return app


def _resolve_ui_dir(frontend_dist_dir: Path, frontend_fallback_dir: Path) -> Path:
    if (frontend_dist_dir / "index.html").exists():
        return frontend_dist_dir
    return frontend_fallback_dir


app = create_app()
