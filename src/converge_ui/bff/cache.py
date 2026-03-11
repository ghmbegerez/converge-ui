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
    def __init__(self, ttl_seconds: float = 120.0) -> None:
        self._entries: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds

    def set(self, key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._entries[key] = CacheEntry(
                payload=payload,
                cached_at=datetime.now(timezone.utc).isoformat(),
            )

    def get(self, key: str) -> CacheEntry | None:
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if self._is_expired(entry):
                del self._entries[key]
                return None
            return entry

    def clear_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        with self._lock:
            expired = [k for k, v in self._entries.items() if self._is_expired(v)]
            for k in expired:
                del self._entries[k]
            return len(expired)

    def _is_expired(self, entry: CacheEntry) -> bool:
        cached_at = datetime.fromisoformat(entry.cached_at)
        age = (datetime.now(timezone.utc) - cached_at).total_seconds()
        return age > self._ttl_seconds
