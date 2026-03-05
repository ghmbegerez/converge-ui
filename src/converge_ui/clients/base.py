from __future__ import annotations

from typing import Any

import httpx


class ApiClient:
    def __init__(self, base_url: str, timeout_seconds: float = 1.5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                params=params,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def _post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any] | list[Any] | None:
        try:
            response = httpx.post(
                f"{self.base_url}{path}",
                json=json,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
