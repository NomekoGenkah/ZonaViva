from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    error = "error"


class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    filename: str
    created_at: str
    error: Optional[str] = None


class TimelineEntry(BaseModel):
    time: int  # seconds from start
    count: int


class ProcessingResult(BaseModel):
    job_id: str
    total_people_detected: int
    peak_count: int
    avg_count: float
    timeline: List[TimelineEntry]
    duration_seconds: int
    frames_analyzed: int
    activity_summary: str
