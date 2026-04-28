import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.storage_service import RESULTS_DIR, get_job

router = APIRouter()


@router.get("/debug/{job_id}")
def get_debug_video(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Results not ready. Current status: {job['status']}",
        )

    path = os.path.join(RESULTS_DIR, f"{job_id}_debug.mp4")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Debug visualization not available for this job",
        )

    return FileResponse(path, media_type="video/mp4", filename=f"debug_{job_id}.mp4")
