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
            "kpis": {"running": 2, "blocked": 1, "retry_pending": 1, "merged": 4, "failed": 0, "uptime_seconds": 10, "block_rate": 0.2, "open_reviews": 2, "mergeable_rate": 0.5},
            "alerts": [{"code": "service_down"}],
            "top_blockers": [{"job_id": "job-1"}],
            "review_summary": {"open_reviews": 2},
            "compliance": {"passed": False},
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
            "reviews": [{"task_id": "review-1", "status": "open"}],
            "review_summary": {"open_reviews": 1},
            "compliance_report": {"passed": False},
            "operator_actions": {"retry": {"enabled": True}},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def get_intent_detail(self, intent_id: str) -> dict:
        return {
            "intent": {"id": intent_id},
            "events": [{"event_type": "INTENT_CREATED"}],
            "risk_review": {"risk": {"risk_score": 44}},
            "reviews": [{"task_id": "review-1", "status": "open"}],
            "review_summary": {"open_reviews": 1},
            "compliance_report": {"passed": True},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def get_reviews(self) -> dict:
        return {
            "items": [{"task_id": "review-1", "intent_id": "intent-1", "status": "open", "reviewer": "ops-oncall", "priority": 1}],
            "summary": {"open_reviews": 1, "completed_reviews": 0},
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def get_compliance(self) -> dict:
        return {
            "report": {"passed": False, "mergeable_rate": 0.42},
            "alerts": [{"code": "security.attestation_missing", "severity": "critical"}],
            "generated_at": "2026-03-05T12:00:00Z",
            "data_source": "real",
        }

    def refresh(self) -> dict:
        return {"status": "ok", "data_source": "real"}

    def retry_job(self, job_id: str) -> dict:
        return {"status": "disabled", "enabled": False, "job_id": job_id}

    def request_review(self, *, intent_id: str, trigger: str = "policy", reviewer: str | None = None, priority: int | None = None) -> dict:
        return {"status": "ok", "review": {"task_id": "review-created", "intent_id": intent_id, "trigger": trigger, "reviewer": reviewer, "priority": priority}}

    def assign_review(self, task_id: str, *, reviewer: str) -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "reviewer": reviewer, "status": "assigned"}}

    def complete_review(self, task_id: str, *, resolution: str = "approved", notes: str = "") -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "status": "completed", "resolution": resolution, "notes": notes}}

    def escalate_review(self, task_id: str, *, reason: str = "sla_breach") -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "status": "escalated", "reason": reason}}

    def cancel_review(self, task_id: str, *, reason: str = "") -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "status": "cancelled", "reason": reason}}


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
    def dashboard(self):
        return None

    def dashboard_alerts(self):
        return None

    def summary(self):
        return None

    def risk_gate_report(self):
        return None

    def compliance_report(self):
        return None

    def compliance_alerts(self):
        return []

    def reviews(self, *, intent_id: str | None = None, status: str | None = None):
        return []

    def reviews_summary(self):
        return None

    def request_review(self, *, intent_id: str, trigger: str = "policy", reviewer: str | None = None, priority: int | None = None):
        return None

    def assign_review(self, task_id: str, *, reviewer: str):
        return None

    def complete_review(self, task_id: str, *, resolution: str = "approved", notes: str = ""):
        return None

    def escalate_review(self, task_id: str, *, reason: str = "sla_breach"):
        return None

    def cancel_review(self, task_id: str, *, reason: str = ""):
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
    assert payload["kpis"]["open_reviews"] == 2


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
    assert payload["review_summary"]["open_reviews"] == 1


def test_intent_detail_contract() -> None:
    r = client.get("/api/v1/intents/intent-1")
    assert r.status_code == 200
    payload = r.json()
    assert payload["intent"]["id"] == "intent-1"
    assert payload["risk_review"]["risk"]["risk_score"] == 44
    assert payload["reviews"][0]["task_id"] == "review-1"


def test_reviews_contract() -> None:
    r = client.get("/api/v1/reviews")
    assert r.status_code == 200
    payload = r.json()
    assert payload["items"][0]["task_id"] == "review-1"
    assert payload["summary"]["open_reviews"] == 1


def test_compliance_contract() -> None:
    r = client.get("/api/v1/compliance")
    assert r.status_code == 200
    payload = r.json()
    assert payload["report"]["passed"] is False
    assert payload["alerts"][0]["code"] == "security.attestation_missing"


def test_refresh_action_contract() -> None:
    r = client.post("/api/v1/actions/refresh")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_review_actions_contract() -> None:
    request = client.post("/api/v1/actions/reviews", json={"intent_id": "intent-1", "priority": 1})
    assert request.status_code == 200
    assert request.json()["review"]["intent_id"] == "intent-1"

    assign = client.post("/api/v1/actions/reviews/review-1/assign", json={"reviewer": "ops-oncall"})
    assert assign.status_code == 200
    assert assign.json()["review"]["reviewer"] == "ops-oncall"

    complete = client.post("/api/v1/actions/reviews/review-1/complete", json={"resolution": "approved", "notes": "looks good"})
    assert complete.status_code == 200
    assert complete.json()["review"]["status"] == "completed"

    escalate = client.post("/api/v1/actions/reviews/review-1/escalate", json={"reason": "sla_breach"})
    assert escalate.status_code == 200
    assert escalate.json()["review"]["status"] == "escalated"

    cancel = client.post("/api/v1/actions/reviews/review-1/cancel", json={"reason": "superseded"})
    assert cancel.status_code == 200
    assert cancel.json()["review"]["status"] == "cancelled"


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
