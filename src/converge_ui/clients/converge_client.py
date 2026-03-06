from __future__ import annotations

from typing import Any

from converge_ui.clients.base import ApiClient


class ConvergeClient(ApiClient):
    service_name = "converge"
    def is_reachable(self) -> bool:
        return self.health() is not None

    def health(self) -> dict[str, Any] | None:
        payload = self._get("/health")
        return payload if isinstance(payload, dict) else None

    def summary(self) -> dict[str, Any] | None:
        payload = self._get("/summary")
        return payload if isinstance(payload, dict) else None

    def dashboard(self) -> dict[str, Any] | None:
        payload = self._get("/dashboard")
        return payload if isinstance(payload, dict) else None

    def dashboard_alerts(self) -> dict[str, Any] | None:
        payload = self._get("/dashboard/alerts")
        return payload if isinstance(payload, dict) else None

    def risk_gate_report(self) -> dict[str, Any] | None:
        payload = self._get("/risk/gate/report")
        return payload if isinstance(payload, dict) else None

    def compliance_report(self) -> dict[str, Any] | None:
        payload = self._get("/compliance/report")
        return payload if isinstance(payload, dict) else None

    def compliance_alerts(self) -> list[dict[str, Any]]:
        payload = self._get("/compliance/alerts")
        return payload if isinstance(payload, list) else []

    def reviews(self, *, intent_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {}
        if intent_id:
            params["intent_id"] = intent_id
        if status:
            params["status"] = status
        payload = self._get("/reviews", params=params or None)
        if isinstance(payload, dict):
            reviews = payload.get("reviews")
            return reviews if isinstance(reviews, list) else []
        return []

    def reviews_summary(self) -> dict[str, Any] | None:
        payload = self._get("/reviews/summary")
        return payload if isinstance(payload, dict) else None

    def get_intent(self, intent_id: str) -> dict[str, Any] | None:
        payload = self._get(f"/intents/{intent_id}")
        return payload if isinstance(payload, dict) else None

    def get_intent_events(self, intent_id: str) -> list[dict[str, Any]]:
        payload = self._get(f"/intents/{intent_id}/events")
        return payload if isinstance(payload, list) else []

    def get_risk_review(self, intent_id: str) -> dict[str, Any] | None:
        payload = self._get("/risk/review", params={"intent_id": intent_id})
        return payload if isinstance(payload, dict) else None

    def request_review(
        self,
        *,
        intent_id: str,
        trigger: str = "policy",
        reviewer: str | None = None,
        priority: int | None = None,
    ) -> dict[str, Any] | None:
        payload = self._post(
            "/reviews",
            json={
                "intent_id": intent_id,
                "trigger": trigger,
                "reviewer": reviewer,
                "priority": priority,
            },
        )
        return payload if isinstance(payload, dict) else None

    def assign_review(self, task_id: str, *, reviewer: str) -> dict[str, Any] | None:
        payload = self._post(f"/reviews/{task_id}/assign", json={"reviewer": reviewer})
        return payload if isinstance(payload, dict) else None

    def complete_review(
        self,
        task_id: str,
        *,
        resolution: str = "approved",
        notes: str = "",
    ) -> dict[str, Any] | None:
        payload = self._post(
            f"/reviews/{task_id}/complete",
            json={"resolution": resolution, "notes": notes},
        )
        return payload if isinstance(payload, dict) else None

    def escalate_review(self, task_id: str, *, reason: str = "sla_breach") -> dict[str, Any] | None:
        payload = self._post(f"/reviews/{task_id}/escalate", json={"reason": reason})
        return payload if isinstance(payload, dict) else None

    def cancel_review(self, task_id: str, *, reason: str = "") -> dict[str, Any] | None:
        payload = self._post(f"/reviews/{task_id}/cancel", json={"reason": reason})
        return payload if isinstance(payload, dict) else None
