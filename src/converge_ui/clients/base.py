from __future__ import annotations

import time
from typing import Any

import httpx

from converge_ui.logging import upstream_call


class ApiClient:
    service_name: str = "unknown"

    def __init__(self, base_url: str, timeout_seconds: float = 1.5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        start = time.monotonic()
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            upstream_call(
                self.service_name, "GET", path,
                status=response.status_code,
                duration_ms=(time.monotonic() - start) * 1000,
            )
            return response.json()
        except Exception as exc:
            upstream_call(
                self.service_name, "GET", path,
                status=None,
                duration_ms=(time.monotonic() - start) * 1000,
                error=str(exc),
            )
            return None

    def _post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        start = time.monotonic()
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                json=json,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            upstream_call(
                self.service_name, "POST", path,
                status=response.status_code,
                duration_ms=(time.monotonic() - start) * 1000,
            )
            return response.json()
        except Exception as exc:
            upstream_call(
                self.service_name, "POST", path,
                status=None,
                duration_ms=(time.monotonic() - start) * 1000,
                error=str(exc),
            )
            return None
