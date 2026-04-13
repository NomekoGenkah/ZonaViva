from fastapi import APIRouter, HTTPException

from app.models.schemas import JobStatusResponse
from app.services.storage_service import get_job

router = APIRouter()


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        filename=job["filename"],
        created_at=job["created_at"],
        error=job.get("error"),
    )
