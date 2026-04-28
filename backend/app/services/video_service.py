import asyncio
import os

from app.services.storage_service import RESULTS_DIR, UPLOAD_DIR, save_results, update_job_status


async def process_video_async(job_id: str, filename: str, debug: bool = False):
    """Offload blocking YOLO inference to a thread so the API stays responsive."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_processing, job_id, filename, debug)


def _run_processing(job_id: str, filename: str, debug: bool = False):
    try:
        update_job_status(job_id, "processing")

        from processing.video_processor import VideoProcessor  # noqa: PLC0415

        video_path = os.path.join(UPLOAD_DIR, filename)
        debug_output_path = None
        if debug:
            debug_output_path = os.path.join(RESULTS_DIR, f"{job_id}_debug.mp4")

        results = VideoProcessor(
            video_path,
            debug=debug,
            debug_output_path=debug_output_path,
        ).process()
        results["job_id"] = job_id

        if debug and debug_output_path and os.path.exists(debug_output_path):
            results["debug_video_url"] = f"/api/v1/debug/{job_id}"

        save_results(job_id, results)
        update_job_status(job_id, "done")
    except Exception as exc:
        update_job_status(job_id, "error", str(exc))
        raise
