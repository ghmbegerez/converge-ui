from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from converge_ui.api.auth import AuthMiddleware, init_auth
from converge_ui.api.routes import router
from converge_ui.config.settings import load_settings
from converge_ui.http import RateLimitMiddleware, SecurityHeadersMiddleware, app_lifespan
from converge_ui.logging import RequestLoggingMiddleware
from converge_ui.rate_limit import init_rate_limit


def create_app() -> FastAPI:
    settings = load_settings()
    app = FastAPI(title="converge-ui", version="0.3.0", lifespan=app_lifespan)
    app.state.frontend_dist_dir = settings.frontend_dist_dir
    app.state.frontend_fallback_enabled = settings.allow_fallback_ui
    app.include_router(router)

    ui_dir = _resolve_ui_dir(
        settings.frontend_dist_dir,
        settings.frontend_fallback_dir,
        allow_fallback=settings.allow_fallback_ui,
    )
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
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuthMiddleware)

    allowed_origins = list(settings.cors_origins)
    allow_creds = "*" not in allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_creds,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RateLimitMiddleware, trust_proxy_headers=settings.trust_proxy_headers)

    init_auth()
    init_rate_limit(enabled=settings.rate_limit_enabled, max_requests=settings.rate_limit_rpm)

    return app


def _resolve_ui_dir(frontend_dist_dir: Path, frontend_fallback_dir: Path, *, allow_fallback: bool) -> Path:
    if (frontend_dist_dir / "index.html").exists():
        return frontend_dist_dir
    if allow_fallback:
        return frontend_fallback_dir
    return frontend_dist_dir


app = create_app()
