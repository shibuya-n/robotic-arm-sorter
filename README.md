# Robotic Arm Sorter

This repository is starting with the computer vision foundation for a future robotic arm sorting system. The current stage detects simple red, green, and blue objects in still image files using OpenCV and configurable HSV thresholds.

It does not use machine learning, YOLO, robot arm control, or a phone app yet.

## Project Structure

```text
src/
    main.py
    detector.py
    camera.py
    config.py
tests/
images/
    input/
    output/
requirements.txt
README.md
.gitignore
```

## Install

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run Detection

Place an image in `images/input/`, then run:

```powershell
python -m src.main --image images/input/sample.jpg
```

The command prints structured JSON to the terminal and saves an annotated image to `images/output/sample_annotated.jpg`.

You can choose explicit output paths:

```powershell
python -m src.main --image images/input/sample.jpg --output images/output/annotated.jpg --json-output images/output/detections.json
```

Example output:

```json
{
  "objects": [
    {
      "color": "red",
      "shape": "rectangle",
      "center_px": [200, 150],
      "bounding_box": {
        "x": 175,
        "y": 110,
        "width": 50,
        "height": 80
      },
      "width_px": 50,
      "height_px": 80,
      "contour_area_px": 4000.0
    }
  ]
}
```

## Run Tests

```powershell
python -m pytest
```

The tests generate synthetic images, so no camera is required.

## Current Limitations

- Detection is based only on hand-tuned HSV color thresholds.
- Lighting, shadows, camera white balance, and object material can affect results.
- Only red, green, and blue objects are configured right now.
- Shape detection is approximate and limited to circle, rectangle, or unknown.
- Overlapping objects may be detected as one contour.
- Camera input, sorting decisions, robot arm control, phone integration, and machine learning are intentionally out of scope for this stage.
