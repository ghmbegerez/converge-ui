from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any


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
