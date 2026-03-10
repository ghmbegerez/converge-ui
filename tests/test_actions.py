"""Direct tests for ActionExecutor + DataProvider — covers real + demo paths."""

from __future__ import annotations

from unittest.mock import patch

from converge_ui.bff.actions import ActionExecutor
from converge_ui.bff.cache import SnapshotCache
from converge_ui.bff.provider import DataProvider
from converge_ui.bff.service import ControlPlaneService
from converge_ui.clients.base import ApiClient
from test_api import NullConverge, NullOrchestrator, build_settings


class FakeOrchestrator(NullOrchestrator):
    def refresh(self):
        return {"status": "ok", "note": "cache cleared"}

    def retry_job(self, job_id: str):
        return {"status": "ok", "reason": "retry queued", "job_id": job_id}


class FakeConverge(NullConverge):
    def request_review(self, *, intent_id, trigger="policy", reviewer=None, priority=None):
        return {"task_id": f"review-{intent_id}", "status": "open"}

    def assign_review(self, task_id, *, reviewer):
        return {"task_id": task_id, "reviewer": reviewer, "status": "assigned"}

    def complete_review(self, task_id, *, resolution="approved", notes=""):
        return {"task_id": task_id, "status": "completed", "resolution": resolution}

    def escalate_review(self, task_id, *, reason="sla_breach"):
        return {"task_id": task_id, "status": "escalated", "reason": reason}

    def cancel_review(self, task_id, *, reason=""):
        return {"task_id": task_id, "status": "cancelled", "reason": reason}


def _make_executor(
    *,
    orchestrator=None,
    converge=None,
    mode: str = "hybrid",
) -> ActionExecutor:
    settings = build_settings(mode)
    return ActionExecutor(
        settings,
        orchestrator=orchestrator or NullOrchestrator(),
        converge=converge or NullConverge(),
        cache=SnapshotCache(),
    )


# ── refresh ──────────────────────────────────────────────────────────────


class TestRefresh:
    def test_real_refresh(self) -> None:
        executor = _make_executor(orchestrator=FakeOrchestrator())
        result = executor.refresh()
        assert result["status"] == "ok"
        assert result["reason"] == "cache cleared"
        assert result["data_source"] == "real"

    def test_demo_refresh(self) -> None:
        executor = _make_executor()
        result = executor.refresh()
        assert result["status"] == "unavailable"
        assert result["data_source"] == "demo"


# ── retry_job ────────────────────────────────────────────────────────────


class TestRetryJob:
    def test_real_retry(self) -> None:
        executor = _make_executor(orchestrator=FakeOrchestrator())
        result = executor.retry_job("job-42")
        assert result["status"] == "ok"
        assert result["job_id"] == "job-42"
        assert result["enabled"] is True
        assert result["data_source"] == "real"

    def test_demo_retry(self) -> None:
        executor = _make_executor()
        result = executor.retry_job("job-42")
        assert result["status"] == "disabled"
        assert result["enabled"] is False
        assert result["data_source"] == "demo"


# ── request_review ───────────────────────────────────────────────────────


class TestRequestReview:
    def test_real_request(self) -> None:
        executor = _make_executor(converge=FakeConverge())
        result = executor.request_review(intent_id="intent-1", trigger="policy")
        assert result["status"] == "ok"
        assert result["review"]["task_id"] == "review-intent-1"
        assert result["data_source"] == "real"

    def test_demo_request(self) -> None:
        executor = _make_executor(mode="demo")
        result = executor.request_review(intent_id="intent-1", trigger="policy", reviewer="bob", priority=2)
        assert result["status"] == "simulated"
        assert result["review"]["intent_id"] == "intent-1"
        assert result["review"]["reviewer"] == "bob"
        assert result["data_source"] == "demo"


# ── assign_review ────────────────────────────────────────────────────────


class TestAssignReview:
    def test_real_assign(self) -> None:
        executor = _make_executor(converge=FakeConverge())
        result = executor.assign_review("review-1", reviewer="ops-oncall")
        assert result["status"] == "ok"
        assert result["review"]["reviewer"] == "ops-oncall"
        assert result["data_source"] == "real"

    def test_demo_assign(self) -> None:
        executor = _make_executor(mode="demo")
        result = executor.assign_review("review-1", reviewer="ops-oncall")
        assert result["status"] == "simulated"
        assert result["data_source"] == "demo"


# ── complete_review ──────────────────────────────────────────────────────


class TestCompleteReview:
    def test_real_complete(self) -> None:
        executor = _make_executor(converge=FakeConverge())
        result = executor.complete_review("review-1", resolution="approved", notes="lgtm")
        assert result["status"] == "ok"
        assert result["review"]["status"] == "completed"
        assert result["data_source"] == "real"

    def test_demo_complete(self) -> None:
        executor = _make_executor(mode="demo")
        result = executor.complete_review("review-1")
        assert result["status"] == "simulated"
        assert result["review"]["resolution"] == "approved"


