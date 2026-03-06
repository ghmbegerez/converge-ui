from __future__ import annotations

from copy import deepcopy


DEMO_STATE = {
    "generated_at": "2026-03-05T12:00:00Z",
    "uptime_seconds": 86400,
    "counts": {
        "queued": 6,
        "claimed": 1,
        "running": 3,
        "evaluated": 1,
        "blocked": 2,
        "retry_pending": 2,
        "merged": 24,
        "failed": 1,
    },
    "running": [
        {
            "job_id": "job-auth-sync",
            "agent": "codex",
            "branch": "orchestrator/codex/auth-sync-9a7d",
            "prompt_preview": "Stabilize auth session rotation and remove duplicate refresh paths.",
            "attempt": 2,
            "started_at": "2026-03-05T11:51:00Z",
            "last_activity_at": "2026-03-05T11:59:52Z",
            "elapsed_seconds": 540,
            "idle_seconds": 8,
        },
        {
            "job_id": "job-risk-budget",
            "agent": "claude",
            "branch": "orchestrator/claude/risk-budget-e1f2",
            "prompt_preview": "Reduce false positives in risk scoring for low-scope refactors.",
            "attempt": 1,
            "started_at": "2026-03-05T11:56:00Z",
            "last_activity_at": "2026-03-05T11:59:57Z",
            "elapsed_seconds": 240,
            "idle_seconds": 3,
        },
        {
            "job_id": "job-ui-pulse",
            "agent": "codex",
            "branch": "orchestrator/codex/ui-pulse-c319",
            "prompt_preview": "Add activity pulse states for the control plane tiles.",
            "attempt": 1,
            "started_at": "2026-03-05T11:58:10Z",
            "last_activity_at": "2026-03-05T11:59:59Z",
            "elapsed_seconds": 110,
            "idle_seconds": 1,
        },
    ],
    "retry_queue": [
        {
            "job_id": "job-merge-rebase",
            "attempt": 2,
            "next_retry_at": "2026-03-05T12:02:10Z",
            "seconds_until_retry": 130,
            "error": "merge_conflict",
        },
        {
            "job_id": "job-tests-flaky",
            "attempt": 3,
            "next_retry_at": "2026-03-05T12:03:45Z",
            "seconds_until_retry": 225,
            "error": "test_failure",
        },
    ],
    "blocked": [
        {
            "job_id": "job-prod-policy",
            "reason": "policy_gate",
            "blocked_since": "2026-03-05T11:31:00Z",
        },
        {
            "job_id": "job-critical-review",
            "reason": "review_required",
            "blocked_since": "2026-03-05T11:12:00Z",
        },
    ],
    "converge": {
        "reachable": True,
        "last_check_at": "2026-03-05T11:59:54Z",
    },
}


