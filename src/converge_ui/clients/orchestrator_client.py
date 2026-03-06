from __future__ import annotations

from typing import Any

from converge_ui.clients.base import ApiClient


class OrchestratorClient(ApiClient):
    service_name = "orchestrator"
    def is_reachable(self) -> bool:
        return self.health() is not None

    def health(self) -> dict[str, Any] | None:
        payload = self._get("/api/v1/health")
        return payload if isinstance(payload, dict) else None

    def state(self) -> dict[str, Any] | None:
        payload = self._get("/api/v1/state")
        return payload if isinstance(payload, dict) else None

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        payload = self._get(f"/api/v1/jobs/{job_id}")
        return payload if isinstance(payload, dict) else None

    def refresh(self) -> dict[str, Any] | None:
        payload = self._post("/api/v1/refresh")
        return payload if isinstance(payload, dict) else None

    def retry_job(self, job_id: str) -> dict[str, Any] | None:
        payload = self._post(f"/api/v1/jobs/{job_id}/retry")
        return payload if isinstance(payload, dict) else None
