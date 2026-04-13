import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "/data/analytics.db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/data/uploads")
RESULTS_DIR = os.getenv("RESULTS_DIR", "/data/results")


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id      TEXT PRIMARY KEY,
            filename    TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL,
            error       TEXT
        )
    """)
    conn.commit()
    conn.close()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_job(job_id: str, filename: str) -> dict:
    now = datetime.utcnow().isoformat()
    conn = _connect()
    conn.execute(
        "INSERT INTO jobs (job_id, filename, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
        (job_id, filename, now, now),
    )
    conn.commit()
    conn.close()
    return {"job_id": job_id, "filename": filename, "status": "pending", "created_at": now}


def update_job_status(job_id: str, status: str, error: str = None):
    now = datetime.utcnow().isoformat()
    conn = _connect()
    conn.execute(
        "UPDATE jobs SET status = ?, updated_at = ?, error = ? WHERE job_id = ?",
        (status, now, error, job_id),
    )
    conn.commit()
    conn.close()


def get_job(job_id: str) -> dict | None:
    conn = _connect()
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def save_results(job_id: str, data: dict):
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(path, "w") as f:
        json.dump(data, f)


def load_results(job_id: str) -> dict | None:
    path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None
