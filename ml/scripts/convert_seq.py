"""
SEQ → JPEG frame extractor for the Caltech Pedestrian Dataset.

The .seq binary format stores MJPEG frames after a 1024-byte header.
Primary strategy: read each frame using the 4-byte size prefix that follows
the header.  Fallback: scan the raw bytes for JPEG SOI/EOI markers.
"""
import struct
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from tqdm import tqdm

_HEADER_SIZE = 1024
_JPEG_SOI = b"\xff\xd8"
_JPEG_EOI = b"\xff\xd9"


def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def _parse_header(data: bytes) -> dict:
    try:
        width  = struct.unpack_from("<I", data, 548)[0]
        height = struct.unpack_from("<I", data, 552)[0]
        fps    = struct.unpack_from("<f", data, 564)[0]
        n_frm  = struct.unpack_from("<I", data, 572)[0]
        return {"width": width, "height": height, "fps": fps, "n_frames": n_frm}
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

def _decode_jpeg(raw: bytes) -> Optional[np.ndarray]:
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _extract_size_prefix(data: bytes, output_dir: Path, frame_skip: int) -> int:
    pos = _HEADER_SIZE
    frame_idx = 0
    saved = 0

    while pos + 4 <= len(data):
        (frame_size,) = struct.unpack_from("<I", data, pos)
        pos += 4

        if frame_size == 0 or pos + frame_size > len(data):
            break

        jpeg_bytes = data[pos : pos + frame_size]
        pos += frame_size

        if frame_idx % frame_skip == 0:
            img = _decode_jpeg(jpeg_bytes)
            if img is not None:
                out = output_dir / f"frame_{frame_idx:06d}.jpg"
                cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                saved += 1

        frame_idx += 1

    return saved


def _extract_jpeg_scan(data: bytes, output_dir: Path, frame_skip: int) -> int:
    pos = _HEADER_SIZE
    frame_idx = 0
    saved = 0

    while pos < len(data) - 1:
        start = data.find(_JPEG_SOI, pos)
        if start == -1:
            break
        end = data.find(_JPEG_EOI, start + 2)
        if end == -1:
            break
        end += 2

        if frame_idx % frame_skip == 0:
            img = _decode_jpeg(data[start:end])
            if img is not None:
                out = output_dir / f"frame_{frame_idx:06d}.jpg"
                cv2.imwrite(str(out), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
                saved += 1

        frame_idx += 1
        pos = end

    return saved


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_seq_frames(seq_path: Path, output_dir: Path, frame_skip: int = 5) -> int:
    """
    Extract frames from a single .seq file.

    Frames are saved as frame_XXXXXX.jpg where XXXXXX is the original frame
    index inside the sequence (preserves temporal alignment with VBB labels).

    Returns the number of frames written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(seq_path, "rb") as f:
        data = f.read()

    if len(data) <= _HEADER_SIZE:
        _log("ERROR", f"File too small to contain frames: {seq_path}")
        return 0

    meta = _parse_header(data)
    if meta:
        _log(
            "INFO",
            f"{seq_path.name}: {meta.get('width')}x{meta.get('height')} "
            f"@ {meta.get('fps', 0):.1f} FPS, {meta.get('n_frames', '?')} frames",
        )

    saved = _extract_size_prefix(data, output_dir, frame_skip)

    if saved == 0:
        _log("INFO", f"Size-prefix strategy yielded 0 frames for {seq_path.name} — trying JPEG scan")
        saved = _extract_jpeg_scan(data, output_dir, frame_skip)

    return saved


def extract_all_sequences(raw_dir: Path, output_base: Path, frame_skip: int = 5) -> None:
    """
    Recursively find all .seq files under raw_dir and extract their frames.

    Output layout:
        output_base/{set_id}_{video_id}/frame_XXXXXX.jpg
    """
    seq_files = sorted(raw_dir.rglob("*.seq"))
    if not seq_files:
        _log("ERROR", f"No .seq files found in {raw_dir}")
        return

    _log("INFO", f"Found {len(seq_files)} .seq file(s)")

    for seq_path in tqdm(seq_files, desc="Extracting SEQ", unit="seq"):
        rel = seq_path.relative_to(raw_dir)
        out_subdir = output_base / "_".join(rel.with_suffix("").parts)
        saved = extract_seq_frames(seq_path, out_subdir, frame_skip)
        _log("OK", f"{seq_path.name} → {saved} frames in {out_subdir.name}/")
