# Claude Instructions – MVP Spatial Analytics

## Context

You are helping build an MVP for a platform that analyzes video to extract spatial metrics (people count, flow, occupancy).

This is an early prototype. Keep things simple, modular, and runnable.

---

## Goal

Build a web-based system where:

* A user uploads a video
* The system processes it
* The system returns basic analytics

---

## Tech Stack (preferred)

* Backend: Python + FastAPI
* Processing: Python + OpenCV + YOLO (lightweight)
* Frontend: React + Vite
* Storage: local files + SQLite
* Containerization: Docker + docker-compose

---

## Core Features

1. Upload video
2. Process video (detect people)
3. Generate metrics:

   * People count over time
   * Total detections
4. Display results in a dashboard

---

## Architecture Rules

* Keep modules separated:

  * API
  * Processing
  * UI
* Avoid tight coupling
* Design thinking ahead (future: live cameras)

---

## API Endpoints

* POST /upload
* GET /status/{id}
* GET /results/{id}

---

## Constraints

* Keep it simple (MVP level)
* Avoid unnecessary complexity
* Must be runnable locally
* Prefer clarity over optimization

---

## Output Expectations

When generating code:

* Provide full working files
* Include folder structure
* Include Docker setup
* Include run instructions

---

## Important Notes

* Do not over-engineer
* Do not introduce unnecessary services
* Focus on working end-to-end pipeline

---

## Future Consideration (do not implement yet)

* IP camera integration
* Real-time processing
* Multi-source ingestion
* Advanced analytics

---

## Principle

This is not about perfect architecture.
This is about validating:
“Can we extract useful spatial metrics from video?”
