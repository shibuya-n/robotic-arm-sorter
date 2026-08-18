# YOLO (Ultralytics) Installation Guide — Robotic Arm Sorter

Step-by-step setup for getting YOLOv8 object detection running on your machine.

## Prerequisites

- Python 3.8+ installed ([python.org](https://www.python.org/downloads/))
- pip (comes with Python)
- (Optional) NVIDIA GPU + drivers if you want CUDA acceleration

Check your Python install:
```bash
python --version
```

## 1. (Recommended) Create a virtual environment (you can definitely skip this)

Keeps this project's packages separate from the rest of your system.

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You'll know it worked if your terminal prompt now starts with `(venv)`.

## 2. Install PyTorch

**Check your CUDA version first** (skip if no NVIDIA GPU):
```bash
nvidia-smi
```
Look at the top-right of the output for "CUDA Version."

**If you have a matching NVIDIA GPU:**
```bash
pip install --user torch torchvision --index-url https://download.pytorch.org/whl/cu132
```
(Replace `cu132` with your CUDA version if different — check [pytorch.org](https://pytorch.org/get-started/locally/) for the exact command.)

**If you don't have a GPU, or aren't sure — start here (safer default):**
```bash
pip install --user torch torchvision
```
CPU inference is plenty fast for small models like `yolov8n`.

> ⚠️ Run this in your normal terminal, **not** inside the Python shell (`>>>`). If you see a `>>>` prompt, type `exit()` first.

## 3. Install Ultralytics (YOLO)

```bash
pip install ultralytics
```

This installs YOLOv8 and pulls in any missing dependencies.

## 4. Verify the install

Create a file `test.py`:

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")  # nano model — smallest/fastest
results = model("https://ultralytics.com/images/bus.jpg", conf=0.1)
results[0].show()  # opens a window with detected boxes
print(results[0].boxes)  # raw detection data
```

Run it:
```bash
python test.py
```

The first run auto-downloads the `yolov8n.pt` weights (~6MB). A window should pop up showing the bus image with detection boxes drawn on it.

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| `SyntaxError: invalid syntax` on `pip install ...` | You're inside the Python REPL (`>>>`), not the terminal | Type `exit()`, then run pip commands from your normal terminal |
| `IndexError: list index out of range` on `results[1]` | Only one image was passed in, so the list only has index `[0]` | Use `results[0]`, or pass multiple images as a list: `model([img1, img2])` |
| `(no detections)` on your own image | Object isn't a COCO class, or confidence threshold too high | Try `conf=0.1` to lower the threshold; if still nothing, you'll need to fine-tune on your own labeled data |
| `results.append(model(...))` gives a nested list | `append()` adds the whole results list as one item | Use `results.extend(model(...))` instead, or pass all images in a single `model([...])` call |

## Notes for This Project

- Pretrained YOLOv8 covers 80 COCO classes (includes `sports ball`, `bottle`, `cup`, `scissors`, etc.) — if your sort objects match one of these, no training needed.
- If your objects are custom (specific parts, colors, etc.), plan to collect ~100–200 labeled images and fine-tune `yolov8n.pt`. [Roboflow](https://roboflow.com/) has a free tier for labeling.
- Stick with `yolov8n` (nano) for now — it's the fastest model and should be enough for real-time sorting on CPU.