DEMO_JOBS = {
    "job-auth-sync": {
        "job": {
            "id": "job-auth-sync",
            "prompt": "Stabilize auth session rotation and remove duplicate refresh paths.",
            "agent": "codex",
            "target_branch": "main",
            "source_branch": "orchestrator/codex/auth-sync-9a7d",
            "intent_id": "intent-auth-sync",
            "status": "running",
            "attempts": 2,
            "max_attempts": 3,
            "created_at": "2026-03-05T11:49:00Z",
            "trace_id": "tr-auth-sync-001",
            "claimed_at": "2026-03-05T11:51:00Z",
            "last_activity_at": "2026-03-05T11:59:52Z",
            "risk_score": 31.5,
            "risk_level": "medium",
            "error": None,
        },
        "timeline": [
            {"job_id": "job-auth-sync", "trace_id": "tr-auth-sync-001", "from_state": "queued", "to_state": "claimed", "reason": "scheduler claim", "timestamp": "2026-03-05T11:50:58Z"},
            {"job_id": "job-auth-sync", "trace_id": "tr-auth-sync-001", "from_state": "claimed", "to_state": "running", "reason": "workspace ready", "timestamp": "2026-03-05T11:51:00Z"},
        ],
    },
    "job-risk-budget": {
        "job": {
            "id": "job-risk-budget",
            "prompt": "Reduce false positives in risk scoring for low-scope refactors.",
            "agent": "claude",
            "target_branch": "main",
            "source_branch": "orchestrator/claude/risk-budget-e1f2",
            "intent_id": "intent-risk-budget",
            "status": "running",
            "attempts": 1,
            "max_attempts": 3,
            "created_at": "2026-03-05T11:55:20Z",
            "trace_id": "tr-risk-budget-003",
            "claimed_at": "2026-03-05T11:56:00Z",
            "last_activity_at": "2026-03-05T11:59:57Z",
            "risk_score": 24.1,
            "risk_level": "low",
            "error": None,
        },
        "timeline": [
            {"job_id": "job-risk-budget", "trace_id": "tr-risk-budget-003", "from_state": "queued", "to_state": "claimed", "reason": "scheduler claim", "timestamp": "2026-03-05T11:55:58Z"},
            {"job_id": "job-risk-budget", "trace_id": "tr-risk-budget-003", "from_state": "claimed", "to_state": "running", "reason": "workspace ready", "timestamp": "2026-03-05T11:56:00Z"},
        ],
    },
    "job-ui-pulse": {
        "job": {
            "id": "job-ui-pulse",
            "prompt": "Add activity pulse states for the control plane tiles.",
            "agent": "codex",
            "target_branch": "main",
            "source_branch": "orchestrator/codex/ui-pulse-c319",
            "intent_id": None,
            "status": "running",
            "attempts": 1,
            "max_attempts": 2,
            "created_at": "2026-03-05T11:57:48Z",
            "trace_id": "tr-ui-pulse-005",
            "claimed_at": "2026-03-05T11:58:10Z",
            "last_activity_at": "2026-03-05T11:59:59Z",
            "risk_score": None,
            "risk_level": None,
            "error": None,
        },
        "timeline": [
            {"job_id": "job-ui-pulse", "trace_id": "tr-ui-pulse-005", "from_state": "queued", "to_state": "claimed", "reason": "scheduler claim", "timestamp": "2026-03-05T11:58:08Z"},
            {"job_id": "job-ui-pulse", "trace_id": "tr-ui-pulse-005", "from_state": "claimed", "to_state": "running", "reason": "workspace ready", "timestamp": "2026-03-05T11:58:10Z"},
        ],
    },
    "job-merge-rebase": {
        "job": {
            "id": "job-merge-rebase",
            "prompt": "Rebase merge-intent after conflict in auth session reducer.",
            "agent": "claude",
            "target_branch": "main",
            "source_branch": "orchestrator/claude/rebase-auth-41cc",
            "intent_id": "intent-merge-rebase",
            "status": "retry_pending",
            "attempts": 2,
            "max_attempts": 4,
            "created_at": "2026-03-05T11:20:00Z",
            "trace_id": "tr-merge-rebase-006",
            "claimed_at": "2026-03-05T11:22:00Z",
            "last_activity_at": "2026-03-05T11:58:22Z",
            "retry_at": "2026-03-05T12:02:10Z",
            "risk_score": 48.0,
            "risk_level": "high",
            "error": "merge_conflict",
        },
        "timeline": [
            {"job_id": "job-merge-rebase", "trace_id": "tr-merge-rebase-006", "from_state": "running", "to_state": "evaluated", "reason": "agent finished", "timestamp": "2026-03-05T11:57:12Z"},
            {"job_id": "job-merge-rebase", "trace_id": "tr-merge-rebase-006", "from_state": "evaluated", "to_state": "blocked", "reason": "merge conflict on converge gate", "timestamp": "2026-03-05T11:58:01Z"},
            {"job_id": "job-merge-rebase", "trace_id": "tr-merge-rebase-006", "from_state": "blocked", "to_state": "retry_pending", "reason": "resolver selected rebase and relaunch", "timestamp": "2026-03-05T11:58:22Z"},
        ],
    },
    "job-tests-flaky": {
        "job": {
            "id": "job-tests-flaky",
            "prompt": "Retry flaky test lane with deterministic fixtures.",
            "agent": "codex",
            "target_branch": "main",
            "source_branch": "orchestrator/codex/tests-fixtures-8da2",
            "intent_id": "intent-tests-flaky",
            "status": "retry_pending",
            "attempts": 3,
            "max_attempts": 4,
            "created_at": "2026-03-05T10:48:00Z",
            "trace_id": "tr-tests-flaky-009",
            "claimed_at": "2026-03-05T11:00:00Z",
            "last_activity_at": "2026-03-05T11:55:10Z",
            "retry_at": "2026-03-05T12:03:45Z",
            "risk_score": 36.3,
            "risk_level": "medium",
            "error": "test_failure",
        },
        "timeline": [
            {"job_id": "job-tests-flaky", "trace_id": "tr-tests-flaky-009", "from_state": "running", "to_state": "retry_pending", "reason": "test failure", "timestamp": "2026-03-05T11:55:12Z"},
        ],
    },
    "job-prod-policy": {
        "job": {
            "id": "job-prod-policy",
            "prompt": "Open a fast path to production branch despite missing security attestations.",
            "agent": "codex",
            "target_branch": "main",
            "source_branch": "orchestrator/codex/policy-fastpath-a922",
            "intent_id": "intent-prod-policy",
            "status": "blocked",
            "attempts": 1,
            "max_attempts": 1,
            "created_at": "2026-03-05T11:05:00Z",
            "trace_id": "tr-prod-policy-010",
            "claimed_at": "2026-03-05T11:06:00Z",
            "last_activity_at": "2026-03-05T11:30:12Z",
            "risk_score": 82.4,
            "risk_level": "critical",
            "error": "policy_gate",
        },
        "timeline": [
            {"job_id": "job-prod-policy", "trace_id": "tr-prod-policy-010", "from_state": "running", "to_state": "evaluated", "reason": "agent finished", "timestamp": "2026-03-05T11:28:11Z"},
            {"job_id": "job-prod-policy", "trace_id": "tr-prod-policy-010", "from_state": "evaluated", "to_state": "blocked", "reason": "policy gate: missing security attestations", "timestamp": "2026-03-05T11:31:00Z"},
        ],
    },
    "job-critical-review": {
        "job": {
            "id": "job-critical-review",
            "prompt": "Patch hot path in payment routing with narrow scope and full audit trail.",
            "agent": "claude",
            "target_branch": "main",
            "source_branch": "orchestrator/claude/payment-route-e911",
            "intent_id": "intent-critical-review",
            "status": "blocked",
            "attempts": 1,
            "max_attempts": 2,
            "created_at": "2026-03-05T10:55:00Z",
            "trace_id": "tr-critical-review-011",
            "claimed_at": "2026-03-05T10:56:00Z",
            "last_activity_at": "2026-03-05T11:10:00Z",
            "risk_score": 67.0,
            "risk_level": "high",
            "error": "review_required",
        },
        "timeline": [
            {"job_id": "job-critical-review", "trace_id": "tr-critical-review-011", "from_state": "evaluated", "to_state": "blocked", "reason": "manual review required for high-risk payment change", "timestamp": "2026-03-05T11:12:00Z"},
        ],
    },
}


