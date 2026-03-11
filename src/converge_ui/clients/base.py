from __future__ import annotations

import time
from typing import Any

import httpx

from converge_ui.logging import upstream_call
from converge_ui.observability import upstream_latency

_RETRIABLE_STATUS_CODES = frozenset({502, 503, 504})


class ApiClient:
    service_name: str = "unknown"

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 1.5,
        retries: int = 1,
        retry_delay: float = 0.3,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.retry_delay = retry_delay

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        url = f"{self.base_url}{path}"
        start = time.monotonic()

        for attempt in range(1 + self.retries):
            try:
                response = httpx.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    timeout=self.timeout_seconds,
                )
                if response.status_code in _RETRIABLE_STATUS_CODES and attempt < self.retries:
                    time.sleep(self.retry_delay)
                    continue
                response.raise_for_status()
                duration = time.monotonic() - start
                upstream_latency.observe(duration, service=self.service_name, method=method, path=path)
                upstream_call(
                    self.service_name,
                    method,
                    path,
                    status=response.status_code,
                    duration_ms=duration * 1000,
                )
                return response.json()
            except (httpx.ConnectError, httpx.ReadTimeout) as exc:
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
                    continue
                duration = time.monotonic() - start
                upstream_latency.observe(duration, service=self.service_name, method=method, path=path)
                upstream_call(
                    self.service_name,
                    method,
                    path,
                    status=None,
                    duration_ms=duration * 1000,
                    error=str(exc),
                )
                return None
            except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
                duration = time.monotonic() - start
                upstream_latency.observe(duration, service=self.service_name, method=method, path=path)
                upstream_call(
                    self.service_name,
                    method,
                    path,
                    status=None,
                    duration_ms=duration * 1000,
                    error=str(exc),
                )
                return None

        return None

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        return self._request("GET", path, params=params)

    def _post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        return self._request("POST", path, json=json)
