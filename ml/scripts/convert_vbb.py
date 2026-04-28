"""
VBB → YOLO label converter for the Caltech Pedestrian Dataset.

.vbb files are MATLAB structs (scipy.io-readable) that store per-frame
bounding box annotations.  Only the "person" class is extracted.

YOLO label format per line:
    <class_id> <cx> <cy> <w> <h>   (all values normalized to [0, 1])
"""
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
import scipy.io as sio
from tqdm import tqdm


def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


# ---------------------------------------------------------------------------
# MATLAB struct navigation helpers
# ---------------------------------------------------------------------------

def _get_attr(obj, name: str):
    """Access a field from a MATLAB struct (attribute or record style)."""
    try:
        return getattr(obj, name)
    except AttributeError:
        pass
    try:
        return obj[name]
    except (KeyError, IndexError, TypeError):
        pass
    return None


def _iter_frame_objects(frame_data) -> list:
    """
    Normalise a cell-array element to a flat list of annotation structs.

    scipy.io returns MATLAB cell arrays as numpy object arrays whose elements
    can be: empty array, numpy void (single record), ndarray of voids, or a
    MatlabObject — depending on squeeze_me and struct_as_record settings.
    """
    if frame_data is None:
        return []
    if isinstance(frame_data, np.ndarray):
        if frame_data.size == 0:
            return []
        if frame_data.ndim == 0:
            item = frame_data.item()
            return [item] if item is not None else []
        return list(frame_data.flatten())
    # Single MatlabObject squeezed out of a 1-element cell
    return [frame_data]


# ---------------------------------------------------------------------------
# Image dimension helper
# ---------------------------------------------------------------------------

def _image_size(images_dir: Path) -> Optional[tuple[int, int]]:
    """Return (width, height) by reading the first available JPEG."""
    for jpg in sorted(images_dir.glob("*.jpg")):
        img = cv2.imread(str(jpg))
        if img is not None:
            h, w = img.shape[:2]
            return w, h
    return None


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------

def convert_vbb_to_yolo(
    vbb_path: Path,
    images_dir: Path,
    labels_dir: Path,
    frame_skip: int = 5,
) -> int:
    """
    Convert one .vbb annotation file to YOLO .txt labels.

    Only emits a label file when a matching extracted image exists in
    images_dir (same naming convention as extract_seq_frames: frame_XXXXXX.jpg).

    Returns the number of label files written.
    """
    labels_dir.mkdir(parents=True, exist_ok=True)

    dims = _image_size(images_dir)
    if dims is None:
        _log("ERROR", f"No images found in {images_dir} — run SEQ extraction first")
        return 0
    img_w, img_h = dims

    try:
        mat = sio.loadmat(str(vbb_path), squeeze_me=True, struct_as_record=False)
    except Exception as exc:
        _log("ERROR", f"Cannot load {vbb_path.name}: {exc}")
        return 0

    A = mat.get("A")
    if A is None:
        _log("ERROR", f"No 'A' key in {vbb_path.name}")
        return 0

    try:
        n_frames = int(A.nFrame)
        obj_lists = A.objLists
    except AttributeError as exc:
        _log("ERROR", f"Unexpected VBB structure in {vbb_path.name}: {exc}")
        return 0

    written = 0

    for frame_idx in range(n_frames):
        if frame_idx % frame_skip != 0:
            continue

        img_path = images_dir / f"frame_{frame_idx:06d}.jpg"
        if not img_path.exists():
            continue

        lbl_path = labels_dir / f"frame_{frame_idx:06d}.txt"
        lines: List[str] = []

        try:
            frame_data = obj_lists[frame_idx]
        except (IndexError, TypeError):
            frame_data = None

        for obj in _iter_frame_objects(frame_data):
            try:
                lbl = _get_attr(obj, "lbl")
                if str(lbl).strip() != "person":
                    continue

                pos = _get_attr(obj, "pos")
                if pos is None:
                    continue
                pos = np.array(pos, dtype=float).flatten()
                if len(pos) < 4:
                    continue

                x, y, w, h = pos[:4]
                if w <= 0 or h <= 0:
                    continue

                cx = float(np.clip((x + w / 2) / img_w, 0.0, 1.0))
                cy = float(np.clip((y + h / 2) / img_h, 0.0, 1.0))
                nw = float(np.clip(w / img_w, 0.0, 1.0))
                nh = float(np.clip(h / img_h, 0.0, 1.0))

                lines.append(f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}")

            except (AttributeError, TypeError, ValueError):
                continue

        lbl_path.write_text("\n".join(lines) + ("\n" if lines else ""))
        written += 1

    return written


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def _find_vbb(seq_dir: Path) -> Optional[Path]:
    """Locate the .vbb file that corresponds to a sequence output directory."""
    # seq_dir name is like set00_V000 — reconstruct likely raw paths
    for vbb in seq_dir.rglob("*.vbb"):
        return vbb
    return None


def convert_all_annotations(
    raw_dir: Path,
    images_base: Path,
    labels_base: Path,
    frame_skip: int = 5,
) -> None:
    """
    Match every .vbb file under raw_dir to its extracted image directory and
    convert annotations.

    Output layout:
        labels_base/{set_id}_{video_id}/frame_XXXXXX.txt
    """
    vbb_files = sorted(raw_dir.rglob("*.vbb"))
    if not vbb_files:
        _log("ERROR", f"No .vbb files found in {raw_dir}")
        return

    _log("INFO", f"Found {len(vbb_files)} .vbb file(s)")

    for vbb_path in tqdm(vbb_files, desc="Converting VBB", unit="vbb"):
        rel = vbb_path.relative_to(raw_dir)
        # Strip the 'annotations' directory level if present
        parts = [p for p in rel.with_suffix("").parts if p != "annotations"]
        key = "_".join(parts)

        images_dir = images_base / key
        labels_dir = labels_base / key

        if not images_dir.exists():
            _log("INFO", f"No images for {vbb_path.name} (expected {images_dir}) — skipping")
            continue

        written = convert_vbb_to_yolo(vbb_path, images_dir, labels_dir, frame_skip)
        _log("OK", f"{vbb_path.name} → {written} label files in {labels_dir.name}/")
