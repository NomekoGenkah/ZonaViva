from collections import defaultdict
from typing import Dict, List, Optional

import cv2
import numpy as np

from processing.detector import PersonDetector


class VideoProcessor:
    """
    Processes a video file and extracts per-second people counts.

    Parameters
    ----------
    video_path:             path to the input video file
    sample_every_n_seconds: how often to sample (default: every second)
    debug:                  if True, render annotated frames to debug_output_path
    debug_output_path:      destination path for the annotated MP4
    """

    def __init__(
        self,
        video_path: str,
        sample_every_n_seconds: int = 1,
        debug: bool = False,
        debug_output_path: Optional[str] = None,
    ):
        self.video_path = video_path
        self.sample_interval = sample_every_n_seconds
        self.debug = debug
        self.debug_output_path = debug_output_path
        self._detector: PersonDetector | None = None

    @property
    def detector(self) -> PersonDetector:
        if self._detector is None:
            self._detector = PersonDetector()
        return self._detector

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self) -> dict:
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")

        try:
            return self._extract_metrics(cap)
        finally:
            cap.release()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_metrics(self, cap: cv2.VideoCapture) -> dict:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = max(1, int(total_frames / fps))
        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Sample one frame per `sample_interval` seconds
        frame_step = max(1, int(fps * self.sample_interval))

        # Debug video writer: output 1 annotated frame per sample interval
        writer = None
        if self.debug and self.debug_output_path:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            # Output at 2 FPS so the player doesn't feel like a slideshow
            writer = cv2.VideoWriter(self.debug_output_path, fourcc, 2.0, (frame_w, frame_h))

        counts_by_second: Dict[int, List[int]] = defaultdict(list)
        frames_analyzed = 0
        frame_idx = 0
        last_boxes: list = []
        last_count: int = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_step == 0:
                    second = int(frame_idx / fps)
                    if self.debug:
                        last_count, last_boxes = self.detector.detect_people(frame)
                    else:
                        last_count = self.detector.count_people(frame)
                        last_boxes = []
                    counts_by_second[second].append(last_count)
                    frames_analyzed += 1

                    if writer is not None:
                        annotated = self._annotate_frame(frame, last_boxes, last_count, second)
                        writer.write(annotated)

                frame_idx += 1
        finally:
            if writer is not None:
                writer.release()

        return self._aggregate(counts_by_second, duration, frames_analyzed)

    def _aggregate(
        self,
        counts_by_second: Dict[int, List[int]],
        duration: int,
        frames_analyzed: int,
    ) -> dict:
        timeline = []
        all_counts: List[int] = []

        for sec in sorted(counts_by_second):
            avg = int(round(np.mean(counts_by_second[sec])))
            timeline.append({"time": sec, "count": avg})
            all_counts.append(avg)

        total = sum(all_counts)
        peak = max(all_counts) if all_counts else 0
        avg_count = round(float(np.mean(all_counts)), 2) if all_counts else 0.0

        return {
            "total_people_detected": total,
            "peak_count": peak,
            "avg_count": avg_count,
            "timeline": timeline,
            "duration_seconds": duration,
            "frames_analyzed": frames_analyzed,
            "activity_summary": self._summarize(timeline, peak, avg_count, duration),
        }

    @staticmethod
    def _annotate_frame(frame: np.ndarray, boxes: list, count: int, second: int) -> np.ndarray:
        out = frame.copy()
        for x1, y1, x2, y2, conf in boxes:
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                out,
                f"person {conf:.2f}",
                (x1, max(0, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )
        overlay = f"Count: {count}  |  t={second}s"
        # Dark background pill for readability
        (tw, th), _ = cv2.getTextSize(overlay, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        cv2.rectangle(out, (6, 6), (tw + 16, th + 16), (0, 0, 0), -1)
        cv2.putText(
            out,
            overlay,
            (10, th + 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return out

    @staticmethod
    def _summarize(
        timeline: List[dict], peak: int, avg: float, duration: int
    ) -> str:
        if not timeline or peak == 0:
            return "No people detected in this video."

        high_threshold = peak * 0.75
        busy = [t["time"] for t in timeline if t["count"] >= high_threshold]

        parts = [f"Video duration: {duration}s."]
        if peak:
            parts.append(f"Peak occupancy: {peak} {'person' if peak == 1 else 'people'}.")
        if avg:
            parts.append(f"Average occupancy: {avg:.1f} people.")
        if busy:
            parts.append(f"Busiest period: {busy[0]}s–{busy[-1]}s.")

        return " ".join(parts)
