from __future__ import annotations

import math
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


# ---------------------------------------------------------------------------
# Histogram — tracks upstream latency distributions
# ---------------------------------------------------------------------------

_HISTOGRAM_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, math.inf)


class Histogram:
    """Minimal Prometheus-style histogram (no external dependency)."""

    def __init__(self, name: str, help_text: str, labels: tuple[str, ...] = ()) -> None:
        self.name = name
        self.help_text = help_text
        self.labels = labels
        self._lock = Lock()
        # key: tuple of label values -> (bucket_counts, sum, count)
        self._series: dict[tuple[str, ...], dict[str, Any]] = {}

    def observe(self, value: float, **label_values: str) -> None:
        key = tuple(label_values.get(l, "") for l in self.labels)
        with self._lock:
            if key not in self._series:
                self._series[key] = {
                    "buckets": [0] * len(_HISTOGRAM_BUCKETS),
                    "sum": 0.0,
                    "count": 0,
                }
            entry = self._series[key]
            entry["sum"] += value
            entry["count"] += 1
            for i, bound in enumerate(_HISTOGRAM_BUCKETS):
                if value <= bound:
                    entry["buckets"][i] += 1

    def render(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            for key, entry in sorted(self._series.items()):
                label_str = ",".join(
                    f'{l}="{v}"' for l, v in zip(self.labels, key) if v
                )
                label_prefix = "{" + label_str + "}" if label_str else ""
                cumulative = 0
                for i, bound in enumerate(_HISTOGRAM_BUCKETS):
                    cumulative += entry["buckets"][i]
                    le = "+Inf" if math.isinf(bound) else str(bound)
                    lines.append(
                        f'{self.name}_bucket{{le="{le}",{label_str}}} {cumulative}'
                        if label_str
                        else f'{self.name}_bucket{{le="{le}"}} {cumulative}'
                    )
                lines.append(f"{self.name}_sum{label_prefix} {entry['sum']:.6f}")
                lines.append(f"{self.name}_count{label_prefix} {entry['count']}")
        return lines


# ---------------------------------------------------------------------------
# Global instances
# ---------------------------------------------------------------------------

_stats = RuntimeStats()

upstream_latency = Histogram(
    "converge_ui_upstream_latency_seconds",
    "Latency of upstream service calls in seconds",
    labels=("service", "method", "path"),
)

# Dedicated counters for cache and data source tracking
_cache_counters: Counter[str] = Counter()
_cache_lock = Lock()

_source_counters: Counter[str] = Counter()
_source_lock = Lock()


def stats() -> RuntimeStats:
    return _stats


def record_cache_hit(service: str) -> None:
    with _cache_lock:
        _cache_counters[f"hit:{service}"] += 1


def record_cache_miss(service: str) -> None:
    with _cache_lock:
        _cache_counters[f"miss:{service}"] += 1


def record_data_source(source: str) -> None:
    with _source_lock:
        _source_counters[source] += 1


def render_prometheus() -> str:
    lines = [
        "# HELP converge_ui_runtime_counter Internal converge-ui counters",
        "# TYPE converge_ui_runtime_counter counter",
    ]
    for key, value in sorted(_stats.snapshot().items()):
        escaped = key.replace("\\", "\\\\").replace("\"", "\\\"")
        lines.append(f'converge_ui_runtime_counter{{key="{escaped}"}} {value}')

    # Upstream latency histogram
    lines.extend(upstream_latency.render())

    # Cache hit/miss counters
    lines.append("# HELP converge_ui_cache_hit_total Cache hits by service")
    lines.append("# TYPE converge_ui_cache_hit_total counter")
    lines.append("# HELP converge_ui_cache_miss_total Cache misses by service")
    lines.append("# TYPE converge_ui_cache_miss_total counter")
    with _cache_lock:
        for key, value in sorted(_cache_counters.items()):
            kind, service = key.split(":", 1)
            metric = f"converge_ui_cache_{kind}_total"
            lines.append(f'{metric}{{service="{service}"}} {value}')

    # Data source counters
    lines.append("# HELP converge_ui_data_source_total Requests served by data source")
    lines.append("# TYPE converge_ui_data_source_total counter")
    with _source_lock:
        for source, value in sorted(_source_counters.items()):
            lines.append(f'converge_ui_data_source_total{{source="{source}"}} {value}')

    return "\n".join(lines) + "\n"