DEMO_INTENTS = {
    "intent-auth-sync": {
        "intent": {
            "id": "intent-auth-sync",
            "status": "RUNNING",
            "source": "orchestrator/codex/auth-sync-9a7d",
            "target": "main",
            "risk_level": "medium",
            "priority": "normal",
        },
        "events": [
            {"event_type": "INTENT_CREATED", "timestamp": "2026-03-05T11:51:10Z", "payload": {"source": "orchestrator/codex/auth-sync-9a7d"}},
            {"event_type": "RISK_EVALUATED", "timestamp": "2026-03-05T11:52:02Z", "payload": {"risk_score": 31.5, "risk_level": "medium"}},
        ],
        "risk_review": {
            "intent_id": "intent-auth-sync",
            "risk": {
                "risk_score": 31.5,
                "risk_level": "medium",
                "damage_score": 22,
                "entropy_score": 14,
                "propagation_score": 12,
            },
            "compliance": {"passed": True, "alerts": []},
            "diagnostics": [
                {"code": "session.touchpoints", "title": "Session touches multiple auth paths", "severity": "medium"},
            ],
            "learning": [],
        },
    },
    "intent-risk-budget": {
        "intent": {
            "id": "intent-risk-budget",
            "status": "RUNNING",
            "source": "orchestrator/claude/risk-budget-e1f2",
            "target": "main",
            "risk_level": "low",
            "priority": "normal",
        },
        "events": [
            {"event_type": "INTENT_CREATED", "timestamp": "2026-03-05T11:56:02Z", "payload": {"source": "orchestrator/claude/risk-budget-e1f2"}},
        ],
        "risk_review": {
            "intent_id": "intent-risk-budget",
            "risk": {
                "risk_score": 24.1,
                "risk_level": "low",
                "damage_score": 10,
                "entropy_score": 9,
                "propagation_score": 8,
            },
            "compliance": {"passed": True, "alerts": []},
            "diagnostics": [],
            "learning": [],
        },
    },
    "intent-merge-rebase": {
        "intent": {
            "id": "intent-merge-rebase",
            "status": "REJECTED",
            "source": "orchestrator/claude/rebase-auth-41cc",
            "target": "main",
            "risk_level": "high",
            "priority": "high",
        },
        "events": [
            {"event_type": "POLICY_EVALUATED", "timestamp": "2026-03-05T11:58:01Z", "payload": {"verdict": "BLOCK", "reason": "merge_conflict"}},
        ],
        "risk_review": {
            "intent_id": "intent-merge-rebase",
            "risk": {
                "risk_score": 48.0,
                "risk_level": "high",
                "damage_score": 31,
                "entropy_score": 22,
                "propagation_score": 21,
            },
            "compliance": {"passed": True, "alerts": []},
            "diagnostics": [
                {"code": "merge.conflict", "title": "Conflict in auth/session reducer", "severity": "high"},
            ],
            "learning": [
                {"code": "learn.conflict_cluster", "title": "Auth reducer is a conflict hotspot"},
            ],
        },
    },
    "intent-tests-flaky": {
        "intent": {
            "id": "intent-tests-flaky",
            "status": "REJECTED",
            "source": "orchestrator/codex/tests-fixtures-8da2",
            "target": "main",
            "risk_level": "medium",
            "priority": "normal",
        },
        "events": [
            {"event_type": "POLICY_EVALUATED", "timestamp": "2026-03-05T11:55:12Z", "payload": {"verdict": "BLOCK", "reason": "test_failure"}},
        ],
        "risk_review": {
            "intent_id": "intent-tests-flaky",
            "risk": {
                "risk_score": 36.3,
                "risk_level": "medium",
                "damage_score": 18,
                "entropy_score": 11,
                "propagation_score": 14,
            },
            "compliance": {"passed": True, "alerts": []},
            "diagnostics": [
                {"code": "tests.flaky", "title": "Flaky snapshot fixture lane", "severity": "medium"},
            ],
            "learning": [],
        },
    },
    "intent-prod-policy": {
        "intent": {
            "id": "intent-prod-policy",
            "status": "REJECTED",
            "source": "orchestrator/codex/policy-fastpath-a922",
            "target": "main",
            "risk_level": "critical",
            "priority": "urgent",
        },
        "events": [
            {"event_type": "POLICY_EVALUATED", "timestamp": "2026-03-05T11:31:00Z", "payload": {"verdict": "BLOCK", "reason": "policy_gate"}},
            {"event_type": "REVIEW_REQUESTED", "timestamp": "2026-03-05T11:31:12Z", "payload": {"trigger": "policy", "priority": 1}},
        ],
        "risk_review": {
            "intent_id": "intent-prod-policy",
            "risk": {
                "risk_score": 82.4,
                "risk_level": "critical",
                "damage_score": 76,
                "entropy_score": 41,
                "propagation_score": 55,
            },
            "compliance": {
                "passed": False,
                "alerts": [
                    {"code": "security.attestation_missing", "title": "Security attestation missing"},
                    {"code": "dual_approval.required", "title": "Critical risk requires dual approval"},
                ],
            },
            "diagnostics": [
                {"code": "policy.fastpath", "title": "Production fast path violates policy guardrail", "severity": "critical"},
            ],
            "learning": [
                {"code": "learn.production_gate", "title": "Critical policy gate must not be bypassed"},
            ],
        },
        "reviews": [
            {"task_id": "review-prod-policy", "intent_id": "intent-prod-policy", "status": "open", "reviewer": None, "priority": 1},
        ],
        "review_summary": {
            "open_reviews": 1,
            "completed_reviews": 0,
        },
        "compliance_report": {
            "passed": False,
            "alerts": [
                {"code": "security.attestation_missing", "title": "Security attestation missing", "severity": "critical"},
            ],
            "mergeable_rate": 0.42,
        },
    },
    "intent-critical-review": {
        "intent": {
            "id": "intent-critical-review",
            "status": "REVIEW_REQUIRED",
            "source": "orchestrator/claude/payment-route-e911",
            "target": "main",
            "risk_level": "high",
            "priority": "high",
        },
        "events": [
            {"event_type": "REVIEW_REQUESTED", "timestamp": "2026-03-05T11:12:00Z", "payload": {"trigger": "risk", "priority": 2}},
        ],
        "risk_review": {
            "intent_id": "intent-critical-review",
            "risk": {
                "risk_score": 67.0,
                "risk_level": "high",
                "damage_score": 49,
                "entropy_score": 28,
                "propagation_score": 37,
            },
            "compliance": {
                "passed": True,
                "alerts": [{"code": "review.pending", "title": "Manual review pending"}],
            },
            "diagnostics": [
                {"code": "payments.manual_review", "title": "Payment routing change requires reviewer assignment", "severity": "high"},
            ],
            "learning": [],
        },
        "reviews": [
            {"task_id": "review-critical-1", "intent_id": "intent-critical-review", "status": "open", "reviewer": "oncall-payments", "priority": 2},
        ],
        "review_summary": {
            "open_reviews": 1,
            "completed_reviews": 0,
        },
        "compliance_report": {
            "passed": True,
            "alerts": [],
            "mergeable_rate": 0.78,
        },
    },
}


