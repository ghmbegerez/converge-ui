from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, TypeVar

_T = TypeVar("_T")


def demo_guard(settings: Any, fn: Callable[..., _T], *args: Any, default: _T = None, **kwargs: Any) -> _T:  # type: ignore[assignment]
    """Call *fn* unless settings indicate demo mode; return *default* in demo mode."""
    if settings.data_mode == "demo":
        return default
    return fn(*args, **kwargs)


def summary_value(payload: dict[str, Any] | None, key: str, fallback: Any = None) -> Any:
    if not isinstance(payload, dict):
        return fallback
    return payload.get(key, fallback)


def merge_source(left: str, right: str) -> str:
    if left == right:
        return left
    if "stale-cache" in {left, right}:
        return "stale-cache"
    if "demo" in {left, right}:
        return "demo"
    return "real"


def operator_actions(job: dict[str, Any] | None, intent: dict[str, Any] | None) -> dict[str, Any]:
    retry_enabled = bool(job and job.get("status") in {"blocked", "retry_pending", "failed"})
    return {
        "refresh": {
            "enabled": True,
            "label": "Refresh",
            "requires_confirmation": False,
        },
        "retry": {
            "enabled": retry_enabled,
            "label": "Retry job",
            "reason": None if retry_enabled else "Retry available only for blocked or retry-pending jobs.",
            "requires_confirmation": True,
        },
        "view_intent": {
            "enabled": bool(intent),
            "label": "Open intent",
            "reason": None if intent else "No converge intent linked to this job.",
            "requires_confirmation": False,
        },
    }


def review_actions() -> dict[str, Any]:
    """Action metadata for the reviews table."""
    return {
        "assign": {"label": "Assign", "requires_confirmation": False},
        "complete": {"label": "Complete", "requires_confirmation": True},
        "escalate": {"label": "Escalate", "requires_confirmation": True},
        "cancel": {"label": "Cancel", "requires_confirmation": True},
    }


def build_services(
    state_bundle: dict[str, Any],
    summary: dict[str, Any] | None,
    converge_health: dict[str, Any] | None,
    *,
    data_mode: str,
) -> dict[str, Any]:
    orch_source = state_bundle["source"]
    orch_payload = state_bundle["payload"]
    return {
        "orchestrator": {
            "reachable": orch_source == "real" and bool(orch_payload),
            "mode": orch_source,
            "last_check_at": orch_payload.get("generated_at"),
        },
        "converge": {
            "reachable": converge_health is not None,
            "mode": "real" if converge_health is not None else ("demo" if data_mode == "demo" else "partial"),
            "last_check_at": datetime.now(timezone.utc).isoformat(),
            "summary_available": summary is not None,
        },
    }


def build_alerts(
    services: dict[str, Any],
    blocked: list[dict[str, Any]],
    source: str,
    *,
    dashboard_alerts: dict[str, Any] | None = None,
    compliance_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if not services["orchestrator"]["reachable"]:
        alerts.append({"code": "service_down", "severity": "high", "title": "Orchestrator unavailable", "source": source})
    if not services["converge"]["reachable"]:
        alerts.append({"code": "service_down", "severity": "medium", "title": "Converge unavailable", "source": source})
    if source == "stale-cache":
        alerts.append({"code": "stale_data", "severity": "medium", "title": "Showing last known snapshot", "source": source})
    if any((item.get("risk_level") in {"high", "critical"}) for item in blocked):
        alerts.append({"code": "blocked_high_risk", "severity": "critical", "title": "High-risk blocked work requires review", "source": source})
    if isinstance(compliance_report, dict) and compliance_report.get("passed") is False:
        for item in compliance_report.get("alerts", [])[:4]:
            alerts.append({
                "code": item.get("code", "compliance_alert"),
                "severity": item.get("severity", "medium"),
                "title": item.get("title") or item.get("message") or "Compliance alert",
                "source": "converge",
            })
    if isinstance(dashboard_alerts, dict):
        for item in dashboard_alerts.get("alerts", [])[:4]:
            alerts.append({
                "code": item.get("code") or item.get("signal") or "dashboard_alert",
                "severity": item.get("severity", "medium"),
                "title": item.get("title") or item.get("message") or "Dashboard alert",
                "source": item.get("source", "converge"),
            })
    return alerts


def recent_events(jobs_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for item in jobs_by_id.values():
        for event in item.get("timeline", [])[-2:]:
            events.append({
                "job_id": event.get("job_id"),
                "trace_id": event.get("trace_id"),
                "from_state": event.get("from_state"),
                "to_state": event.get("to_state"),
                "reason": event.get("reason"),
                "timestamp": event.get("timestamp"),
            })
    events.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return events[:10]


def review_summary_from_items(reviews: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "open_reviews": len([item for item in reviews if item.get("status") == "open"]),
        "completed_reviews": len([item for item in reviews if item.get("status") == "completed"]),
    }
