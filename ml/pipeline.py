#!/usr/bin/env python3
"""
ZonaViva ML Pipeline — Caltech Pedestrian Dataset → YOLOv8n

Usage:
    python pipeline.py --mode full        # convert + train
    python pipeline.py --mode convert     # SEQ/VBB preprocessing only
    python pipeline.py --mode train       # training only (requires prior convert)
    python pipeline.py --mode visualize   # inference viewer on val set
"""
import argparse
import random
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from scripts.convert_seq import extract_all_sequences
from scripts.convert_vbb import convert_all_annotations
from scripts.report import generate_report
from scripts.visualize import visualize_predictions


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def _resolve(cfg: dict, key: str) -> Path:
    return ROOT / cfg[key.split(".")[0]][key.split(".")[1]]


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------

def _step_convert(cfg: dict) -> None:
    raw_dir       = ROOT / cfg["data"]["raw_dir"]
    processed_dir = ROOT / cfg["data"]["processed_dir"]
    frame_skip    = int(cfg["seq"]["frame_skip"])

    images_base = processed_dir / "images"
    labels_base = processed_dir / "labels"

    _log("INFO", f"raw_dir   : {raw_dir}")
    _log("INFO", f"frame_skip: {frame_skip}")

    _log("INFO", "--- SEQ → images ---")
    extract_all_sequences(raw_dir, images_base, frame_skip)

    _log("INFO", "--- VBB → YOLO labels ---")
    convert_all_annotations(raw_dir, images_base, labels_base, frame_skip)

    _log("OK", "Conversion complete")


def _step_build_dataset(cfg: dict) -> None:
    processed_dir = ROOT / cfg["data"]["processed_dir"]
    train_split   = float(cfg["data"]["train_split"])

    images_base = processed_dir / "images"
    labels_base = processed_dir / "labels"

    # Collect images that are NOT already in a train/val split dir
    _SPLIT_DIRS = {"train", "val"}
    all_images = [
        p for p in sorted(images_base.rglob("*.jpg"))
        if not _SPLIT_DIRS.intersection(p.parts)
    ]

    if not all_images:
        _log("ERROR", f"No source images found in {images_base}")
        sys.exit(1)

    # Keep only images that have a matching label file
    pairs = []
    for img in all_images:
        rel = img.relative_to(images_base)
        lbl = labels_base / rel.with_suffix(".txt")
        if lbl.exists():
            pairs.append((img, lbl))

    if not pairs:
        _log("ERROR", "No image/label pairs found — run convert first")
        sys.exit(1)

    _log("INFO", f"Found {len(pairs)} image/label pair(s)")

    random.shuffle(pairs)
    cut = int(len(pairs) * train_split)
    splits = {"train": pairs[:cut], "val": pairs[cut:]}

    for subset, subset_pairs in splits.items():
        img_dst = images_base / subset
        lbl_dst = labels_base / subset
        # Clear stale files from a previous build
        shutil.rmtree(img_dst, ignore_errors=True)
        shutil.rmtree(lbl_dst, ignore_errors=True)
        img_dst.mkdir(parents=True)
        lbl_dst.mkdir(parents=True)

        for img_src, lbl_src in subset_pairs:
            # Flatten path to a unique filename: set00_V000_frame_000000.jpg
            flat = img_src.relative_to(images_base).as_posix().replace("/", "_")
            shutil.copy2(img_src, img_dst / flat)
            shutil.copy2(lbl_src, lbl_dst / (Path(flat).stem + ".txt"))

        _log("INFO", f"{subset}: {len(subset_pairs)} samples")

    dataset_yaml = processed_dir / "dataset.yaml"
    dataset_yaml.write_text(
        yaml.dump(
            {
                "path": str(processed_dir.resolve()),
                "train": "images/train",
                "val":   "images/val",
                "nc":    1,
                "names": ["person"],
            },
            default_flow_style=False,
        )
    )
    _log("OK", f"dataset.yaml → {dataset_yaml}")


def _step_train(cfg: dict) -> None:
    import torch
    from ultralytics import YOLO

    processed_dir = ROOT / cfg["data"]["processed_dir"]
    runs_dir      = ROOT / cfg["output"]["runs_dir"]
    models_dir    = ROOT / cfg["output"]["models_dir"]
    models_dir.mkdir(parents=True, exist_ok=True)

    dataset_yaml = processed_dir / "dataset.yaml"
    if not dataset_yaml.exists():
        _log("ERROR", "dataset.yaml not found — run convert first")
        sys.exit(1)

    device_cfg = str(cfg["model"].get("device", "auto"))
    if device_cfg == "auto":
        if torch.cuda.is_available():
            device = "0"
            _log("INFO", f"Device: GPU (CUDA) — {torch.cuda.get_device_name(0)}")
        else:
            device = "cpu"
            _log("INFO", "Device: CPU (CUDA not available)")
    else:
        device = device_cfg
        _log("INFO", f"Device: {device} (from config)")

    model = YOLO(cfg["model"]["name"])

    model.train(
        data=str(dataset_yaml),
        epochs=int(cfg["model"]["epochs"]),
        batch=int(cfg["model"]["batch_size"]),
        imgsz=int(cfg["model"]["img_size"]),
        device=device,
        project=str(runs_dir),
        name="caltech_pedestrian",
        exist_ok=True,
    )

    best_weights = runs_dir / "caltech_pedestrian" / "weights" / "best.pt"
    if best_weights.exists():
        dest = models_dir / "best.pt"
        shutil.copy2(best_weights, dest)
        _log("OK", f"Best model → {dest}")
    else:
        _log("ERROR", "best.pt not found after training — check runs/ directory")


def _step_report(cfg: dict) -> None:
    _log("INFO", "--- Generating report ---")
    path = generate_report(cfg, ROOT)
    _log("OK", f"Report saved → {path.relative_to(ROOT)}")


def _step_visualize(cfg: dict) -> None:
    models_dir    = ROOT / cfg["output"]["models_dir"]
    processed_dir = ROOT / cfg["data"]["processed_dir"]

    model_path = models_dir / "best.pt"
    val_images  = processed_dir / "images" / "val"

    if not model_path.exists():
        _log("ERROR", f"Model not found: {model_path}  (run train first)")
        sys.exit(1)
    if not val_images.exists():
        _log("ERROR", f"Val images not found: {val_images}  (run convert first)")
        sys.exit(1)

    visualize_predictions(model_path, val_images)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ZonaViva ML Pipeline — Caltech Pedestrian → YOLOv8n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["full", "convert", "train", "visualize", "report"],
        default="full",
        help="Pipeline mode (default: full)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "config.yaml",
        help="Path to config.yaml (default: config/config.yaml)",
    )
    args = parser.parse_args()

    if not args.config.exists():
        _log("ERROR", f"Config not found: {args.config}")
        sys.exit(1)

    cfg = _load_config(args.config)
    _log("INFO", f"Mode: {args.mode}  |  Config: {args.config}")

    if args.mode in ("full", "convert"):
        _step_convert(cfg)
        _step_build_dataset(cfg)

    if args.mode in ("full", "train"):
        _step_train(cfg)
        _step_report(cfg)

    if args.mode == "report":
        _step_report(cfg)

    if args.mode == "visualize":
        _step_visualize(cfg)

    _log("OK", "Pipeline done")


if __name__ == "__main__":
    main()
