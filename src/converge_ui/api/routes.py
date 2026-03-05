from __future__ import annotations

from fastapi import APIRouter

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


@router.post("/api/v1/actions/refresh")
def refresh() -> dict:
    return get_control_plane_service().refresh()


@router.post("/api/v1/actions/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    return get_control_plane_service().retry_job(job_id)
