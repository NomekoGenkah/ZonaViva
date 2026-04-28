"""
SEQ → JPEG frame extractor for the Caltech Pedestrian Dataset.

The Caltech .seq format (Norpix StreamPix) stores MJPEG frames after a
1024-byte header.  Two block layouts appear in practice:

  A) No size prefix — JPEG frames are concatenated directly after the header.
  B) 4-byte little-endian block size before each JPEG, where the size value
     INCLUDES those 4 bytes (i.e. jpeg_bytes = block_size - 4).

The correct layout is auto-detected from the bytes immediately after the
header before any frame is extracted.
"""
import struct
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from tqdm import tqdm

_HEADER_SIZE = 1024
_JPEG_SOI    = b"\xff\xd8"
_JPEG_EOI    = b"\xff\xd9"
_MIN_FRAME_B = 512   # real JPEG frames are always larger than this


def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


# ---------------------------------------------------------------------------
# Header parsing
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
# Format auto-detection
# ---------------------------------------------------------------------------

def _detect_layout(data: bytes) -> tuple[str, bool]:
    """
    Inspect the bytes right after the header and return:
        ("direct", False)       — JPEGs concatenated with no prefix
        ("prefix", True/False)  — 4-byte prefix; True if size includes itself

    Falls back to ("direct", False) when the layout cannot be determined.
    """
    if len(data) <= _HEADER_SIZE + 6:
        return "direct", False

    h = _HEADER_SIZE

    # Layout A: JPEG starts right at the header boundary
    if data[h : h + 2] == _JPEG_SOI:
        return "direct", False

    # Layout B: 4-byte size prefix, JPEG starts 4 bytes after header
    if data[h + 4 : h + 6] == _JPEG_SOI:
        first_block = struct.unpack_from("<I", data, h)[0]

        # If size INCLUDES the 4-byte field itself:
        #   next block starts at h + first_block
        pos_incl = h + first_block
        # If size does NOT include the 4-byte field:
        #   next block starts at h + 4 + first_block
        pos_excl = h + 4 + first_block

        if pos_incl + 6 <= len(data) and data[pos_incl + 4 : pos_incl + 6] == _JPEG_SOI:
            return "prefix", True   # size includes the 4-byte field

        if pos_excl + 6 <= len(data) and data[pos_excl + 4 : pos_excl + 6] == _JPEG_SOI:
            return "prefix", False  # size is pure JPEG size

        # Single-frame file or can't confirm — assume self-inclusive (most common)
        return "prefix", True

    return "direct", False


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

def _decode_jpeg(raw: bytes) -> Optional[np.ndarray]:
    arr = np.frombuffer(raw, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _save_frame(img: np.ndarray, output_dir: Path, frame_idx: int) -> None:
    path = output_dir / f"frame_{frame_idx:06d}.jpg"
    cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])


def _extract_prefix(
    data: bytes,
    output_dir: Path,
    frame_skip: int,
    size_includes_self: bool,
) -> int:
    """Extract using a 4-byte little-endian block-size prefix per frame."""
    pos = _HEADER_SIZE
    frame_idx = 0
    saved = 0

    while pos + 4 <= len(data):
        (block_size,) = struct.unpack_from("<I", data, pos)
        pos += 4

        # Derive the actual JPEG byte count from the block size
        jpeg_len = block_size - 4 if size_includes_self else block_size

        if jpeg_len < _MIN_FRAME_B or pos + jpeg_len > len(data):
            break

        jpeg_bytes = data[pos : pos + jpeg_len]
        pos += jpeg_len

        if frame_idx % frame_skip == 0:
            img = _decode_jpeg(jpeg_bytes)
            if img is not None:
                _save_frame(img, output_dir, frame_idx)
                saved += 1

        frame_idx += 1

    return saved


def _extract_scan(data: bytes, output_dir: Path, frame_skip: int) -> int:
    """
    Scan for JPEG SOI/EOI markers as a fallback.

    Skips segments smaller than _MIN_FRAME_B to avoid false hits on EXIF
    thumbnails embedded inside larger frames.
    """
    pos = _HEADER_SIZE
    frame_idx = 0
    saved = 0

    while pos < len(data) - 1:
        soi = data.find(_JPEG_SOI, pos)
        if soi == -1:
            break

        eoi = data.find(_JPEG_EOI, soi + 2)
        if eoi == -1:
            break
        eoi += 2  # include the two EOI bytes

        segment_len = eoi - soi
        if segment_len < _MIN_FRAME_B:
            # False positive (e.g. EXIF thumbnail) — skip past it and keep going
            pos = eoi
            continue

        if frame_idx % frame_skip == 0:
            img = _decode_jpeg(data[soi:eoi])
            if img is not None:
                _save_frame(img, output_dir, frame_idx)
                saved += 1

        frame_idx += 1
        pos = eoi

    return saved


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_seq_frames(seq_path: Path, output_dir: Path, frame_skip: int = 5) -> int:
    """
    Extract sampled frames from a single .seq file.

    Output filenames preserve the original frame index so they align with
    VBB annotation indices: frame_000000.jpg, frame_000005.jpg, …

    Returns the number of frames written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(seq_path, "rb") as f:
        data = f.read()

    if len(data) <= _HEADER_SIZE:
        _log("ERROR", f"File too small: {seq_path}")
        return 0

    meta = _parse_header(data)
    expected = meta.get("n_frames", 0)
    if meta.get("width"):
        _log(
            "INFO",
            f"{seq_path.name}: {meta['width']}x{meta['height']} "
            f"@ {meta.get('fps', 0):.1f} FPS, {expected} frames",
        )

    layout, size_incl = _detect_layout(data)
    _log("INFO", f"{seq_path.name}: layout={layout}, size_includes_self={size_incl}")

    if layout == "prefix":
        saved = _extract_prefix(data, output_dir, frame_skip, size_incl)
    else:
        saved = _extract_scan(data, output_dir, frame_skip)

    # Sanity check: if we expected many frames but got very few, try the scan
    expected_saved = max(1, expected // frame_skip) if expected else 0
    if saved < max(2, expected_saved // 4) and layout == "prefix":
        _log(
            "INFO",
            f"{seq_path.name}: prefix extracted {saved} frames (expected ~{expected_saved}) "
            f"— retrying with JPEG scan",
        )
        # Clear any partially written files from the failed prefix run
        for f in output_dir.glob("frame_*.jpg"):
            f.unlink()
        saved = _extract_scan(data, output_dir, frame_skip)

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
        _log("OK", f"{seq_path.name} → {saved} frames saved")
