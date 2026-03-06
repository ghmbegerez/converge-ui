"""Tests for input validation on POST endpoints."""

from __future__ import annotations

import os

# Ensure auth is disabled before any app import
os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
os.environ.pop("CONVERGE_UI_API_KEYS", None)

from fastapi.testclient import TestClient

import converge_ui.api.routes as routes
from converge_ui.api.auth import init_auth

# Re-init auth to ensure it picks up disabled state
init_auth()


class FakeService:
    """Minimal fake that satisfies the route contracts."""

    def request_review(self, *, intent_id: str, trigger: str, reviewer: str | None, priority: int | None) -> dict:
        return {"status": "ok", "review": {"intent_id": intent_id, "trigger": trigger}}

    def assign_review(self, task_id: str, *, reviewer: str) -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "reviewer": reviewer}}

    def complete_review(self, task_id: str, *, resolution: str, notes: str) -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "resolution": resolution}}

    def escalate_review(self, task_id: str, *, reason: str) -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "reason": reason}}

    def cancel_review(self, task_id: str, *, reason: str) -> dict:
        return {"status": "ok", "review": {"task_id": task_id, "reason": reason}}

    def retry_job(self, job_id: str) -> dict:
        return {"status": "ok", "job_id": job_id}

    def refresh(self) -> dict:
        return {"status": "ok"}

    def get_job_detail(self, job_id: str) -> dict:
        return {"job": {"id": job_id}, "data_source": "demo"}

    def get_intent_detail(self, intent_id: str) -> dict:
        return {"intent": {"id": intent_id}, "data_source": "demo"}


def setup_module() -> None:
    # Ensure auth is disabled for all tests in this module
    os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
    os.environ.pop("CONVERGE_UI_API_KEYS", None)
    init_auth()
    routes.get_control_plane_service = lambda: FakeService()


from converge_ui.app import create_app

client = TestClient(create_app())


class TestReviewCreateValidation:
    def test_valid_request(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "intent-001", "trigger": "policy", "priority": 1},
        )
        assert r.status_code == 200

    def test_missing_intent_id(self) -> None:
        r = client.post("/api/v1/actions/reviews", json={})
        assert r.status_code == 422

    def test_empty_intent_id(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews", json={"intent_id": ""}
        )
        assert r.status_code == 422

    def test_invalid_intent_id_chars(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "intent<script>alert(1)</script>"},
        )
        assert r.status_code == 422

    def test_intent_id_too_long(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "x" * 201},
        )
        assert r.status_code == 422

    def test_invalid_trigger(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "intent-001", "trigger": "invalid"},
        )
        assert r.status_code == 422

    def test_priority_out_of_range(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "intent-001", "priority": 99},
        )
        assert r.status_code == 422

    def test_priority_zero(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews",
            json={"intent_id": "intent-001", "priority": 0},
        )
        assert r.status_code == 422


class TestReviewAssignValidation:
    def test_valid_assign(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/assign",
            json={"reviewer": "ops-oncall"},
        )
        assert r.status_code == 200

    def test_empty_reviewer(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/assign",
            json={"reviewer": ""},
        )
        assert r.status_code == 422

    def test_missing_reviewer(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/assign",
            json={},
        )
        assert r.status_code == 422


class TestReviewCompleteValidation:
    def test_valid_complete(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/complete",
            json={"resolution": "approved", "notes": "looks good"},
        )
        assert r.status_code == 200

    def test_invalid_resolution(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/complete",
            json={"resolution": "yolo"},
        )
        assert r.status_code == 422

    def test_notes_too_long(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/complete",
            json={"resolution": "approved", "notes": "x" * 2001},
        )
        assert r.status_code == 422

    def test_default_resolution(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/complete",
            json={},
        )
        assert r.status_code == 200


class TestReviewEscalateValidation:
    def test_valid_escalate(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/escalate",
            json={"reason": "sla_breach"},
        )
        assert r.status_code == 200

    def test_reason_too_long(self) -> None:
        r = client.post(
            "/api/v1/actions/reviews/review-1/escalate",
            json={"reason": "x" * 501},
        )
        assert r.status_code == 422


class TestPathParamValidation:
    def test_valid_job_id(self) -> None:
        r = client.get("/api/v1/jobs/job-123")
        assert r.status_code == 200

    def test_invalid_job_id_chars(self) -> None:
        r = client.get("/api/v1/jobs/job<bad>")
        assert r.status_code == 400

    def test_valid_intent_id(self) -> None:
        r = client.get("/api/v1/intents/intent-001")
        assert r.status_code == 200

    def test_invalid_intent_id_chars(self) -> None:
        r = client.get("/api/v1/intents/intent<bad>")
        assert r.status_code == 400
