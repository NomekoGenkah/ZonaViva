FROM python:3.11-slim

# System deps for OpenCV + ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1-mesa-glx \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer cache)
COPY backend/requirements.txt /tmp/backend_req.txt
COPY processing/requirements.txt /tmp/processing_req.txt
RUN pip install --no-cache-dir -r /tmp/backend_req.txt -r /tmp/processing_req.txt

# Pre-download YOLOv8n model so it's baked into the image
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" 2>/dev/null || true

# Copy application code
COPY backend/app /app/app
COPY processing /app/processing

# Data directories
RUN mkdir -p /data/uploads /data/results

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
