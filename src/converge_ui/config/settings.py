from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    environment: str
    host: str
    port: int
    converge_base_url: str
    orchestrator_base_url: str
    data_mode: str
    request_timeout_seconds: float
    frontend_dist_dir: Path
    frontend_fallback_dir: Path
    cors_origins: tuple[str, ...]
    rate_limit_enabled: bool
    rate_limit_rpm: int
    allow_fallback_ui: bool
    trust_proxy_headers: bool


def _load_cors_origins() -> tuple[str, ...]:
    raw = os.environ.get("CONVERGE_UI_CORS_ORIGINS", "")
    if raw:
        return tuple(origin.strip() for origin in raw.split(",") if origin.strip())
    return (
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )


def _validate_settings(settings: Settings) -> Settings:
    if settings.environment not in {"local", "staging", "production", "test"}:
        raise ValueError(f"Invalid CONVERGE_UI_ENV: {settings.environment}")
    if settings.data_mode not in {"real", "hybrid", "demo"}:
        raise ValueError(f"Invalid CONVERGE_UI_DATA_MODE: {settings.data_mode}")
    if settings.request_timeout_seconds <= 0:
        raise ValueError("CONVERGE_UI_TIMEOUT_SECONDS must be > 0")
    if settings.rate_limit_rpm <= 0:
        raise ValueError("CONVERGE_UI_RATE_LIMIT_RPM must be > 0")
    if not (1 <= settings.port <= 65535):
        raise ValueError("CONVERGE_UI_PORT must be between 1 and 65535")
    if settings.environment == "production" and not settings.cors_origins:
        raise ValueError("CONVERGE_UI_CORS_ORIGINS must not be empty in production")
    return settings


def load_settings() -> Settings:
    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parents[1]
    frontend_root = repo_root / "frontend"
    default_dist = frontend_root / "dist"
    fallback_dir = package_root / "web"
    environment = os.environ.get("CONVERGE_UI_ENV", "local").lower()
    allow_fallback_ui = _bool_env(
        "CONVERGE_UI_ALLOW_FALLBACK_UI",
        default=environment != "production",
    )

    return _validate_settings(Settings(
        environment=environment,
        host=os.environ.get("CONVERGE_UI_HOST", "127.0.0.1"),
        port=int(os.environ.get("CONVERGE_UI_PORT", "9988")),
        converge_base_url=os.environ.get("CONVERGE_BASE_URL", "http://127.0.0.1:9876"),
        orchestrator_base_url=os.environ.get("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:9989"),
        data_mode=os.environ.get("CONVERGE_UI_DATA_MODE", "hybrid").lower(),
        request_timeout_seconds=float(os.environ.get("CONVERGE_UI_TIMEOUT_SECONDS", "1.5")),
        frontend_dist_dir=Path(os.environ.get("CONVERGE_UI_FRONTEND_DIST", str(default_dist))),
        frontend_fallback_dir=fallback_dir,
        cors_origins=_load_cors_origins(),
        rate_limit_enabled=_bool_env("CONVERGE_UI_RATE_LIMIT_ENABLED", default=True),
        rate_limit_rpm=int(os.environ.get("CONVERGE_UI_RATE_LIMIT_RPM", "120")),
        allow_fallback_ui=allow_fallback_ui,
        trust_proxy_headers=_bool_env("CONVERGE_UI_TRUST_PROXY_HEADERS", default=environment in {"staging", "production"}),
    ))
