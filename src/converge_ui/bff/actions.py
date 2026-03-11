from __future__ import annotations

from typing import Any

from converge_ui.bff.cache import SnapshotCache
from converge_ui.bff.helpers import demo_guard
from converge_ui.clients.converge_client import ConvergeClient
from converge_ui.clients.orchestrator_client import OrchestratorClient
from converge_ui.config.settings import Settings
from converge_ui.observability import stats


class ActionExecutor:
    def __init__(
        self,
        settings: Settings,
        *,
        orchestrator: OrchestratorClient,
        converge: ConvergeClient,
        cache: SnapshotCache,
    ) -> None:
        self.settings = settings
        self.orchestrator = orchestrator
        self.converge = converge
        self.cache = cache

    def _call(self, fn: Any, *args: Any, default: Any = None, **kwargs: Any) -> Any:
        return demo_guard(self.settings, fn, *args, default=default, **kwargs)

    def refresh(self) -> dict[str, Any]:
        response = self.orchestrator.refresh()
        if response is not None:
            stats().inc("actions.refresh.real")
            payload = {
                "status": response.get("status", "ok"),
                "reason": response.get("note", response.get("reason", "")),
                "data_source": "real",
            }
            self.cache.set("refresh", payload)
            return payload
        stats().inc("actions.refresh.demo")
        return {
            "status": "unavailable",
            "reason": "Refresh endpoint unavailable in current mode.",
            "data_source": "demo",
        }

    def retry_job(self, job_id: str) -> dict[str, Any]:
        response = self.orchestrator.retry_job(job_id)
        if response is not None:
            stats().inc("actions.retry.real")
            return {
                "status": response.get("status", "ok"),
                "job_id": job_id,
                "reason": response.get("reason", ""),
                "enabled": True,
                "data_source": "real",
            }
        stats().inc("actions.retry.demo")
        return {
            "status": "disabled",
            "job_id": job_id,
            "reason": "Retry is not exposed by the current orchestrator API.",
            "enabled": False,
            "data_source": "demo",
        }

    def request_review(
        self,
        *,
        intent_id: str,
        trigger: str = "policy",
        reviewer: str | None = None,
        priority: int | None = None,
    ) -> dict[str, Any]:
        response = self._call(
            self.converge.request_review,
            intent_id=intent_id,
            trigger=trigger,
            reviewer=reviewer,
            priority=priority,
        )
        if response is not None:
            stats().inc("actions.review.request.real")
            return {"status": "ok", "review": response, "data_source": "real"}
        stats().inc("actions.review.request.demo")
        return {
            "status": "simulated",
            "review": {
                "task_id": f"review-{intent_id}",
                "intent_id": intent_id,
                "status": "open",
                "reviewer": reviewer,
                "priority": priority,
                "trigger": trigger,
            },
            "data_source": "demo",
        }

    def assign_review(self, task_id: str, *, reviewer: str) -> dict[str, Any]:
        response = self._call(self.converge.assign_review, task_id, reviewer=reviewer)
        if response is not None:
            stats().inc("actions.review.assign.real")
            return {"status": "ok", "review": response, "data_source": "real"}
        stats().inc("actions.review.assign.demo")
        return {
            "status": "simulated",
            "review": {"task_id": task_id, "reviewer": reviewer, "status": "assigned"},
            "data_source": "demo",
        }

    def complete_review(self, task_id: str, *, resolution: str = "approved", notes: str = "") -> dict[str, Any]:
        response = self._call(
            self.converge.complete_review,
            task_id,
            resolution=resolution,
            notes=notes,
        )
        if response is not None:
            stats().inc("actions.review.complete.real")
            return {"status": "ok", "review": response, "data_source": "real"}
        stats().inc("actions.review.complete.demo")
        return {
            "status": "simulated",
            "review": {"task_id": task_id, "status": "completed", "resolution": resolution, "notes": notes},
            "data_source": "demo",
        }

    def escalate_review(self, task_id: str, *, reason: str = "sla_breach") -> dict[str, Any]:
        response = self._call(self.converge.escalate_review, task_id, reason=reason)
        if response is not None:
            stats().inc("actions.review.escalate.real")
            return {"status": "ok", "review": response, "data_source": "real"}
        stats().inc("actions.review.escalate.demo")
        return {
            "status": "simulated",
            "review": {"task_id": task_id, "status": "escalated", "reason": reason},
            "data_source": "demo",
        }

    def cancel_review(self, task_id: str, *, reason: str = "") -> dict[str, Any]:
        response = self._call(self.converge.cancel_review, task_id, reason=reason)
        if response is not None:
            stats().inc("actions.review.cancel.real")
            return {"status": "ok", "review": response, "data_source": "real"}
        stats().inc("actions.review.cancel.demo")
        return {
            "status": "simulated",
            "review": {"task_id": task_id, "status": "cancelled", "reason": reason},
            "data_source": "demo",
        }
