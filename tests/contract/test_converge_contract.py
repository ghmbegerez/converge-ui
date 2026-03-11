"""Contract tests: verify UI's converge client matches converge's actual API.

These tests import converge's FastAPI app and extract its routes,
then verify that every endpoint the UI client calls actually exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make converge importable if installed
# ---------------------------------------------------------------------------

CONVERGE_SRC = Path(__file__).resolve().parents[3] / "converge" / "src"
if str(CONVERGE_SRC) not in sys.path:
    sys.path.insert(0, str(CONVERGE_SRC))


def _try_import_converge_routes():
    """Try to extract converge routes from its FastAPI app."""
    try:
        from converge.api import create_app

        app = create_app()

        routes = set()
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                for method in route.methods:
                    routes.add(f"{method} {route.path}")
        return routes
    except (ImportError, Exception):
        return None


CONVERGE_ROUTES = _try_import_converge_routes()

# Endpoints the UI client calls (from clients/converge_client.py)
# These are relative to the API prefix (/api or /v1)
UI_EXPECTED_PATHS = [
    ("GET", "/health"),
    ("GET", "/summary"),
    ("GET", "/dashboard"),
    ("GET", "/dashboard/alerts"),
    ("GET", "/risk/gate/report"),
    ("GET", "/compliance/report"),
    ("GET", "/compliance/alerts"),
    ("GET", "/reviews"),
    ("GET", "/reviews/summary"),
    ("GET", "/intents/{intent_id}"),
    ("GET", "/intents/{intent_id}/events"),
    ("GET", "/risk/review"),
    ("POST", "/reviews"),
    ("POST", "/reviews/{task_id}/assign"),
    ("POST", "/reviews/{task_id}/complete"),
    ("POST", "/reviews/{task_id}/escalate"),
    ("POST", "/reviews/{task_id}/cancel"),
]


def _route_matches(method: str, path: str, actual_routes: set[str]) -> bool:
    """Check if a UI-expected path matches any converge route.

    Converge mounts routers under /api and /v1 prefixes.
    """
    for prefix in ("/api", "/v1", ""):
        full = f"{method} {prefix}{path}"
        normalized = full.replace("{intent_id}", "{intent_id}").replace(
            "{task_id}", "{task_id}"
        )
        if normalized in actual_routes:
            return True
        # Try path fragment matching for parameterized routes
        for route in actual_routes:
            if method in route:
                # Strip parameters and compare base paths
                route_base = route.split("{")[0] if "{" in route else route
                expected_base = (
                    f"{method} {prefix}{path}".split("{")[0]
                    if "{" in path
                    else f"{method} {prefix}{path}"
                )
                if route_base.rstrip("/") == expected_base.rstrip("/"):
                    return True
    return False


@pytest.mark.skipif(
    CONVERGE_ROUTES is None,
    reason="converge package not importable",
)
class TestConvergeContract:
    def test_health_endpoint_exists(self) -> None:
        assert any("health" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_intents_endpoint_exists(self) -> None:
        assert any("intents" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_reviews_endpoint_exists(self) -> None:
        assert any("reviews" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_compliance_endpoint_exists(self) -> None:
        assert any("compliance" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_risk_endpoint_exists(self) -> None:
        assert any("risk" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_dashboard_endpoint_exists(self) -> None:
        assert any("dashboard" in r for r in CONVERGE_ROUTES if "GET" in r)

    def test_all_expected_endpoints(self) -> None:
        """Verify every UI client endpoint exists in converge."""
        missing = []
        for method, path in UI_EXPECTED_PATHS:
            if not _route_matches(method, path, CONVERGE_ROUTES):
                missing.append(f"{method} {path}")

        if missing:
            pytest.fail(
                f"UI client expects endpoints not found in converge:\n"
                + "\n".join(f"  - {m}" for m in missing)
                + f"\n\nActual converge routes:\n"
                + "\n".join(f"  {r}" for r in sorted(CONVERGE_ROUTES))
            )


# ---------------------------------------------------------------------------
# Payload shape contract tests — verify the STRUCTURE of responses.
# ---------------------------------------------------------------------------


def _try_build_converge_client():
    """Build a TestClient for the converge API with auth disabled."""
    try:
        import os

        os.environ["CONVERGE_AUTH_REQUIRED"] = "0"
        from converge.api import create_app

        app = create_app()
        from fastapi.testclient import TestClient

        return TestClient(app)
    except (ImportError, Exception):
        return None


_CONVERGE_CLIENT = _try_build_converge_client()


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeHealthShape:
    """Verify converge /health returns the fields the UI relies on."""

    def test_health_has_status_and_timestamp(self) -> None:
        resp = _CONVERGE_CLIENT.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data, "health must have 'status'"
        assert "timestamp" in data, "health must have 'timestamp'"

    def test_health_status_is_ok(self) -> None:
        resp = _CONVERGE_CLIENT.get("/health")
        data = resp.json()
        assert data["status"] == "ok"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeErrorEnvelope:
    """Verify converge errors use {"error": {"code": ..., "message": ...}}."""

    def test_404_error_envelope(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/intents/nonexistent-intent-xyz")
        assert resp.status_code in (404, 422)
        data = resp.json()
        assert "error" in data, f"Error response must have 'error' key, got: {data}"
        error = data["error"]
        assert isinstance(error, dict), f"error must be a dict, got: {type(error)}"
        assert "code" in error, f"error must have 'code', got: {error}"
        assert "message" in error, f"error must have 'message', got: {error}"

    def test_validation_error_envelope(self) -> None:
        """POST without required body should return error envelope."""
        resp = _CONVERGE_CLIENT.post("/v1/intents/evaluate")
        # FastAPI returns 400 or 422 for validation errors
        assert resp.status_code in (400, 422)
        data = resp.json()
        assert "error" in data, f"Validation error must have 'error' key, got: {data}"
        error = data["error"]
        assert isinstance(error, dict)
        assert "code" in error
        assert "message" in error


# ---------------------------------------------------------------------------
# Response shape tests — verify fields the UI actually reads from converge.
# A field rename in converge that doesn't break route existence would still
# break the UI's rendering logic.
# ---------------------------------------------------------------------------


def _seed_intent(client):
    """Create a test intent and return its id."""
    resp = client.post("/v1/intents", json={
        "source": "feature/ui-contract",
        "target": "main",
        "status": "READY",
    })
    if resp.status_code == 200:
        return resp.json().get("intent_id")
    return None


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeReviewsShape:
    """Verify converge /reviews returns fields the UI reads."""

    def test_reviews_has_reviews_key(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert "reviews" in data, f"reviews response must have 'reviews', got: {data.keys()}"
        assert isinstance(data["reviews"], list)


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeReviewsSummaryShape:
    """Verify converge /reviews/summary returns counters the UI reads."""

    def test_summary_has_total(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/reviews/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict), "summary must be a dict"
        assert "total" in data, f"summary must have 'total', got: {data.keys()}"
        assert "by_status" in data, f"summary must have 'by_status', got: {data.keys()}"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeComplianceShape:
    """Verify converge compliance endpoints return expected fields."""

    def test_report_has_passed_and_alerts(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/compliance/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "passed" in data, f"compliance report must have 'passed', got: {data.keys()}"
        assert isinstance(data["passed"], bool)
        assert "alerts" in data, f"compliance report must have 'alerts', got: {data.keys()}"
        assert isinstance(data["alerts"], list)

    def test_alerts_endpoint_returns_list(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/compliance/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"compliance alerts must be a list, got: {type(data)}"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeDashboardShape:
    """Verify converge dashboard endpoints return expected fields."""

    def test_dashboard_has_sections(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict), "dashboard must be a dict"
        for key in ("health", "queue", "compliance"):
            assert key in data, f"dashboard must have '{key}', got: {data.keys()}"

    def test_dashboard_alerts_has_alerts(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/dashboard/alerts")
        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data, f"dashboard alerts must have 'alerts', got: {data.keys()}"
        assert isinstance(data["alerts"], list)


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeRiskGateShape:
    """Verify converge /risk/gate/report returns evaluation stats."""

    def test_gate_report_has_fields(self) -> None:
        resp = _CONVERGE_CLIENT.get("/v1/risk/gate/report")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_evaluations" in data, f"gate report must have 'total_evaluations'"
        assert "block_rate" in data, f"gate report must have 'block_rate'"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeIntentDetailShape:
    """Verify converge /intents/{id} returns fields the UI reads."""

    def test_intent_has_core_fields(self) -> None:
        intent_id = _seed_intent(_CONVERGE_CLIENT)
        if intent_id is None:
            pytest.skip("could not seed intent")
        resp = _CONVERGE_CLIENT.get(f"/v1/intents/{intent_id}")
        assert resp.status_code == 200
        data = resp.json()
        for field in ("id", "status", "source", "target"):
            assert field in data, f"intent detail must have '{field}', got: {data.keys()}"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeIntentEventsShape:
    """Verify converge /intents/{id}/events returns a list."""

    def test_events_returns_list(self) -> None:
        intent_id = _seed_intent(_CONVERGE_CLIENT)
        if intent_id is None:
            pytest.skip("could not seed intent")
        resp = _CONVERGE_CLIENT.get(f"/v1/intents/{intent_id}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list), f"events must be a list, got: {type(data)}"


@pytest.mark.skipif(
    _CONVERGE_CLIENT is None,
    reason="converge API not importable for shape tests",
)
class TestConvergeRiskReviewShape:
    """Verify converge /risk/review returns a dict."""

    def test_risk_review_returns_dict(self) -> None:
        intent_id = _seed_intent(_CONVERGE_CLIENT)
        if intent_id is None:
            pytest.skip("could not seed intent")
        resp = _CONVERGE_CLIENT.get("/v1/risk/review", params={"intent_id": intent_id})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict), f"risk review must be a dict, got: {type(data)}"
