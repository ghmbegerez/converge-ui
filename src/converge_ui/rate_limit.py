"""Sliding-window rate limiter for converge-ui."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from converge_ui.logging import emit

EXEMPT_PREFIXES: tuple[str, ...] = ("/health/", "/assets")


class SlidingWindowCounter:
    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            entries = self._buckets[key]
            self._buckets[key] = [t for t in entries if t > cutoff]
            if len(self._buckets[key]) >= self.max_requests:
                return False
            self._buckets[key].append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            entries = [t for t in self._buckets.get(key, []) if t > cutoff]
            return max(0, self.max_requests - len(entries))


_limiter: SlidingWindowCounter | None = None
_enabled: bool = False


def init_rate_limit(*, enabled: bool, max_requests: int) -> None:
    global _limiter, _enabled
    _enabled = enabled
    _limiter = SlidingWindowCounter(max_requests=max_requests)


def check_rate_limit(key: str, path: str) -> bool:
    if not _enabled or _limiter is None:
        return True
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return True
    allowed = _limiter.allow(key)
    if not allowed:
        emit("rate_limit.exceeded", {"key": key, "path": path}, level="warn")
    return allowed


def get_remaining(key: str) -> int:
    if _limiter is None:
        return 999
    return _limiter.remaining(key)
