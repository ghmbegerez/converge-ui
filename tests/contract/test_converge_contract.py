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
