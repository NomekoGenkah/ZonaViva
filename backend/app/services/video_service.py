import asyncio
import os

from app.services.storage_service import UPLOAD_DIR, save_results, update_job_status


async def process_video_async(job_id: str, filename: str):
    """Offload blocking YOLO inference to a thread so the API stays responsive."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_processing, job_id, filename)


def _run_processing(job_id: str, filename: str):
    try:
        update_job_status(job_id, "processing")

        from processing.video_processor import VideoProcessor  # noqa: PLC0415

        video_path = os.path.join(UPLOAD_DIR, filename)
        results = VideoProcessor(video_path).process()
        results["job_id"] = job_id

        save_results(job_id, results)
        update_job_status(job_id, "done")
    except Exception as exc:
        update_job_status(job_id, "error", str(exc))
        raise
