from __future__ import annotations

from fastapi import APIRouter, Body

from converge_ui.bff.service import get_control_plane_service


router = APIRouter()


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready() -> dict[str, str]:
    return {"status": "ready"}


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
    return get_control_plane_service().get_job_detail(job_id)


@router.get("/api/v1/intents/{intent_id}")
def intent_detail(intent_id: str) -> dict:
    return get_control_plane_service().get_intent_detail(intent_id)


@router.get("/api/v1/reviews")
def reviews() -> dict:
    return get_control_plane_service().get_reviews()


@router.get("/api/v1/compliance")
def compliance() -> dict:
    return get_control_plane_service().get_compliance()


@router.post("/api/v1/actions/refresh")
def refresh() -> dict:
    return get_control_plane_service().refresh()


@router.post("/api/v1/actions/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    return get_control_plane_service().retry_job(job_id)


@router.post("/api/v1/actions/reviews")
def request_review(body: dict = Body(default_factory=dict)) -> dict:
    return get_control_plane_service().request_review(
        intent_id=str(body.get("intent_id", "")),
        trigger=str(body.get("trigger", "policy")),
        reviewer=body.get("reviewer"),
        priority=body.get("priority"),
    )


@router.post("/api/v1/actions/reviews/{task_id}/assign")
def assign_review(task_id: str, body: dict = Body(default_factory=dict)) -> dict:
    return get_control_plane_service().assign_review(
        task_id,
        reviewer=str(body.get("reviewer", "")),
    )


@router.post("/api/v1/actions/reviews/{task_id}/complete")
def complete_review(task_id: str, body: dict = Body(default_factory=dict)) -> dict:
    return get_control_plane_service().complete_review(
        task_id,
        resolution=str(body.get("resolution", "approved")),
        notes=str(body.get("notes", "")),
    )


@router.post("/api/v1/actions/reviews/{task_id}/escalate")
def escalate_review(task_id: str, body: dict = Body(default_factory=dict)) -> dict:
    return get_control_plane_service().escalate_review(
        task_id,
        reason=str(body.get("reason", "sla_breach")),
    )


@router.post("/api/v1/actions/reviews/{task_id}/cancel")
def cancel_review(task_id: str, body: dict = Body(default_factory=dict)) -> dict:
    return get_control_plane_service().cancel_review(
        task_id,
        reason=str(body.get("reason", "")),
    )
