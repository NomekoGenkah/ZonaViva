from fastapi import APIRouter, HTTPException

from app.services.storage_service import get_job, load_results

router = APIRouter()


@router.get("/results/{job_id}")
def get_results(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] != "done":
        raise HTTPException(
            status_code=400,
            detail=f"Results not ready. Current status: {job['status']}",
        )
    data = load_results(job_id)
    if not data:
        raise HTTPException(status_code=500, detail="Result file missing")
    return data
