"""Structured JSON logging for converge-ui.

Same pattern as orchestrator's logging module: single-line JSON to stderr.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


def emit(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    level: str = "info",
) -> None:
    """Write a structured JSON event to stderr."""
    record: dict[str, Any] = {
        "event": event_type,
        "level": level,
        "ts": datetime.now(UTC).isoformat(),
    }
    if payload:
        record.update(payload)
    sys.stderr.write(json.dumps(record, default=str) + "\n")
    sys.stderr.flush()


def request_received(method: str, path: str) -> None:
    emit("http.request", {"method": method, "path": path}, level="debug")


def request_completed(
    method: str, path: str, status_code: int, duration_ms: float
) -> None:
    lvl = "info" if status_code < 400 else "warn" if status_code < 500 else "error"
    emit(
        "http.response",
        {
            "method": method,
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 1),
        },
        level=lvl,
    )


def upstream_call(
    service: str,
    method: str,
    path: str,
    status: int | None,
    duration_ms: float,
    error: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "service": service,
        "method": method,
        "path": path,
        "duration_ms": round(duration_ms, 1),
    }
    if status is not None:
        payload["status"] = status
    if error is not None:
        payload["error"] = error
    emit("upstream.call", payload, level="warn" if error else "debug")


def app_started(host: str, port: int) -> None:
    emit("app.started", {"host": host, "port": port})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, and duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.monotonic()
        request_received(request.method, request.url.path)
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000
        request_completed(
            request.method, request.url.path, response.status_code, duration_ms
        )
        return response
