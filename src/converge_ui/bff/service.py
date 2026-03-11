from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from converge_ui.bff.actions import ActionExecutor
from converge_ui.bff.cache import SnapshotCache
from converge_ui.bff.helpers import (
    build_alerts,
    build_services,
    merge_source,
    operator_actions,
    recent_events,
    summary_value,
)
from converge_ui.bff.provider import DataProvider
from converge_ui.clients.converge_client import ConvergeClient
from converge_ui.clients.orchestrator_client import OrchestratorClient
from converge_ui.config.settings import Settings, load_settings


class ControlPlaneService:
    def __init__(
        self,
        settings: Settings,
        orchestrator: OrchestratorClient | None = None,
        converge: ConvergeClient | None = None,
        cache: SnapshotCache | None = None,
    ) -> None:
        self.settings = settings
        timeout = settings.request_timeout_seconds
        self.orchestrator = orchestrator or OrchestratorClient(settings.orchestrator_base_url, timeout)
        self.converge = converge or ConvergeClient(settings.converge_base_url, timeout)
        self.cache = cache or SnapshotCache(ttl_seconds=settings.cache_ttl_seconds)
        self.actions = ActionExecutor(
            settings,
            orchestrator=self.orchestrator,
            converge=self.converge,
            cache=self.cache,
        )
        self.provider = DataProvider(
            settings,
            orchestrator=self.orchestrator,
            converge=self.converge,
            cache=self.cache,
        )

    def get_overview(self) -> dict[str, Any]:
        state_bundle = self.provider.resolve_state()
        # Parallelize independent converge calls
        futures: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=7) as pool:
            futures = {
                "summary": pool.submit(self.converge.summary),
                "dashboard": pool.submit(self.converge.dashboard),
                "dashboard_alerts": pool.submit(self.converge.dashboard_alerts),
                "compliance_report": pool.submit(self.converge.compliance_report),
                "reviews_summary": pool.submit(self.converge.reviews_summary),
                "gate": pool.submit(self.converge.risk_gate_report),
            }
            if self.settings.data_mode != "demo":
                futures["health"] = pool.submit(self.converge.health)
            # Resolve operations while converge calls execute
            operations_bundle = self._resolve_operations(state_bundle)
            # Collect results
            results: dict[str, Any] = {}
            for key, future in futures.items():
                try:
                    results[key] = future.result()
                except Exception:
                    results[key] = None
        summary = results["summary"]
        dashboard = results["dashboard"]
        dashboard_alerts = results["dashboard_alerts"]
        compliance_report = results["compliance_report"]
        reviews_summary = results["reviews_summary"]
        gate = results["gate"]
        converge_health = results.get("health")
        services = build_services(state_bundle, summary, converge_health, data_mode=self.settings.data_mode)
        counts = state_bundle["payload"]["counts"]
        blocked = operations_bundle["payload"]["blocked"]
        alerts = build_alerts(
            services,
            blocked,
            state_bundle["source"],
            dashboard_alerts=dashboard_alerts,
            compliance_report=compliance_report,
        )

        block_rate = None
        if isinstance(gate, dict):
            block_rate = gate.get("block_rate")
        if block_rate is None:
            block_rate = round(counts.get("blocked", 0) / max(counts.get("merged", 0) + counts.get("blocked", 0), 1), 3)

        payload = {
            "services": services,
            "counts": counts,
            "kpis": {
                "running": counts.get("running", 0),
                "blocked": counts.get("blocked", 0),
                "retry_pending": counts.get("retry_pending", 0),
                "merged": counts.get("merged", 0),
                "failed": counts.get("failed", 0),
                "uptime_seconds": state_bundle["payload"].get("uptime_seconds", 0),
                "block_rate": block_rate,
                "open_reviews": summary_value(reviews_summary, "open_reviews", fallback=0),
                "mergeable_rate": summary_value(compliance_report, "mergeable_rate"),
            },
            "alerts": alerts,
            "top_blockers": blocked[:3],
            "queue_health": summary.get("queue") if isinstance(summary, dict) else None,
            "converge_dashboard": dashboard,
            "review_summary": reviews_summary,
            "compliance": compliance_report,
            "generated_at": state_bundle["payload"].get("generated_at"),
            "data_source": state_bundle["source"],
        }
        self.cache.set("overview", payload)
        return payload

    def get_operations(self) -> dict[str, Any]:
        state_bundle = self.provider.resolve_state()
        operations_bundle = self._resolve_operations(state_bundle)
        payload = operations_bundle["payload"]
        self.cache.set("operations", payload)
        return payload

    def list_jobs(self) -> dict[str, Any]:
        operations = self.get_operations()
        jobs = operations["running"] + operations["retry_queue"] + operations["blocked"]
        jobs.sort(key=lambda item: (item.get("status", ""), item.get("job_id", "")))
        return {
            "items": jobs,
            "generated_at": operations["generated_at"],
            "data_source": operations["data_source"],
            "filters": operations["filters"],
        }

    def get_job_detail(self, job_id: str) -> dict[str, Any]:
        orchestrator_job, source = self.provider.get_job_payload(job_id)
        if orchestrator_job is None:
            cached = self.cache.get(f"job:{job_id}")
            if cached is not None:
                payload = dict(cached.payload)
                payload["data_source"] = "stale-cache"
                return payload
            return {
                "job": None,
                "timeline": [],
                "intent": None,
                "risk_review": None,
                "operator_actions": operator_actions(job=None, intent=None),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "demo",
                "error": f"Unknown job: {job_id}",
            }

        job = orchestrator_job.get("job", {})
        timeline = orchestrator_job.get("timeline", [])
        intent_id = job.get("intent_id")
        intent_bundle = self.provider.get_intent_bundle(intent_id) if intent_id else None
        payload = {
            "job": job,
            "timeline": timeline,
            "intent": intent_bundle["intent"] if intent_bundle else None,
            "intent_events": intent_bundle["events"] if intent_bundle else [],
            "risk_review": intent_bundle["risk_review"] if intent_bundle else None,
            "reviews": intent_bundle["reviews"] if intent_bundle else [],
            "review_summary": intent_bundle["review_summary"] if intent_bundle else None,
            "compliance_report": intent_bundle["compliance_report"] if intent_bundle else None,
            "operator_actions": operator_actions(job=job, intent=intent_bundle["intent"] if intent_bundle else None),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": source if intent_bundle is None else merge_source(source, intent_bundle["data_source"]),
        }
        self.cache.set(f"job:{job_id}", payload)
        return payload

    def get_intent_detail(self, intent_id: str) -> dict[str, Any]:
        intent_bundle = self.provider.get_intent_bundle(intent_id)
        if intent_bundle is None:
            cached = self.cache.get(f"intent:{intent_id}")
            if cached is not None:
                payload = dict(cached.payload)
                payload["data_source"] = "stale-cache"
                return payload
            return {
                "intent": None,
                "events": [],
                "risk_review": None,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "demo",
                "error": f"Unknown intent: {intent_id}",
            }
        payload = {
            "intent": intent_bundle["intent"],
            "events": intent_bundle["events"],
            "risk_review": intent_bundle["risk_review"],
            "reviews": intent_bundle["reviews"],
            "review_summary": intent_bundle["review_summary"],
            "compliance_report": intent_bundle["compliance_report"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": intent_bundle["data_source"],
        }
        self.cache.set(f"intent:{intent_id}", payload)
        return payload

    def get_reviews(self) -> dict[str, Any]:
        reviews, summary, source = self.provider.get_reviews_payload()
        payload = {
            "items": reviews,
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": source,
        }
        self.cache.set("reviews", payload)
        return payload

    def get_compliance(self) -> dict[str, Any]:
        report, alerts, source = self.provider.get_compliance_payload()
        payload = {
            "report": report,
            "alerts": alerts,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": source,
        }
        self.cache.set("compliance", payload)
        return payload

    def refresh(self) -> dict[str, Any]:
        return self.actions.refresh()

    def retry_job(self, job_id: str) -> dict[str, Any]:
        return self.actions.retry_job(job_id)

    def request_review(
        self,
        *,
        intent_id: str,
        trigger: str = "policy",
        reviewer: str | None = None,
        priority: int | None = None,
    ) -> dict[str, Any]:
        return self.actions.request_review(
            intent_id=intent_id,
            trigger=trigger,
            reviewer=reviewer,
            priority=priority,
        )

    def assign_review(self, task_id: str, *, reviewer: str) -> dict[str, Any]:
        return self.actions.assign_review(task_id, reviewer=reviewer)

    def complete_review(self, task_id: str, *, resolution: str = "approved", notes: str = "") -> dict[str, Any]:
        return self.actions.complete_review(task_id, resolution=resolution, notes=notes)

    def escalate_review(self, task_id: str, *, reason: str = "sla_breach") -> dict[str, Any]:
        return self.actions.escalate_review(task_id, reason=reason)

    def cancel_review(self, task_id: str, *, reason: str = "") -> dict[str, Any]:
        return self.actions.cancel_review(task_id, reason=reason)

    def _resolve_operations(self, state_bundle: dict[str, Any]) -> dict[str, Any]:
        state = state_bundle["payload"]
        jobs_by_id = self.provider.seed_jobs_for_source(state_bundle["source"])
        for collection_name in ("running", "retry_queue", "blocked"):
            for item in state.get(collection_name, []):
                job_id = item.get("job_id")
                if not job_id:
                    continue
                if job_id not in jobs_by_id and state_bundle["source"] == "real":
                    real_job = self.orchestrator.get_job(job_id)
                    if isinstance(real_job, dict) and real_job.get("job"):
                        jobs_by_id[job_id] = real_job
                        continue
                if job_id not in jobs_by_id and state_bundle["source"] != "real":
                    demo_job, _ = self.provider.get_job_payload(job_id)
                    if demo_job is not None:
                        jobs_by_id[job_id] = demo_job

        running = [self._normalize_job_card(item.get("job_id"), "running", item, jobs_by_id) for item in state.get("running", [])]
        retry_queue = [self._normalize_job_card(item.get("job_id"), "retry_pending", item, jobs_by_id) for item in state.get("retry_queue", [])]
        blocked = [self._normalize_job_card(item.get("job_id"), "blocked", item, jobs_by_id) for item in state.get("blocked", [])]
        payload = {
            "running": running,
            "retry_queue": retry_queue,
            "blocked": blocked,
            "recent_events": recent_events(jobs_by_id),
            "filters": {
                "status": sorted({item["status"] for item in running + retry_queue + blocked}),
                "agent": sorted({item["agent"] for item in running + retry_queue + blocked if item.get("agent")}),
                "risk_level": sorted({item["risk_level"] for item in running + retry_queue + blocked if item.get("risk_level")}),
                "source": [state_bundle["source"]],
            },
            "generated_at": state.get("generated_at"),
            "data_source": state_bundle["source"],
        }
        return {"payload": payload, "source": state_bundle["source"]}

    def _normalize_job_card(
        self,
        job_id: str | None,
        status: str,
        state_item: dict[str, Any],
        jobs_by_id: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        job_detail = jobs_by_id.get(job_id or "", {})
        job = job_detail.get("job", {})
        intent_id = job.get("intent_id")
        intent_bundle = self.provider.get_intent_bundle(intent_id) if intent_id else None
        risk = intent_bundle["risk_review"]["risk"] if intent_bundle and isinstance(intent_bundle.get("risk_review"), dict) else {}
        return {
            "job_id": job_id,
            "trace_id": job.get("trace_id"),
            "agent": job.get("agent") or state_item.get("agent"),
            "attempt": job.get("attempts", state_item.get("attempt")),
            "status": status,
            "risk_level": risk.get("risk_level") or job.get("risk_level"),
            "risk_score": risk.get("risk_score") or job.get("risk_score"),
            "reason": job.get("error") or state_item.get("error") or state_item.get("reason"),
            "started_at": job.get("claimed_at") or state_item.get("started_at") or job.get("created_at"),
            "last_activity_at": job.get("last_activity_at") or state_item.get("last_activity_at"),
            "idle_seconds": state_item.get("idle_seconds"),
            "next_retry_at": state_item.get("next_retry_at") or job.get("retry_at"),
            "seconds_until_retry": state_item.get("seconds_until_retry"),
            "intent_id": intent_id,
            "prompt_preview": state_item.get("prompt_preview") or job.get("prompt"),
            "source_branch": job.get("source_branch") or state_item.get("branch"),
            "data_source": "real" if job_detail else "demo",
        }


_service: ControlPlaneService | None = None


def get_control_plane_service() -> ControlPlaneService:
    global _service
    if _service is None:
        _service = ControlPlaneService(load_settings())
    return _service
