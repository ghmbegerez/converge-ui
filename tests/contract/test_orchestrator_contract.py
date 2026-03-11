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


# ---------------------------------------------------------------------------
# Payload shape contract tests — verify the STRUCTURE of responses,
# not just that routes exist. A field rename in the orchestrator that
# doesn't break route existence would still break the UI.
# ---------------------------------------------------------------------------


def _try_build_state_client():
    """Build a TestClient for the orchestrator state API."""
    try:
        from orchestrator.store import JobStore
        from orchestrator.webhook import create_state_app

        store = JobStore(":memory:")
        app = create_state_app(store)
        from fastapi.testclient import TestClient

        return TestClient(app), store
    except ImportError:
        return None, None


_STATE_CLIENT, _STATE_STORE = _try_build_state_client()


@pytest.mark.skipif(
    _STATE_CLIENT is None,
    reason="orchestrator state API not importable",
)
class TestOrchestratorStateShape:
    """Verify /api/v1/state returns the fields the UI relies on."""

    def test_state_top_level_fields(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        assert resp.status_code == 200
        data = resp.json()
        required = {"generated_at", "uptime_seconds", "counts", "running", "retry_queue", "blocked", "converge"}
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in /api/v1/state: {missing}"

    def test_state_counts_is_dict(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        assert isinstance(data["counts"], dict), "counts must be a dict"

    def test_state_lists_are_lists(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        for key in ("running", "retry_queue", "blocked"):
            assert isinstance(data[key], list), f"{key} must be a list"

    def test_state_converge_has_reachable(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        assert "reachable" in data["converge"], "converge must have 'reachable' field"

    def test_health_top_level_fields(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        required = {"status", "uptime_seconds"}
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in /api/v1/health: {missing}"

    def test_metrics_top_level_fields(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/metrics")
        assert resp.status_code == 200
        data = resp.json()
        required = {"uptime_seconds", "jobs_total", "counts", "throughput_per_hour", "block_rate"}
        missing = required - set(data.keys())
        assert not missing, f"Missing fields in /api/v1/metrics: {missing}"

    def test_metrics_counts_is_dict(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/metrics")
        data = resp.json()
        assert isinstance(data["counts"], dict)

    def test_metrics_numeric_fields(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/metrics")
        data = resp.json()
        assert isinstance(data["uptime_seconds"], (int, float))
        assert isinstance(data["jobs_total"], (int, float))
        assert isinstance(data["throughput_per_hour"], (int, float))
        assert isinstance(data["block_rate"], (int, float))


# ---------------------------------------------------------------------------
# Deeper shape tests — verify the STRUCTURE of individual items in lists
# and sub-endpoint responses that the UI actually reads.
# ---------------------------------------------------------------------------


def _seed_orchestrator_jobs(store):
    """Seed jobs of various statuses into the store for shape testing."""
    try:
        from orchestrator.models import Job, JobStatus, TransitionEvent

        store.save_job(
            Job(
                id="j-shape-run",
                prompt="running shape test",
                agent="claude",
                status=JobStatus.RUNNING,
                source_branch="orchestrator/claude/test",
                last_activity_at="2026-01-01T00:00:00+00:00",
            )
        )
        store.save_job(
            Job(
                id="j-shape-retry",
                prompt="retry shape test",
                agent="claude",
                status=JobStatus.RETRY_PENDING,
                retry_at="2099-01-01T00:00:00+00:00",
                attempts=2,
                error="merge_conflict",
            )
        )
        store.save_job(
            Job(
                id="j-shape-blocked",
                prompt="blocked shape test",
                agent="claude",
                status=JobStatus.BLOCKED,
                error="review_required",
            )
        )
        store.save_job(Job(id="j-shape-det", prompt="detail test", agent="claude"))
        store.save_event(
            TransitionEvent(
                job_id="j-shape-det",
                trace_id="trace-shape",
                from_state="queued",
                to_state="claimed",
                reason="test",
            )
        )
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    _STATE_CLIENT is None,
    reason="orchestrator state API not importable",
)
class TestOrchestratorItemShapes:
    """Verify fields inside running/retry/blocked items and sub-endpoints."""

    @pytest.fixture(autouse=True, scope="class")
    def _seed(self):
        if _STATE_STORE is not None:
            _seed_orchestrator_jobs(_STATE_STORE)

    def test_running_item_has_job_id(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        running = data.get("running", [])
        if running:
            assert "job_id" in running[0], f"running item must have 'job_id', got: {running[0].keys()}"

    def test_running_item_has_branch(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        running = data.get("running", [])
        if running:
            assert "branch" in running[0], f"running item must have 'branch', got: {running[0].keys()}"

    def test_retry_item_has_attempt(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        retry = data.get("retry_queue", [])
        if retry:
            assert "attempt" in retry[0], f"retry item must have 'attempt', got: {retry[0].keys()}"

    def test_retry_item_has_seconds_until_retry(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        retry = data.get("retry_queue", [])
        if retry:
            assert "seconds_until_retry" in retry[0], (
                f"retry item must have 'seconds_until_retry', got: {retry[0].keys()}"
            )

    def test_blocked_item_has_reason(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/state")
        data = resp.json()
        blocked = data.get("blocked", [])
        if blocked:
            assert "reason" in blocked[0], f"blocked item must have 'reason', got: {blocked[0].keys()}"

    def test_job_detail_has_job_and_timeline(self) -> None:
        resp = _STATE_CLIENT.get("/api/v1/jobs/j-shape-det")
        assert resp.status_code == 200
        data = resp.json()
        assert "job" in data, f"job detail must have 'job', got: {data.keys()}"
        assert "timeline" in data, f"job detail must have 'timeline', got: {data.keys()}"
        assert isinstance(data["job"], dict)
        assert isinstance(data["timeline"], list)

    def test_refresh_has_status(self) -> None:
        resp = _STATE_CLIENT.post("/api/v1/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data, f"refresh must have 'status', got: {data.keys()}"
