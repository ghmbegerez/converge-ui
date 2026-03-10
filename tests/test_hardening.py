"""Integration tests for production hardening: security headers, CORS, readiness, rate limit."""

from __future__ import annotations

import os
from unittest.mock import patch

os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
os.environ["CONVERGE_UI_RATE_LIMIT_ENABLED"] = "0"

from fastapi.testclient import TestClient

import converge_ui.api.routes as routes
from converge_ui.api.auth import init_auth
from converge_ui.app import app


class FakeServiceMinimal:
    """Minimal fake service with no orchestrator/converge attrs."""

    def get_overview(self) -> dict:
        return {"data_source": "fake"}


class FakeServiceWithReachable:
    """Fake service with orchestrator/converge that report reachable."""

    class _Reachable:
        def is_reachable(self) -> bool:
            return True

    orchestrator = _Reachable()
    converge = _Reachable()


class FakeServiceUnreachable:
    """Fake service with orchestrator/converge that report unreachable."""

    class _Unreachable:
        def is_reachable(self) -> bool:
            return False

    orchestrator = _Unreachable()
    converge = _Unreachable()


client = TestClient(app)


def setup_module() -> None:
    os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
    init_auth()
    routes.get_control_plane_service = lambda: FakeServiceMinimal()


class TestSecurityHeaders:
    def test_health_live_has_security_headers(self) -> None:
        r = client.get("/health/live")
        assert r.status_code == 200
        assert r.headers["X-Content-Type-Options"] == "nosniff"
        assert r.headers["X-Frame-Options"] == "DENY"
        assert r.headers["X-XSS-Protection"] == "0"
        assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "camera=()" in r.headers["Permissions-Policy"]


class TestMetricsEndpoint:
    def test_metrics_is_public_and_text(self) -> None:
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "text/plain" in r.headers["content-type"]
        assert "converge_ui_runtime_counter" in r.text


class TestReadinessCheck:
    def test_degraded_when_no_clients(self) -> None:
        routes.get_control_plane_service = lambda: FakeServiceMinimal()
        r = client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "degraded"
        assert data["orchestrator"] == "unreachable"
        assert data["converge"] == "unreachable"

    def test_ready_when_backends_reachable(self) -> None:
        routes.get_control_plane_service = lambda: FakeServiceWithReachable()
        r = client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ready"
        assert data["orchestrator"] == "ok"
        assert data["converge"] == "ok"

    def test_degraded_when_backends_unreachable(self) -> None:
        routes.get_control_plane_service = lambda: FakeServiceUnreachable()
        r = client.get("/health/ready")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "degraded"
        assert data["orchestrator"] == "unreachable"
        assert data["converge"] == "unreachable"


class TestAuthErrorFormat:
    def test_401_uses_detail_key(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "valid:admin:root",
        }
        with patch.dict(os.environ, env, clear=False):
            init_auth()
            r = client.get("/api/v1/overview", headers={"authorization": "wrong-key"})
            assert r.status_code == 401
            data = r.json()
            assert "detail" in data
            assert "error" not in data

        # restore
        os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
        init_auth()

    def test_403_uses_detail_key(self) -> None:
        env = {
            "CONVERGE_UI_AUTH_REQUIRED": "1",
            "CONVERGE_UI_API_KEYS": "viewerkey:viewer:alice",
        }
        with patch.dict(os.environ, env, clear=False):
            init_auth()
            r = client.post(
                "/api/v1/actions/refresh",
                headers={"authorization": "viewerkey"},
            )
            assert r.status_code == 403
            data = r.json()
            assert "detail" in data
            assert "error" not in data

        os.environ["CONVERGE_UI_AUTH_REQUIRED"] = "0"
        init_auth()
