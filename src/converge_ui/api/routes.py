from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from converge_ui.bff.service import get_control_plane_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Request validation models
# ---------------------------------------------------------------------------

_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")
_RESOLUTION_VALUES = {"approved", "rejected", "deferred", "escalated"}
_TRIGGER_VALUES = {"policy", "manual", "sla", "risk"}


class ReviewCreateRequest(BaseModel):
    intent_id: str
    trigger: str = "policy"
    reviewer: str | None = None
    priority: int | None = None

    @field_validator("intent_id")
    @classmethod
    def intent_id_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("intent_id is required")
        if not _ID_PATTERN.match(v):
            raise ValueError("intent_id contains invalid characters")
        if len(v) > 200:
            raise ValueError("intent_id too long (max 200)")
        return v

    @field_validator("trigger")
    @classmethod
    def trigger_valid(cls, v: str) -> str:
        if v not in _TRIGGER_VALUES:
            raise ValueError(
                f"trigger must be one of {sorted(_TRIGGER_VALUES)}"
            )
        return v

    @field_validator("reviewer")
    @classmethod
    def reviewer_valid(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 100:
                raise ValueError("reviewer too long (max 100)")
        return v

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 10):
            raise ValueError("priority must be between 1 and 10")
        return v


class ReviewAssignRequest(BaseModel):
    reviewer: str

    @field_validator("reviewer")
    @classmethod
    def reviewer_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("reviewer is required")
        if len(v) > 100:
            raise ValueError("reviewer too long (max 100)")
        return v


class ReviewCompleteRequest(BaseModel):
    resolution: str = "approved"
    notes: str = ""

    @field_validator("resolution")
    @classmethod
    def resolution_valid(cls, v: str) -> str:
        if v not in _RESOLUTION_VALUES:
            raise ValueError(
                f"resolution must be one of {sorted(_RESOLUTION_VALUES)}"
            )
        return v

    @field_validator("notes")
    @classmethod
    def notes_valid(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError("notes too long (max 2000)")
        return v


class ReviewEscalateRequest(BaseModel):
    reason: str = "sla_breach"

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("reason too long (max 500)")
        return v


class ReviewCancelRequest(BaseModel):
    reason: str = ""

    @field_validator("reason")
    @classmethod
    def reason_valid(cls, v: str) -> str:
        if len(v) > 500:
            raise ValueError("reason too long (max 500)")
        return v


# ---------------------------------------------------------------------------
# Path param validation
# ---------------------------------------------------------------------------


def _validate_id(value: str, name: str) -> str:
    if not value or not _ID_PATTERN.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} format",
        )
    return value


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready() -> dict[str, str]:
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# Data endpoints (viewer)
# ---------------------------------------------------------------------------


@router.get("/api/v1/overview")
def overview() -> dict:
    return get_control_plane_service().get_overview()


@router.get("/api/v1/operations")
def operations() -> dict:
    return get_control_plane_service().get_operations()


@router.get("/api/v1/jobs")
def list_jobs() -> dict:
    return get_control_plane_service().list_jobs()


@router.get("/api/v1/jobs/{job_id}")
def job_detail(job_id: str) -> dict:
    _validate_id(job_id, "job_id")
    return get_control_plane_service().get_job_detail(job_id)


@router.get("/api/v1/intents/{intent_id}")
def intent_detail(intent_id: str) -> dict:
    _validate_id(intent_id, "intent_id")
    return get_control_plane_service().get_intent_detail(intent_id)


@router.get("/api/v1/reviews")
def reviews() -> dict:
    return get_control_plane_service().get_reviews()


@router.get("/api/v1/compliance")
def compliance() -> dict:
    return get_control_plane_service().get_compliance()


# ---------------------------------------------------------------------------
# Action endpoints (operator)
# ---------------------------------------------------------------------------


@router.post("/api/v1/actions/refresh")
def refresh() -> dict:
    return get_control_plane_service().refresh()


@router.post("/api/v1/actions/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    _validate_id(job_id, "job_id")
    return get_control_plane_service().retry_job(job_id)


@router.post("/api/v1/actions/reviews")
def request_review(body: ReviewCreateRequest) -> dict:
    return get_control_plane_service().request_review(
        intent_id=body.intent_id,
        trigger=body.trigger,
        reviewer=body.reviewer,
        priority=body.priority,
    )


@router.post("/api/v1/actions/reviews/{task_id}/assign")
def assign_review(task_id: str, body: ReviewAssignRequest) -> dict:
    _validate_id(task_id, "task_id")
    return get_control_plane_service().assign_review(
        task_id,
        reviewer=body.reviewer,
    )


@router.post("/api/v1/actions/reviews/{task_id}/complete")
def complete_review(task_id: str, body: ReviewCompleteRequest) -> dict:
    _validate_id(task_id, "task_id")
    return get_control_plane_service().complete_review(
        task_id,
        resolution=body.resolution,
        notes=body.notes,
    )


@router.post("/api/v1/actions/reviews/{task_id}/escalate")
def escalate_review(task_id: str, body: ReviewEscalateRequest) -> dict:
    _validate_id(task_id, "task_id")
    return get_control_plane_service().escalate_review(
        task_id,
        reason=body.reason,
    )


@router.post("/api/v1/actions/reviews/{task_id}/cancel")
def cancel_review(task_id: str, body: ReviewCancelRequest) -> dict:
    _validate_id(task_id, "task_id")
    return get_control_plane_service().cancel_review(
        task_id,
        reason=body.reason,
    )
