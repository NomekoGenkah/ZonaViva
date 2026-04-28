"""
Post-training report generator.

Reads the Ultralytics results.csv, the processed dataset directories, and the
config to produce a self-contained markdown report saved under ml/reports/.
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np


def _log(level: str, msg: str) -> None:
    print(f"[{level}] {msg}")


# ---------------------------------------------------------------------------
# Dataset statistics
# ---------------------------------------------------------------------------

def _label_stats(labels_dir: Path) -> dict:
    """
    Scan a labels directory and return annotation statistics.

    Each .txt file = one image.  Each non-empty line = one person annotation.
    """
    if not labels_dir.exists():
        return {"images": 0, "annotated": 0, "empty": 0, "total_persons": 0,
                "avg": 0.0, "max": 0, "min": 0}

    counts = []
    for txt in sorted(labels_dir.glob("*.txt")):
        lines = [l for l in txt.read_text().splitlines() if l.strip()]
        counts.append(len(lines))

    if not counts:
        return {"images": 0, "annotated": 0, "empty": 0, "total_persons": 0,
                "avg": 0.0, "max": 0, "min": 0}

    annotated = [c for c in counts if c > 0]
    return {
        "images":         len(counts),
        "annotated":      len(annotated),
        "empty":          len(counts) - len(annotated),
        "total_persons":  sum(counts),
        "avg":            round(float(np.mean(annotated)), 2) if annotated else 0.0,
        "max":            max(annotated) if annotated else 0,
        "min":            min(annotated) if annotated else 0,
    }


def _collect_dataset_stats(processed_dir: Path) -> dict:
    train = _label_stats(processed_dir / "labels" / "train")
    val   = _label_stats(processed_dir / "labels" / "val")

    total_images   = train["images"] + val["images"]
    total_persons  = train["total_persons"] + val["total_persons"]
    total_annotated = train["annotated"] + val["annotated"]

    all_avg = (
        round((train["avg"] * train["annotated"] + val["avg"] * val["annotated"])
              / total_annotated, 2)
        if total_annotated else 0.0
    )

    return {
        "train": train,
        "val":   val,
        "total_images":    total_images,
        "total_persons":   total_persons,
        "total_annotated": total_annotated,
        "overall_avg":     all_avg,
        "overall_max":     max(train["max"], val["max"]),
    }


# ---------------------------------------------------------------------------
# Training results
# ---------------------------------------------------------------------------

def _read_results_csv(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        return [{k.strip(): v.strip() for k, v in row.items()} for row in reader]


def _best_epoch_row(rows: list[dict]) -> Optional[dict]:
    """Return the row with the highest mAP@0.5."""
    if not rows:
        return None
    try:
        return max(rows, key=lambda r: float(r.get("metrics/mAP50(B)", 0) or 0))
    except (ValueError, TypeError):
        return None


def _fval(row: Optional[dict], key: str, pct: bool = False) -> str:
    if row is None:
        return "N/A"
    raw = row.get(key, "")
    try:
        v = float(raw)
        return f"{v * 100:.1f}%" if pct else f"{v:.4f}"
    except (ValueError, TypeError):
        return "N/A"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(cfg: dict, root: Path) -> Path:
    """
    Build a markdown report for the most recent training run and save it
    under ml/reports/.  Returns the path to the created file.
    """
    processed_dir = root / cfg["data"]["processed_dir"]
    runs_dir      = root / cfg["output"]["runs_dir"]
    models_dir    = root / cfg["output"]["models_dir"]
    reports_dir   = root / "reports"
    reports_dir.mkdir(exist_ok=True)

    timestamp  = datetime.now()
    ts_str     = timestamp.strftime("%Y%m%d_%H%M%S")
    ts_display = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    # ---- dataset stats ------------------------------------------------
    ds = _collect_dataset_stats(processed_dir)

    # ---- training metrics --------------------------------------------
    results_csv = runs_dir / "caltech_pedestrian" / "results.csv"
    rows        = _read_results_csv(results_csv)
    best_row    = _best_epoch_row(rows)
    total_epochs = len(rows)
    best_epoch   = best_row.get("epoch", "N/A") if best_row else "N/A"

    # ---- model file --------------------------------------------------
    model_path = models_dir / "best.pt"
    model_size = (
        f"{model_path.stat().st_size / 1024 / 1024:.2f} MB"
        if model_path.exists() else "N/A"
    )

    # ---- device (best-effort from args.yaml) -------------------------
    args_yaml = runs_dir / "caltech_pedestrian" / "args.yaml"
    device_used = cfg["model"].get("device", "auto")
    if args_yaml.exists():
        try:
            import yaml
            args = yaml.safe_load(args_yaml.read_text())
            device_used = str(args.get("device", device_used))
        except Exception:
            pass

    # ---- assemble report ------------------------------------------
    lines: list[str] = []

    def h(level: int, text: str) -> None:
        lines.append(f"{'#' * level} {text}\n")

    def table(headers: list[str], rows_: list[list[str]]) -> None:
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for r in rows_:
            lines.append("| " + " | ".join(str(c) for c in r) + " |")
        lines.append("")

    def rule() -> None:
        lines.append("---\n")

    # Header
    h(1, "ZonaViva ML Pipeline — Training Report")
    lines.append(f"**Generated:** {ts_display}  \n")
    lines.append(f"**Run name:** caltech_pedestrian  \n")
    lines.append("")
    rule()

    # Configuration
    h(2, "Configuration")
    table(
        ["Parameter", "Value"],
        [
            ["Base model",    cfg["model"]["name"]],
            ["Epochs",        cfg["model"]["epochs"]],
            ["Batch size",    cfg["model"]["batch_size"]],
            ["Image size",    cfg["model"]["img_size"]],
            ["Device",        device_used],
            ["Frame skip",    cfg["seq"]["frame_skip"]],
            ["Train split",   f"{int(cfg['data']['train_split'] * 100)}%"],
        ],
    )
    rule()

    # Dataset
    h(2, "Dataset")
    tr, va = ds["train"], ds["val"]
    table(
        ["Metric", "Train", "Val", "Total"],
        [
            ["Images",                tr["images"],       va["images"],       ds["total_images"]],
            ["Annotated frames",      tr["annotated"],    va["annotated"],    ds["total_annotated"]],
            ["Empty frames",          tr["empty"],        va["empty"],        tr["empty"] + va["empty"]],
            ["Person annotations",    tr["total_persons"],va["total_persons"],ds["total_persons"]],
            ["Avg persons / frame",   tr["avg"],          va["avg"],          ds["overall_avg"]],
            ["Max persons in a frame",tr["max"],          va["max"],          ds["overall_max"]],
            ["Min persons in a frame",tr["min"],          va["min"],          min(tr["min"], va["min"])],
        ],
    )
    rule()

    # Training results
    h(2, "Training Results")
    if rows:
        last_row = rows[-1]
        table(
            ["Metric", "Value"],
            [
                ["Epochs completed",  total_epochs],
                ["Best epoch",        best_epoch],
                ["mAP @ 0.5",         _fval(best_row, "metrics/mAP50(B)")],
                ["mAP @ 0.5:0.95",    _fval(best_row, "metrics/mAP50-95(B)")],
                ["Precision",         _fval(best_row, "metrics/precision(B)")],
                ["Recall",            _fval(best_row, "metrics/recall(B)")],
                ["Box loss (val)",    _fval(best_row, "val/box_loss")],
                ["Cls loss (val)",    _fval(best_row, "val/cls_loss")],
                ["Final box loss",    _fval(last_row, "val/box_loss")],
                ["Final cls loss",    _fval(last_row, "val/cls_loss")],
            ],
        )
    else:
        lines.append("_No results.csv found — training may not have completed._\n")
    rule()

    # Output files
    h(2, "Output Files")
    table(
        ["File", "Path", "Size"],
        [
            ["Best model weights", f"`models/best.pt`",               model_size],
            ["Training run",       f"`runs/caltech_pedestrian/`",      "—"],
            ["Dataset config",     f"`data/processed/dataset.yaml`",   "—"],
            ["This report",        f"`reports/report_{ts_str}.md`",    "—"],
        ],
    )
    rule()

    # Notes
    if ds["total_images"] == 0:
        lines.append(
            "> **Note:** No dataset images were found. "
            "Run `--mode convert` before inspecting dataset statistics.\n"
        )
    if not rows:
        lines.append(
            "> **Note:** Training metrics are unavailable. "
            "Run `--mode train` to populate this section.\n"
        )

    report_path = reports_dir / f"report_{ts_str}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
