# ZonaViva Analytics

A minimal viable platform for extracting spatial metrics from video — people count, occupancy, and activity over time.

Upload a video recording, let the system process it with YOLOv8, and explore the results in a simple dashboard.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS + Recharts |
| Backend API | Python + FastAPI |
| Video processing | OpenCV + YOLOv8n (ultralytics) |
| Storage | SQLite (job state) + JSON files (results) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
ZonaViva/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── models/schemas.py
│       ├── routes/          # upload · status · results
│       └── services/        # storage · video dispatch
├── processing/
│   ├── video_processor.py   # frame sampling + aggregation
│   └── detector.py          # YOLOv8n with HOG fallback
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    └── src/
        ├── pages/           # UploadPage · ResultsPage
        └── components/      # PeopleChart · MetricCard · StatusBadge
```

---

## Running with Docker (recommended)

Requires: Docker + Docker Compose

```bash
git clone <repo-url>
cd ZonaViva
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

> The first build downloads the YOLOv8n model (~6 MB) and bakes it into the image. Subsequent builds use the Docker layer cache.

---

## Running locally (dev)

Requires: Python 3.11+ · Node.js 20+

**Backend**

```bash
pip install -r backend/requirements.txt -r processing/requirements.txt

DB_PATH=./data/analytics.db \
UPLOAD_DIR=./data/uploads \
RESULTS_DIR=./data/results \
uvicorn app.main:app --reload --app-dir backend
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/v1/*` to `http://localhost:8000`, so no CORS configuration is needed.

Open http://localhost:5173.

---

## API Reference

### `POST /api/v1/upload`

Upload a video file for processing.

**Request:** `multipart/form-data` with field `file`  
**Accepted formats:** MP4, AVI, MOV, MKV, WebM (max 500 MB)

**Response `202`:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Video uploaded successfully. Processing has started."
}
```

---

### `GET /api/v1/status/{job_id}`

Poll the processing status of a job.

**Response `200`:**
```json
{
  "job_id": "550e8400-...",
  "status": "processing",
  "filename": "550e8400-....mp4",
  "created_at": "2026-04-13T10:00:00",
  "error": null
}
```

| `status` value | Meaning |
|----------------|---------|
| `pending` | Queued, not started |
| `processing` | YOLO inference running |
| `done` | Results available |
| `error` | Processing failed (see `error` field) |

---

### `GET /api/v1/results/{job_id}`

Retrieve the full analytics results for a completed job.

**Response `200`:**
```json
{
  "job_id": "550e8400-...",
  "total_people_detected": 120,
  "peak_count": 8,
  "avg_count": 3.4,
  "duration_seconds": 60,
  "frames_analyzed": 60,
  "timeline": [
    { "time": 0, "count": 3 },
    { "time": 1, "count": 5 }
  ],
  "activity_summary": "Video duration: 60s. Peak occupancy: 8 people. Average occupancy: 3.4 people. Busiest period: 12s–45s."
}
```

Returns `400` if the job is not yet complete, `404` if the job does not exist.

---

### `GET /api/v1/health`

Basic health check used by Docker Compose.

```json
{ "status": "ok" }
```

---

## How it works

1. User uploads a video via the web UI.
2. The backend saves the file and creates a job record in SQLite.
3. A background thread runs the video processor:
   - Samples one frame per second using OpenCV.
   - Runs YOLOv8n on each frame to count people (class 0).
   - Aggregates counts into a per-second timeline.
4. Results are saved as a JSON file and the job status is set to `done`.
5. The frontend polls `/api/v1/status/{id}` every 2.5 seconds and renders the dashboard once complete.

---

## Roadmap (not yet implemented)

- IP camera / RTSP stream ingestion
- Real-time processing
- Heatmap visualization
- Multi-source ingestion
- Dedicated worker service (Celery + Redis)
