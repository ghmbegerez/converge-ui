"""Pydantic response models for the BFF API.

These mirror the frontend TypeScript types in frontend/src/types/index.ts
and provide runtime validation + automatic OpenAPI documentation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Shared building blocks
# ---------------------------------------------------------------------------


class JobCard(BaseModel):
    job_id: str
    trace_id: str | None = None
    agent: str | None = None
    attempt: int | None = None
    status: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    reason: str | None = None
    started_at: str | None = None
    last_activity_at: str | None = None
    next_retry_at: str | None = None
    intent_id: str | None = None
    prompt_preview: str | None = None

    model_config = {"extra": "allow"}


class ReviewItem(BaseModel):
    task_id: str | None = None
    intent_id: str | None = None
    status: str | None = None
    reviewer: str | None = None
    priority: int | None = None
    resolution: str | None = None
    notes: str | None = None

    model_config = {"extra": "allow"}


class FilterSet(BaseModel):
    status: list[str] = []
    agent: list[str] = []
    risk_level: list[str] = []
    source: list[str] = []


# ---------------------------------------------------------------------------
# Page-level responses
# ---------------------------------------------------------------------------


class ServiceStatus(BaseModel):
    reachable: bool
    mode: str | None = None

    model_config = {"extra": "allow"}


class ServicesInfo(BaseModel):
    orchestrator: ServiceStatus
    converge: ServiceStatus


class OverviewResponse(BaseModel):
    services: ServicesInfo
    kpis: dict[str, Any]
    alerts: list[dict[str, Any]]
    top_blockers: list[JobCard]
    generated_at: str
    data_source: str

    model_config = {"extra": "allow"}


class OperationsResponse(BaseModel):
    running: list[JobCard]
    retry_queue: list[JobCard]
    blocked: list[JobCard]
    recent_events: list[dict[str, Any]] = []
    filters: FilterSet
    generated_at: str
    data_source: str


class JobsListResponse(BaseModel):
    items: list[dict[str, Any]]
    filters: dict[str, Any] = {}
    generated_at: str
    data_source: str

    model_config = {"extra": "allow"}


class JobDetailResponse(BaseModel):
    job: dict[str, Any] | None = None
    timeline: list[dict[str, Any]] = []
    intent: dict[str, Any] | None = None
    intent_events: list[dict[str, Any]] = []
    risk_review: dict[str, Any] | None = None
    reviews: list[ReviewItem] = []
    review_summary: dict[str, Any] | None = None
    compliance_report: dict[str, Any] | None = None
    operator_actions: dict[str, Any] = {}
    generated_at: str | None = None
    data_source: str = ""

    model_config = {"extra": "allow"}


class IntentDetailResponse(BaseModel):
    intent: dict[str, Any] | None = None
    events: list[dict[str, Any]] = []
    risk_review: dict[str, Any] | None = None
    reviews: list[ReviewItem] = []
    review_summary: dict[str, Any] | None = None
    compliance_report: dict[str, Any] | None = None
    generated_at: str | None = None
    data_source: str = ""

    model_config = {"extra": "allow"}


class ReviewsResponse(BaseModel):
    items: list[ReviewItem]
    summary: dict[str, Any] | None = None
    generated_at: str
    data_source: str


class ComplianceResponse(BaseModel):
    report: dict[str, Any] | None = None
    alerts: list[dict[str, Any]] = []
    generated_at: str
    data_source: str


class ActionResponse(BaseModel):
    status: str
    reason: str | None = None
    data_source: str | None = None
    review: ReviewItem | None = None

    model_config = {"extra": "allow"}
