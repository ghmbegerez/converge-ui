from __future__ import annotations

from collections import Counter
from threading import Lock
from typing import Any


class RuntimeStats:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: Counter[str] = Counter()

    def inc(self, key: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[key] += amount

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._counters)

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()


_stats = RuntimeStats()


def stats() -> RuntimeStats:
    return _stats


def render_prometheus() -> str:
    lines = [
        "# HELP converge_ui_runtime_counter Internal converge-ui counters",
        "# TYPE converge_ui_runtime_counter counter",
    ]
    for key, value in sorted(_stats.snapshot().items()):
        escaped = key.replace("\\", "\\\\").replace("\"", "\\\"")
        lines.append(f'converge_ui_runtime_counter{{key="{escaped}"}} {value}')
    return "\n".join(lines) + "\n"