# ── escalate_review ──────────────────────────────────────────────────────


class TestEscalateReview:
    def test_real_escalate(self) -> None:
        executor = _make_executor(converge=FakeConverge())
        result = executor.escalate_review("review-1", reason="sla_breach")
        assert result["status"] == "ok"
        assert result["review"]["status"] == "escalated"
        assert result["data_source"] == "real"

    def test_demo_escalate(self) -> None:
        executor = _make_executor(mode="demo")
        result = executor.escalate_review("review-1")
        assert result["status"] == "simulated"
        assert result["review"]["reason"] == "sla_breach"


# ── cancel_review ────────────────────────────────────────────────────────


class TestCancelReview:
    def test_real_cancel(self) -> None:
        executor = _make_executor(converge=FakeConverge())
        result = executor.cancel_review("review-1", reason="superseded")
        assert result["status"] == "ok"
        assert result["review"]["status"] == "cancelled"
        assert result["data_source"] == "real"

    def test_demo_cancel(self) -> None:
        executor = _make_executor(mode="demo")
        result = executor.cancel_review("review-1")
        assert result["status"] == "simulated"
        assert result["review"]["status"] == "cancelled"


# ── DataProvider ─────────────────────────────────────────────────────────


class RealOrchestrator(NullOrchestrator):
    def __init__(self) -> None:
        super().__init__(state_payload={
            "generated_at": "2026-03-10T00:00:00Z",
            "uptime_seconds": 10,
            "counts": {"queued": 0, "claimed": 0, "running": 1, "evaluated": 0, "blocked": 0, "retry_pending": 0, "merged": 0, "failed": 0},
            "running": [],
            "retry_queue": [],
            "blocked": [],
            "converge": {"reachable": True},
        })

    def get_job(self, job_id: str):
        return {"job": {"id": job_id, "status": "running", "agent": "claude"}, "timeline": []}


class RealConverge(NullConverge):
    def reviews(self, *, intent_id=None, status=None):
        return [{"task_id": "review-1", "status": "open"}]

    def reviews_summary(self):
        return {"open_reviews": 1, "completed_reviews": 0}

    def compliance_report(self):
        return {"passed": True, "mergeable_rate": 1.0}

    def compliance_alerts(self):
        return [{"code": "test-alert"}]

    def get_intent(self, intent_id):
        return {"id": intent_id, "status": "VALIDATED"}

    def get_intent_events(self, intent_id):
        return [{"event_type": "CREATED"}]

    def get_risk_review(self, intent_id):
        return {"risk": {"risk_level": "low", "risk_score": 10}}


def _make_provider(*, orchestrator=None, converge=None, mode="hybrid") -> DataProvider:
    return DataProvider(
        build_settings(mode),
        orchestrator=orchestrator or NullOrchestrator(),
        converge=converge or NullConverge(),
        cache=SnapshotCache(),
    )


class TestProviderResolveState:
    def test_real_state(self) -> None:
        provider = _make_provider(orchestrator=RealOrchestrator())
        result = provider.resolve_state()
        assert result["source"] == "real"
        assert result["payload"]["counts"]["running"] == 1

    def test_demo_fallback(self) -> None:
        provider = _make_provider()
        result = provider.resolve_state()
        assert result["source"] == "demo"

    def test_stale_cache_fallback(self) -> None:
        cache = SnapshotCache()
        real_provider = DataProvider(
            build_settings("hybrid"),
            orchestrator=RealOrchestrator(),
            converge=NullConverge(),
            cache=cache,
        )
        real_provider.resolve_state()
        # Now make orchestrator unavailable
        degraded_provider = DataProvider(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=cache,
        )
        result = degraded_provider.resolve_state()
        assert result["source"] == "stale-cache"


class TestProviderGetJobPayload:
    def test_real_job(self) -> None:
        provider = _make_provider(orchestrator=RealOrchestrator())
        job, source = provider.get_job_payload("job-1")
        assert source == "real"
        assert job is not None
        assert job["job"]["id"] == "job-1"

    def test_demo_job_fallback(self) -> None:
        provider = _make_provider()
        job, source = provider.get_job_payload("unknown-job")
        # Either demo data or miss
        assert source == "demo"


class TestProviderReviewsPayload:
    def test_real_reviews(self) -> None:
        provider = _make_provider(converge=RealConverge())
        reviews, summary, source = provider.get_reviews_payload()
        assert source == "real"
        assert len(reviews) == 1
        assert summary is not None

    def test_demo_reviews(self) -> None:
        provider = _make_provider(mode="demo")
        reviews, summary, source = provider.get_reviews_payload()
        assert source == "demo"
        assert isinstance(reviews, list)


