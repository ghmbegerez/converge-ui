from __future__ import annotations

from typing import Any

from converge_ui.clients.base import ApiClient


class ConvergeClient(ApiClient):
    def is_reachable(self) -> bool:
        return self.health() is not None

    def health(self) -> dict[str, Any] | None:
        payload = self._get("/health")
        return payload if isinstance(payload, dict) else None

    def summary(self) -> dict[str, Any] | None:
        payload = self._get("/summary")
        return payload if isinstance(payload, dict) else None

    def risk_gate_report(self) -> dict[str, Any] | None:
        payload = self._get("/risk/gate/report")
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
