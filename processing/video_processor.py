from collections import defaultdict
from typing import Dict, List

import cv2
import numpy as np

from processing.detector import PersonDetector


class VideoProcessor:
    """
    Processes a video file and extracts per-second people counts.

    Parameters
    ----------
    video_path:       path to the input video file
    sample_every_n_seconds: how often to sample (default: every second)
    """

    def __init__(self, video_path: str, sample_every_n_seconds: int = 1):
        self.video_path = video_path
        self.sample_interval = sample_every_n_seconds
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

        # Sample one frame per `sample_interval` seconds
        frame_step = max(1, int(fps * self.sample_interval))

        # Map: second -> list of counts (multiple samples possible per second)
        counts_by_second: Dict[int, List[int]] = defaultdict(list)
        frames_analyzed = 0
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                second = int(frame_idx / fps)
                count = self.detector.count_people(frame)
                counts_by_second[second].append(count)
                frames_analyzed += 1

            frame_idx += 1

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
            parts.append(f"Busiest period: {busy[0]}s\u2013{busy[-1]}s.")

        return " ".join(parts)
