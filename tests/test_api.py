from pathlib import Path

from fastapi.testclient import TestClient

import converge_ui.api.routes as routes
from converge_ui.app import app
from converge_ui.bff.service import ControlPlaneService, SnapshotCache
from converge_ui.config.settings import Settings


class FakeService:
    def get_overview(self) -> dict:
        return {
            "services": {"orchestrator": {"reachable": True}, "converge": {"reachable": False}},
            "counts": {"running": 2, "blocked": 1, "retry_pending": 1, "merged": 4, "failed": 0},
            "kpis": {"running": 2, "blocked": 1, "retry_pending": 1, "merged": 4, "failed": 0, "uptime_seconds": 10, "block_rate": 0.2},
            "alerts": [{"code": "service_down"}],
            "top_blockers": [{"job_id": "job-1"}],
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def get_operations(self) -> dict:
        return {
            "running": [{"job_id": "job-1", "status": "running"}],
            "retry_queue": [{"job_id": "job-2", "status": "retry_pending"}],
            "blocked": [{"job_id": "job-3", "status": "blocked"}],
            "recent_events": [{"job_id": "job-1", "to_state": "running"}],
            "filters": {"status": ["running", "blocked"], "agent": [], "risk_level": [], "source": ["real"]},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def list_jobs(self) -> dict:
        return {
            "items": [{"job_id": "job-1"}],
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
            "filters": {"status": []},
        }

    def get_job_detail(self, job_id: str) -> dict:
        return {
            "job": {"id": job_id, "status": "blocked", "intent_id": "intent-1"},
            "timeline": [{"to_state": "blocked"}],
            "intent": {"id": "intent-1"},
            "intent_events": [{"event_type": "POLICY_EVALUATED"}],
            "risk_review": {"risk": {"risk_level": "high"}},
            "operator_actions": {"retry": {"enabled": True}},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def get_intent_detail(self, intent_id: str) -> dict:
        return {
            "intent": {"id": intent_id},
            "events": [{"event_type": "INTENT_CREATED"}],
            "risk_review": {"risk": {"risk_score": 44}},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def refresh(self) -> dict:
        return {"status": "ok", "data_source": "real"}

    def retry_job(self, job_id: str) -> dict:
        return {"status": "disabled", "enabled": False, "job_id": job_id}


class NullOrchestrator:
    def __init__(self, state_payload=None) -> None:
        self._state_payload = state_payload

    def state(self):
        return self._state_payload

    def get_job(self, job_id: str):
        return None

    def refresh(self):
        return None

    def retry_job(self, job_id: str):
        return None


class NullConverge:
    def summary(self):
        return None

    def risk_gate_report(self):
        return None

    def health(self):
        return None

    def get_intent(self, intent_id: str):
        return None

    def get_intent_events(self, intent_id: str):
        return []

    def get_risk_review(self, intent_id: str):
        return None


def build_settings(mode: str = "hybrid") -> Settings:
    return Settings(
        host="127.0.0.1",
        port=9988,
        converge_base_url="http://127.0.0.1:9876",
        orchestrator_base_url="http://127.0.0.1:9989",
        data_mode=mode,
        request_timeout_seconds=1.0,
        frontend_dist_dir=Path("frontend/dist"),
        frontend_fallback_dir=Path("src/converge_ui/web"),
    )


client = TestClient(app)


def setup_module() -> None:
    routes.get_control_plane_service = lambda: FakeService()


def test_health_live() -> None:
    r = client.get("/health/live")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_overview_contract() -> None:
    r = client.get("/api/v1/overview")
    assert r.status_code == 200
    payload = r.json()
    assert payload["data_source"] == "real"
    assert "services" in payload
    assert "kpis" in payload
    assert payload["alerts"][0]["code"] == "service_down"


def test_operations_contract() -> None:
    r = client.get("/api/v1/operations")
    assert r.status_code == 200
    payload = r.json()
    assert payload["running"][0]["job_id"] == "job-1"
    assert payload["blocked"][0]["status"] == "blocked"


def test_job_detail_contract() -> None:
    r = client.get("/api/v1/jobs/job-3")
    assert r.status_code == 200
    payload = r.json()
    assert payload["job"]["intent_id"] == "intent-1"
    assert payload["risk_review"]["risk"]["risk_level"] == "high"


def test_intent_detail_contract() -> None:
    r = client.get("/api/v1/intents/intent-1")
    assert r.status_code == 200
    payload = r.json()
    assert payload["intent"]["id"] == "intent-1"
    assert payload["risk_review"]["risk"]["risk_score"] == 44


def test_refresh_action_contract() -> None:
    r = client.post("/api/v1/actions/refresh")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_serves_html_shell() -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_hybrid_falls_back_to_demo_state() -> None:
    service = ControlPlaneService(
        build_settings("hybrid"),
        orchestrator=NullOrchestrator(),
        converge=NullConverge(),
        cache=SnapshotCache(),
    )
    payload = service.get_overview()
    assert payload["data_source"] == "demo"
    assert payload["counts"]["running"] == 3
    assert payload["alerts"]


def test_stale_cache_is_used_when_real_state_disappears() -> None:
    cache = SnapshotCache()
    service = ControlPlaneService(
        build_settings("hybrid"),
        orchestrator=NullOrchestrator(
            {
                "generated_at": "2026-03-05T12:00:00Z",
                "uptime_seconds": 1,
                "counts": {"queued": 0, "claimed": 0, "running": 1, "evaluated": 0, "blocked": 0, "retry_pending": 0, "merged": 0, "failed": 0},
                "running": [],
                "retry_queue": [],
                "blocked": [],
                "converge": {"reachable": True},
            }
        ),
        converge=NullConverge(),
        cache=cache,
    )
    first = service.get_overview()
    assert first["data_source"] == "real"

    degraded = ControlPlaneService(
        build_settings("hybrid"),
        orchestrator=NullOrchestrator(),
        converge=NullConverge(),
        cache=cache,
    )
    second = degraded.get_overview()
    assert second["data_source"] == "stale-cache"


def test_refresh_returns_demo_unavailable_when_endpoint_missing() -> None:
    service = ControlPlaneService(
        build_settings("hybrid"),
        orchestrator=NullOrchestrator(),
        converge=NullConverge(),
        cache=SnapshotCache(),
    )
    payload = service.refresh()
    assert payload["status"] == "unavailable"
    assert payload["data_source"] == "demo"
