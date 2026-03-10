from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import converge_ui.api.routes as routes
from converge_ui.app import create_app
from converge_ui.observability import stats


class FakeService:
    class _Reachable:
        def is_reachable(self) -> bool:
            return True

    orchestrator = _Reachable()
    converge = _Reachable()

    def get_overview(self) -> dict:
        stats().inc("test.overview")
        return {
            "services": {"orchestrator": {"reachable": True}, "converge": {"reachable": True}},
            "counts": {"running": 1, "blocked": 0, "retry_pending": 0, "merged": 0, "failed": 0},
            "kpis": {"running": 1, "blocked": 0, "retry_pending": 0, "merged": 0, "failed": 0, "uptime_seconds": 1, "block_rate": 0.0},
            "alerts": [],
            "top_blockers": [],
            "generated_at": "2026-03-09T00:00:00Z",
            "data_source": "real",
        }

    def get_operations(self) -> dict:
        return {
            "running": [],
            "retry_queue": [],
            "blocked": [],
            "recent_events": [],
            "filters": {"status": [], "agent": [], "risk_level": [], "source": ["real"]},
            "generated_at": "2026-03-09T00:00:00Z",
            "data_source": "real",
        }

    def list_jobs(self) -> dict:
        return {"items": [], "generated_at": "2026-03-09T00:00:00Z", "data_source": "real", "filters": {}}

    def get_job_detail(self, job_id: str) -> dict:
        return {"job": {"id": job_id}, "timeline": [], "intent": None, "risk_review": None, "operator_actions": {}, "generated_at": "2026-03-09T00:00:00Z", "data_source": "real"}

    def get_intent_detail(self, intent_id: str) -> dict:
        return {"intent": {"id": intent_id}, "events": [], "risk_review": None, "generated_at": "2026-03-09T00:00:00Z", "data_source": "real"}

    def get_reviews(self) -> dict:
        return {"items": [], "summary": {}, "generated_at": "2026-03-09T00:00:00Z", "data_source": "real"}

    def get_compliance(self) -> dict:
        return {"report": {}, "alerts": [], "generated_at": "2026-03-09T00:00:00Z", "data_source": "real"}

    def refresh(self) -> dict:
        return {"status": "ok", "data_source": "real"}


def test_debug_endpoint_reports_stats() -> None:
    stats().reset()
    routes.get_control_plane_service = lambda: FakeService()
    client = TestClient(create_app())
    overview = client.get("/api/v1/overview")
    assert overview.status_code == 200
    debug = client.get("/api/v1/system/debug")
    assert debug.status_code == 200
    assert "test.overview" in debug.json()["stats"]


def test_production_without_dist_or_fallback_returns_503() -> None:
    missing = str(Path("/tmp/does-not-exist-converge-ui-dist"))
    env = {
        "CONVERGE_UI_ENV": "production",
        "CONVERGE_UI_FRONTEND_DIST": missing,
        "CONVERGE_UI_ALLOW_FALLBACK_UI": "0",
        "CONVERGE_UI_AUTH_REQUIRED": "0",
        "CONVERGE_UI_RATE_LIMIT_ENABLED": "0",
    }
    with patch.dict(os.environ, env, clear=False):
        client = TestClient(create_app())
        response = client.get("/")
    assert response.status_code == 503