class TestProviderCompliancePayload:
    def test_real_compliance(self) -> None:
        provider = _make_provider(converge=RealConverge())
        report, alerts, source = provider.get_compliance_payload()
        assert source == "real"
        assert report is not None
        assert len(alerts) == 1

    def test_demo_compliance(self) -> None:
        provider = _make_provider(mode="demo")
        report, alerts, source = provider.get_compliance_payload()
        assert source == "demo"


class TestProviderIntentBundle:
    def test_real_intent(self) -> None:
        provider = _make_provider(converge=RealConverge())
        bundle = provider.get_intent_bundle("intent-1")
        assert bundle is not None
        assert bundle["data_source"] == "real"
        assert bundle["intent"]["id"] == "intent-1"

    def test_none_intent_id(self) -> None:
        provider = _make_provider()
        assert provider.get_intent_bundle(None) is None

    def test_empty_intent_id(self) -> None:
        provider = _make_provider()
        assert provider.get_intent_bundle("") is None

    def test_seed_jobs_for_demo(self) -> None:
        provider = _make_provider(mode="demo")
        jobs = provider.seed_jobs_for_source("demo")
        assert isinstance(jobs, dict)

    def test_seed_jobs_for_real(self) -> None:
        provider = _make_provider()
        jobs = provider.seed_jobs_for_source("real")
        assert jobs == {}


# ── ControlPlaneService extra paths ──────────────────────────────────────


class TestServiceReviewActions:
    def test_service_retry_job(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=FakeOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.retry_job("job-1")
        assert result["status"] == "ok"
        assert result["data_source"] == "real"

    def test_service_request_review(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=FakeConverge(),
            cache=SnapshotCache(),
        )
        result = service.request_review(intent_id="intent-1")
        assert result["status"] == "ok"

    def test_service_assign_review(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=FakeConverge(),
            cache=SnapshotCache(),
        )
        result = service.assign_review("review-1", reviewer="ops")
        assert result["status"] == "ok"

    def test_service_complete_review(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=FakeConverge(),
            cache=SnapshotCache(),
        )
        result = service.complete_review("review-1")
        assert result["status"] == "ok"

    def test_service_escalate_review(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=FakeConverge(),
            cache=SnapshotCache(),
        )
        result = service.escalate_review("review-1")
        assert result["status"] == "ok"

    def test_service_cancel_review(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=FakeConverge(),
            cache=SnapshotCache(),
        )
        result = service.cancel_review("review-1")
        assert result["status"] == "ok"


class TestServiceDataPaths:
    def test_service_get_reviews_hybrid(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_reviews()
        assert "items" in result
        assert result["data_source"] in ("real", "demo")

    def test_service_get_compliance_hybrid(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_compliance()
        assert "report" in result
        assert result["data_source"] in ("real", "demo")

    def test_service_get_operations_hybrid(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_operations()
        assert "running" in result
        assert result["data_source"] in ("real", "demo")

    def test_service_list_jobs_hybrid(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.list_jobs()
        assert "items" in result

    def test_service_get_job_detail_unknown(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_job_detail("unknown-job-id")
        # Should not crash
        assert "job" in result or "error" in result

    def test_service_get_intent_detail_unknown(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_intent_detail("unknown-intent")
        assert "intent" in result or "error" in result

    def test_service_get_job_detail_real(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=RealOrchestrator(),
            converge=NullConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_job_detail("job-real-1")
        assert result["job"]["id"] == "job-real-1"
        assert result["data_source"] == "real"

    def test_service_get_intent_detail_real(self) -> None:
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=RealConverge(),
            cache=SnapshotCache(),
        )
        result = service.get_intent_detail("intent-1")
        assert result["intent"]["id"] == "intent-1"
        assert result["data_source"] == "real"

    def test_service_job_detail_stale_cache(self) -> None:
        cache = SnapshotCache()
        # First: populate cache with real data
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=RealOrchestrator(),
            converge=NullConverge(),
            cache=cache,
        )
        service.get_job_detail("job-cached")
        # Now: orchestrator goes down
        degraded = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=cache,
        )
        result = degraded.get_job_detail("job-cached")
        assert result["data_source"] == "stale-cache"

    def test_service_intent_detail_stale_cache(self) -> None:
        cache = SnapshotCache()
        service = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=RealConverge(),
            cache=cache,
        )
        service.get_intent_detail("intent-cached")
        degraded = ControlPlaneService(
            build_settings("hybrid"),
            orchestrator=NullOrchestrator(),
            converge=NullConverge(),
            cache=cache,
        )
        result = degraded.get_intent_detail("intent-cached")
        assert result["data_source"] == "stale-cache"


# ── ApiClient base ───────────────────────────────────────────────────────


class TestApiClient:
    def test_get_returns_none_on_error(self) -> None:
        client = ApiClient("http://localhost:1", timeout_seconds=0.1)
        result = client._get("/nonexistent")
        assert result is None

    def test_post_returns_none_on_error(self) -> None:
        client = ApiClient("http://localhost:1", timeout_seconds=0.1)
        result = client._post("/nonexistent", json={"test": True})
        assert result is None
