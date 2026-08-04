from __future__ import annotations

import json

import cv2
import numpy as np

from src.detector import detect_image_file, detect_objects, detections_to_json


def test_detects_colored_rectangle_and_circle() -> None:
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.rectangle(image, (40, 60), (100, 140), (0, 0, 255), -1)
    cv2.circle(image, (210, 120), 30, (0, 255, 0), -1)

    detections = detect_objects(image)

    by_color = {detection.color: detection for detection in detections}
    assert set(by_color) == {"green", "red"}

    red = by_color["red"]
    assert red.shape == "rectangle"
    assert 65 <= red.center_px[0] <= 75
    assert 95 <= red.center_px[1] <= 105
    assert 55 <= red.width_px <= 70
    assert 75 <= red.height_px <= 90
    assert red.contour_area_px > 4000

    green = by_color["green"]
    assert green.shape == "circle"
    assert 205 <= green.center_px[0] <= 215
    assert 115 <= green.center_px[1] <= 125


def test_small_noise_is_removed() -> None:
    image = np.zeros((120, 120, 3), dtype=np.uint8)
    cv2.rectangle(image, (10, 10), (12, 12), (0, 0, 255), -1)

    assert detect_objects(image) == []


def test_detections_are_json_serializable() -> None:
    image = np.zeros((160, 160, 3), dtype=np.uint8)
    cv2.rectangle(image, (30, 40), (90, 100), (255, 0, 0), -1)

    payload = detections_to_json(detect_objects(image))

    json.dumps(payload)
    assert len(payload["objects"]) == 1
    detected = payload["objects"][0]
    assert detected["color"] == "blue"
    assert detected["center_px"] == [60, 70]
    assert detected["bounding_box"]["width"] > 0
    assert detected["contour_area_px"] > 0


def test_detect_image_file_saves_annotated_image_and_json(tmp_path) -> None:
    input_path = tmp_path / "input.png"
    annotated_path = tmp_path / "annotated.png"
    json_path = tmp_path / "detections.json"

    image = np.zeros((160, 160, 3), dtype=np.uint8)
    cv2.rectangle(image, (25, 30), (80, 90), (0, 0, 255), -1)
    assert cv2.imwrite(str(input_path), image)

    payload = detect_image_file(input_path, annotated_path, json_path)

    assert annotated_path.exists()
    assert json_path.exists()
    assert payload == json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["objects"][0]["color"] == "red"
