import cv2
import numpy as np


class PersonDetector:
    """
    Detects and counts people in a single frame.

    Primary:  YOLOv8n (ultralytics) — fast, accurate, ~6 MB model.
    Fallback: OpenCV HOG people detector — no download required.
    """

    def __init__(self):
        self.model = None
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO  # noqa: PLC0415

            self.model = YOLO("yolov8n.pt")
            print("[Detector] YOLOv8n loaded.")
        except Exception as exc:
            print(f"[Detector] YOLO unavailable ({exc}). Falling back to HOG.")
            self.model = None

    def count_people(self, frame: np.ndarray) -> int:
        count, _ = self.detect_people(frame)
        return count

    def detect_people(self, frame: np.ndarray) -> tuple[int, list]:
        """Returns (count, boxes) where boxes is [(x1, y1, x2, y2, confidence), ...]."""
        if self.model is not None:
            return self._yolo_detect(frame)
        return self._hog_detect(frame)

    def _yolo_detect(self, frame: np.ndarray) -> tuple[int, list]:
        results = self.model(frame, classes=[0], verbose=False)
        boxes = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                boxes.append((int(x1), int(y1), int(x2), int(y2), conf))
        return len(boxes), boxes

    def _hog_detect(self, frame: np.ndarray) -> tuple[int, list]:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        h, w = frame.shape[:2]
        scale = min(1.0, 640 / max(h, w))
        small = cv2.resize(frame, (int(w * scale), int(h * scale)))
        rects, weights = hog.detectMultiScale(small, winStride=(8, 8), padding=(4, 4), scale=1.05)
        if len(rects) == 0:
            return 0, []
        boxes = []
        for (x, y, bw, bh), conf in zip(rects, weights):
            x1 = int(x / scale)
            y1 = int(y / scale)
            x2 = int((x + bw) / scale)
            y2 = int((y + bh) / scale)
            boxes.append((x1, y1, x2, y2, float(conf)))
        return len(boxes), boxes
