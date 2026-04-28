import os
import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile

from app.models.schemas import UploadResponse
from app.services.storage_service import UPLOAD_DIR, create_job
from app.services.video_service import process_video_async

router = APIRouter()

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB


@router.post("/upload", response_model=UploadResponse, status_code=202)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    debug: bool = Form(False),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    job_id = str(uuid.uuid4())
    dest_filename = f"{job_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, dest_filename)

    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    create_job(job_id, dest_filename, debug=debug)
    background_tasks.add_task(process_video_async, job_id, dest_filename, debug)

    return UploadResponse(
        job_id=job_id,
        status="pending",
        message="Video uploaded successfully. Processing has started.",
    )
