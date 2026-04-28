"""
Inference visualizer — runs a trained YOLOv8 model over validation images and
renders bounding boxes with confidence scores in an OpenCV window.

Controls:
    SPACE  →  pause / resume
    q      →  quit
"""
from pathlib import Path

import cv2


def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


_WINDOW = "ZonaViva — Detection Preview"
_BOX_COLOR = (0, 255, 0)
_TEXT_COLOR = (0, 255, 0)
_FONT = cv2.FONT_HERSHEY_SIMPLEX


def _draw_detections(frame, results) -> None:
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), _BOX_COLOR, 2)

            label = f"person {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, _FONT, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), _BOX_COLOR, -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 4), _FONT, 0.5, (0, 0, 0), 1, cv2.LINE_AA)


def visualize_predictions(model_path: Path, images_dir: Path) -> None:
    """
    Load a trained model and display detections on every image in images_dir.

    Blocks until the user presses 'q'.
    """
    from ultralytics import YOLO  # deferred so the module is importable without torch

    images = sorted(images_dir.rglob("*.jpg"))
    if not images:
        _log("ERROR", f"No images found in {images_dir}")
        return

    _log("INFO", f"Loading model: {model_path}")
    model = YOLO(str(model_path))

    _log("INFO", f"Visualizing {len(images)} image(s). SPACE = pause, q = quit")

    cv2.namedWindow(_WINDOW, cv2.WINDOW_NORMAL)
    paused = False

    for img_path in images:
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue

        results = model(frame, verbose=False)
        n_det = sum(len(r.boxes) for r in results)
        _draw_detections(frame, results)

        status = f"{img_path.name}  |  detections: {n_det}  |  SPACE=pause  q=quit"
        cv2.setWindowTitle(_WINDOW, status)
        cv2.imshow(_WINDOW, frame)

        # Inner loop keeps frame visible while paused
        while True:
            wait_ms = 0 if paused else 30
            key = cv2.waitKey(wait_ms) & 0xFF
            if key == ord("q"):
                cv2.destroyAllWindows()
                _log("OK", "Visualization ended by user")
                return
            if key == ord(" "):
                paused = not paused
            if not paused:
                break

    cv2.destroyAllWindows()
    _log("OK", "All images displayed")
