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
        if self.model is not None:
            return self._yolo_count(frame)
        return self._hog_count(frame)

    def _yolo_count(self, frame: np.ndarray) -> int:
        results = self.model(frame, classes=[0], verbose=False)  # class 0 = person
        return sum(len(r.boxes) for r in results)

    def _hog_count(self, frame: np.ndarray) -> int:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        # Resize to speed up inference; scale back detections are not needed here
        h, w = frame.shape[:2]
        scale = min(1.0, 640 / max(h, w))
        small = cv2.resize(frame, (int(w * scale), int(h * scale)))
        rects, _ = hog.detectMultiScale(small, winStride=(8, 8), padding=(4, 4), scale=1.05)
        return len(rects)
