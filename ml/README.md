# ZonaViva ML Pipeline

Fine-tune YOLOv8n on the Caltech Pedestrian Dataset for people detection.
Fully standalone — no dependency on the backend or frontend.

---

## Directory layout

Everything lives inside `ml/`.  The backend and frontend are never touched.

```
ml/
├── pipeline.py            # CLI entry point
├── requirements.txt
├── config/
│   └── config.yaml        # all tuneable parameters
├── scripts/
│   ├── convert_seq.py     # .seq → JPEG frames
│   ├── convert_vbb.py     # .vbb → YOLO labels
│   └── visualize.py       # inference preview
├── data/
│   ├── raw/               # ← put your Caltech .seq + .vbb files here
│   └── processed/         # auto-generated (frames, labels, dataset.yaml)
├── runs/                  # auto-generated (Ultralytics training output)
└── models/                # auto-generated (best.pt copied here after training)
```

---

## Setup

```bash
cd ml
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

GPU support is automatic.  PyTorch with CUDA is detected at runtime; no manual switch is needed.

---

## Data preparation

Download the Caltech Pedestrian Dataset and place it under `data/raw/`.
Expected structure (the pipeline searches recursively):

```
data/raw/
└── set00/
    ├── V000.seq
    ├── V001.seq
    └── annotations/
        ├── V000.vbb
        └── V001.vbb
```

---

## Running

### Full pipeline (convert + train)

```bash
python pipeline.py --mode full
```

### Preprocessing only

Extracts frames from .seq files and converts .vbb annotations to YOLO format,
then builds the train/val split.

```bash
python pipeline.py --mode convert
```

### Training only

Requires a prior `convert` run.

```bash
python pipeline.py --mode train
```

### Inference preview

Opens an OpenCV window and runs the trained model over validation images.
Press **SPACE** to pause, **q** to quit.

```bash
python pipeline.py --mode visualize
```

### Custom config

```bash
python pipeline.py --mode full --config config/config.yaml
```

---

## Configuration (`config/config.yaml`)

| Key | Default | Description |
|-----|---------|-------------|
| `data.raw_dir` | `data/raw` | Source .seq/.vbb files |
| `data.processed_dir` | `data/processed` | Extracted frames and labels |
| `data.train_split` | `0.8` | Fraction used for training |
| `seq.frame_skip` | `5` | Extract every Nth frame |
| `model.name` | `yolov8n.pt` | Base weights (auto-downloaded) |
| `model.epochs` | `50` | Training epochs |
| `model.batch_size` | `16` | Batch size |
| `model.img_size` | `640` | Input resolution |
| `model.device` | `auto` | `auto` \| `cpu` \| `0` (GPU index) |
| `output.runs_dir` | `runs` | Ultralytics training output |
| `output.models_dir` | `models` | Best model destination |

---

## GPU usage

- `device: auto` — uses GPU if CUDA is available, otherwise CPU.
- `device: cpu` — force CPU.
- `device: 0` — force GPU 0.  Use `1`, `2`, etc. for multi-GPU machines.

The pipeline logs the selected device at startup:

```
[INFO] Device: GPU (CUDA) — NVIDIA GeForce RTX 3080
```

---

## Outputs

| Path | Contents |
|------|----------|
| `data/processed/images/train/` | Training images |
| `data/processed/images/val/` | Validation images |
| `data/processed/labels/train/` | YOLO labels for train |
| `data/processed/labels/val/` | YOLO labels for val |
| `data/processed/dataset.yaml` | Dataset config for Ultralytics |
| `runs/caltech_pedestrian/` | Full Ultralytics training run |
| `models/best.pt` | Best checkpoint (copied from runs/) |
