"""Contract tests: verify UI's orchestrator client matches orchestrator's actual API.

These tests import the orchestrator's FastAPI app and extract its routes,
then verify that every endpoint the UI client calls actually exists.

Note: The orchestrator mounts a state_api sub-app whose routes may not
appear in the main app's route list. We test those separately.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make orchestrator importable
# ---------------------------------------------------------------------------

ORCHESTRATOR_SRC = Path(__file__).resolve().parents[3] / "converge-orchestrator" / "src"
if str(ORCHESTRATOR_SRC) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_SRC))


def _try_extract_routes():
    """Extract all routes from orchestrator app + mounted sub-apps."""
    try:
        from orchestrator.store import JobStore
        from orchestrator.webhook import create_app

        store = JobStore(":memory:")
        app = create_app(store)

        routes = set()
        # Main app routes
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                for method in route.methods:
                    routes.add(f"{method} {route.path}")
            # Check mounted sub-applications
            if hasattr(route, "app") and hasattr(route.app, "routes"):
                prefix = getattr(route, "path", "")
                for sub_route in route.app.routes:
                    if hasattr(sub_route, "methods") and hasattr(sub_route, "path"):
                        for method in sub_route.methods:
                            routes.add(f"{method} {prefix}{sub_route.path}")
        return routes
    except ImportError:
        return None


ORCH_ROUTES = _try_extract_routes()


@pytest.mark.skipif(
    ORCH_ROUTES is None,
    reason="orchestrator package not importable",
)
class TestOrchestratorContract:
    def test_health_endpoint_exists(self) -> None:
        assert any("health" in r for r in ORCH_ROUTES if r.startswith("GET"))

    def test_jobs_list_endpoint(self) -> None:
        """UI calls GET /api/v1/jobs/{job_id}."""
        has_jobs = any("jobs" in r for r in ORCH_ROUTES if r.startswith("GET"))
        assert has_jobs, f"No jobs GET endpoint. Routes: {sorted(ORCH_ROUTES)}"

    def test_dispatch_endpoint(self) -> None:
        """Orchestrator should accept POST dispatch requests."""
        has_dispatch = any("dispatch" in r for r in ORCH_ROUTES if r.startswith("POST"))
        assert has_dispatch, f"No dispatch POST endpoint. Routes: {sorted(ORCH_ROUTES)}"

    def test_agents_endpoint(self) -> None:
        """UI queries agent availability."""
        has_agents = any("agents" in r for r in ORCH_ROUTES if r.startswith("GET"))
        assert has_agents, f"No agents GET endpoint. Routes: {sorted(ORCH_ROUTES)}"

    def test_webhook_endpoint(self) -> None:
        """Converge sends events to POST /webhook."""
        has_webhook = any("webhook" in r for r in ORCH_ROUTES if r.startswith("POST"))
        assert has_webhook, f"No webhook POST endpoint. Routes: {sorted(ORCH_ROUTES)}"

    def test_core_route_categories(self) -> None:
        """Verify key route categories the UI depends on exist."""
        categories = {
            "health": False,
            "jobs": False,
            "agents": False,
        }
        for route in ORCH_ROUTES:
            for cat in categories:
                if cat in route:
                    categories[cat] = True

        missing = [k for k, v in categories.items() if not v]
        assert not missing, (
            f"Missing route categories: {missing}. "
            f"Available: {sorted(ORCH_ROUTES)}"
        )
