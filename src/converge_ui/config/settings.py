from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    converge_base_url: str
    orchestrator_base_url: str
    data_mode: str
    request_timeout_seconds: float
    frontend_dist_dir: Path
    frontend_fallback_dir: Path


def load_settings() -> Settings:
    package_root = Path(__file__).resolve().parents[1]
    repo_root = package_root.parents[1]
    frontend_root = repo_root / "frontend"
    default_dist = frontend_root / "dist"
    fallback_dir = package_root / "web"

    return Settings(
        host=os.environ.get("CONVERGE_UI_HOST", "127.0.0.1"),
        port=int(os.environ.get("CONVERGE_UI_PORT", "9988")),
        converge_base_url=os.environ.get("CONVERGE_BASE_URL", "http://127.0.0.1:9876"),
        orchestrator_base_url=os.environ.get("ORCHESTRATOR_BASE_URL", "http://127.0.0.1:9989"),
        data_mode=os.environ.get("CONVERGE_UI_DATA_MODE", "hybrid").lower(),
        request_timeout_seconds=float(os.environ.get("CONVERGE_UI_TIMEOUT_SECONDS", "1.5")),
        frontend_dist_dir=Path(os.environ.get("CONVERGE_UI_FRONTEND_DIST", str(default_dist))),
        frontend_fallback_dir=fallback_dir,
    )
