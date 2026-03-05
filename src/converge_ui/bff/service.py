from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from converge_ui.bff.demo_data import get_demo_intent, get_demo_job, get_demo_jobs, get_demo_state
from converge_ui.clients.converge_client import ConvergeClient
from converge_ui.clients.orchestrator_client import OrchestratorClient
from converge_ui.config.settings import Settings, load_settings


@dataclass
class CacheEntry:
    payload: dict[str, Any]
    cached_at: str


class SnapshotCache:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def set(self, key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = CacheEntry(
                payload=payload,
                cached_at=datetime.now(timezone.utc).isoformat(),
            )

    def get(self, key: str) -> CacheEntry | None:
        with self._lock:
            return self._entries.get(key)


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
        self.cache = cache or SnapshotCache()

    def get_overview(self) -> dict[str, Any]:
        state_bundle = self._resolve_state()
        operations_bundle = self._resolve_operations(state_bundle)
        summary = self.converge.summary()
        gate = self.converge.risk_gate_report()
        services = self._build_services(state_bundle, summary)
        counts = state_bundle["payload"]["counts"]
        blocked = operations_bundle["payload"]["blocked"]
        alerts = self._build_alerts(services, blocked, state_bundle["source"])

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
            },
            "alerts": alerts,
            "top_blockers": blocked[:3],
            "generated_at": state_bundle["payload"].get("generated_at"),
            "data_source": state_bundle["source"],
        }
        self.cache.set("overview", payload)
        return payload

    def get_operations(self) -> dict[str, Any]:
        state_bundle = self._resolve_state()
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
        orchestrator_job = self.orchestrator.get_job(job_id)
        source = "real"
        if orchestrator_job is None:
            orchestrator_job = get_demo_job(job_id)
            source = "demo"
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
                "operator_actions": self._operator_actions(job=None, intent=None),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "data_source": "demo",
                "error": f"Unknown job: {job_id}",
            }

        job = orchestrator_job.get("job", {})
        timeline = orchestrator_job.get("timeline", [])
        intent_id = job.get("intent_id")
        intent_bundle = self._get_intent_bundle(intent_id) if intent_id else None
        payload = {
            "job": job,
            "timeline": timeline,
            "intent": intent_bundle["intent"] if intent_bundle else None,
            "intent_events": intent_bundle["events"] if intent_bundle else [],
            "risk_review": intent_bundle["risk_review"] if intent_bundle else None,
            "operator_actions": self._operator_actions(job=job, intent=intent_bundle["intent"] if intent_bundle else None),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": source if intent_bundle is None else self._merge_source(source, intent_bundle["data_source"]),
        }
        self.cache.set(f"job:{job_id}", payload)
        return payload

    def get_intent_detail(self, intent_id: str) -> dict[str, Any]:
        intent_bundle = self._get_intent_bundle(intent_id)
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
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_source": intent_bundle["data_source"],
        }
        self.cache.set(f"intent:{intent_id}", payload)
        return payload

    def refresh(self) -> dict[str, Any]:
        response = self.orchestrator.refresh()
        if response is not None:
            payload = {
                "status": response.get("status", "ok"),
                "note": response.get("note", ""),
                "data_source": "real",
            }
            self.cache.set("refresh", payload)
            return payload
        return {
            "status": "unavailable",
            "note": "Refresh endpoint unavailable in current mode.",
            "data_source": "demo",
        }

    def retry_job(self, job_id: str) -> dict[str, Any]:
        response = self.orchestrator.retry_job(job_id)
        if response is not None:
            return {
                "status": response.get("status", "ok"),
                "job_id": job_id,
                "reason": response.get("reason", ""),
                "enabled": True,
                "data_source": "real",
            }
        return {
            "status": "disabled",
            "job_id": job_id,
            "reason": "Retry is not exposed by the current orchestrator API.",
            "enabled": False,
            "data_source": "demo",
        }

    def _resolve_state(self) -> dict[str, Any]:
        real_state = None if self.settings.data_mode == "demo" else self.orchestrator.state()
        if real_state is not None:
            payload = {"payload": real_state, "source": "real"}
            self.cache.set("state", payload)
            return payload
        cached = self.cache.get("state")
        if cached is not None and self.settings.data_mode != "demo":
            payload = dict(cached.payload)
            payload["source"] = "stale-cache"
            return payload
        demo_state = get_demo_state()
        return {"payload": demo_state, "source": "demo"}

    def _resolve_operations(self, state_bundle: dict[str, Any]) -> dict[str, Any]:
        state = state_bundle["payload"]
        jobs_by_id = self._seed_jobs_for_source(state_bundle["source"])
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
                    demo_job = get_demo_job(job_id)
                    if demo_job is not None:
                        jobs_by_id[job_id] = demo_job

        running = [self._normalize_job_card(item.get("job_id"), "running", item, jobs_by_id) for item in state.get("running", [])]
        retry_queue = [self._normalize_job_card(item.get("job_id"), "retry_pending", item, jobs_by_id) for item in state.get("retry_queue", [])]
        blocked = [self._normalize_job_card(item.get("job_id"), "blocked", item, jobs_by_id) for item in state.get("blocked", [])]
        payload = {
            "running": running,
            "retry_queue": retry_queue,
            "blocked": blocked,
            "recent_events": self._recent_events(jobs_by_id),
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

    def _seed_jobs_for_source(self, source: str) -> dict[str, dict[str, Any]]:
        if source == "real":
            return {}
        return {item["job"]["id"]: item for item in get_demo_jobs()}

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
        intent_bundle = self._get_intent_bundle(intent_id) if intent_id else None
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

    def _build_services(self, state_bundle: dict[str, Any], summary: dict[str, Any] | None) -> dict[str, Any]:
        orch_source = state_bundle["source"]
        orch_payload = state_bundle["payload"]
        converge_health = None if self.settings.data_mode == "demo" else self.converge.health()
        return {
            "orchestrator": {
                "reachable": orch_source == "real" and bool(orch_payload),
                "mode": orch_source,
                "last_check_at": orch_payload.get("generated_at"),
            },
            "converge": {
                "reachable": converge_health is not None,
                "mode": "real" if converge_health is not None else ("demo" if self.settings.data_mode == "demo" else "partial"),
                "last_check_at": datetime.now(timezone.utc).isoformat(),
                "summary_available": summary is not None,
            },
        }

    def _build_alerts(self, services: dict[str, Any], blocked: list[dict[str, Any]], source: str) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        if not services["orchestrator"]["reachable"]:
            alerts.append({"code": "service_down", "severity": "high", "title": "Orchestrator unavailable", "source": source})
        if not services["converge"]["reachable"]:
            alerts.append({"code": "service_down", "severity": "medium", "title": "Converge unavailable", "source": source})
        if source == "stale-cache":
            alerts.append({"code": "stale_data", "severity": "medium", "title": "Showing last known snapshot", "source": source})
        if any((item.get("risk_level") in {"high", "critical"}) for item in blocked):
            alerts.append({"code": "blocked_high_risk", "severity": "critical", "title": "High-risk blocked work requires review", "source": source})
        return alerts

    def _recent_events(self, jobs_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for item in jobs_by_id.values():
            for event in item.get("timeline", [])[-2:]:
                events.append({
                    "job_id": event.get("job_id"),
                    "trace_id": event.get("trace_id"),
                    "from_state": event.get("from_state"),
                    "to_state": event.get("to_state"),
                    "reason": event.get("reason"),
                    "timestamp": event.get("timestamp"),
                })
        events.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
        return events[:10]

    def _get_intent_bundle(self, intent_id: str | None) -> dict[str, Any] | None:
        if not intent_id:
            return None
        intent = None if self.settings.data_mode == "demo" else self.converge.get_intent(intent_id)
        events = [] if self.settings.data_mode == "demo" else self.converge.get_intent_events(intent_id)
        risk_review = None if self.settings.data_mode == "demo" else self.converge.get_risk_review(intent_id)
        if intent is not None:
            return {
                "intent": intent,
                "events": events,
                "risk_review": risk_review,
                "data_source": "real",
            }
        demo = get_demo_intent(intent_id)
        if demo is not None:
            return {
                "intent": demo["intent"],
                "events": demo["events"],
                "risk_review": demo["risk_review"],
                "data_source": "demo",
            }
        return None

    def _operator_actions(self, job: dict[str, Any] | None, intent: dict[str, Any] | None) -> dict[str, Any]:
        retry_enabled = bool(job and job.get("status") in {"blocked", "retry_pending", "failed"})
        return {
            "refresh": {"enabled": True, "label": "Refresh"},
            "retry": {
                "enabled": retry_enabled,
                "label": "Retry job",
                "reason": None if retry_enabled else "Retry available only for blocked or retry-pending jobs.",
            },
            "view_intent": {
                "enabled": bool(intent),
                "label": "Open intent",
                "reason": None if intent else "No converge intent linked to this job.",
            },
        }

    def _merge_source(self, left: str, right: str) -> str:
        if left == right:
            return left
        if "stale-cache" in {left, right}:
            return "stale-cache"
        if "demo" in {left, right}:
            return "demo"
        return "real"


_service: ControlPlaneService | None = None


def get_control_plane_service() -> ControlPlaneService:
    global _service
    if _service is None:
        _service = ControlPlaneService(load_settings())
    return _service