def get_demo_state() -> dict:
    return deepcopy(DEMO_STATE)


def get_demo_job(job_id: str) -> dict | None:
    payload = DEMO_JOBS.get(job_id)
    return deepcopy(payload) if payload else None


def get_demo_jobs() -> list[dict]:
    return [deepcopy(item) for item in DEMO_JOBS.values()]


def get_demo_intent(intent_id: str) -> dict | None:
    payload = DEMO_INTENTS.get(intent_id)
    return deepcopy(payload) if payload else None


def get_demo_reviews() -> list[dict]:
    reviews: list[dict] = []
    for intent in DEMO_INTENTS.values():
        for review in intent.get("reviews", []):
            reviews.append(deepcopy(review))
    reviews.sort(key=lambda item: (item.get("priority") or 99, item.get("task_id") or ""))
    return reviews


def get_demo_compliance() -> dict:
    alerts: list[dict] = []
    passed = True
    mergeable_rates: list[float] = []
    for intent in DEMO_INTENTS.values():
        report = intent.get("compliance_report") or {}
        if report.get("passed") is False:
            passed = False
        for alert in report.get("alerts", []):
            alerts.append(deepcopy(alert))
        if isinstance(report.get("mergeable_rate"), (int, float)):
            mergeable_rates.append(float(report["mergeable_rate"]))
    mergeable_rate = round(sum(mergeable_rates) / len(mergeable_rates), 2) if mergeable_rates else None
    return {
        "passed": passed,
        "alerts": alerts,
        "mergeable_rate": mergeable_rate,
        "source": "demo",
    }
