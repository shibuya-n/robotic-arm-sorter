"""OpenCV object detection utilities for color-based sorting."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

from src.config import (
    ANNOTATION_FONT_SCALE,
    ANNOTATION_LINE_THICKNESS,
    HSVRange,
    HSV_THRESHOLDS,
    MIN_CONTOUR_AREA,
    MORPH_KERNEL_SIZE,
)


@dataclass(frozen=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Detection:
    color: str
    shape: str
    center_px: tuple[int, int]
    bounding_box: BoundingBox
    width_px: int
    height_px: int
    contour_area_px: float


DRAW_COLORS_BGR: dict[str, tuple[int, int, int]] = {
    "red": (0, 0, 255),
    "green": (0, 180, 0),
    "blue": (255, 0, 0),
}


def load_image(image_path: str | Path) -> np.ndarray:
    """Load an image from disk using OpenCV."""

    path = Path(image_path)
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return image


def detect_objects(
    image_bgr: np.ndarray,
    hsv_thresholds: dict[str, list[HSVRange]] | None = None,
    min_contour_area: float = MIN_CONTOUR_AREA,
    morph_kernel_size: int = MORPH_KERNEL_SIZE,
) -> list[Detection]:
    """Detect configured object colors in a BGR image."""

    if image_bgr is None or image_bgr.size == 0:
        raise ValueError("image_bgr must be a non-empty OpenCV image")

    thresholds = hsv_thresholds or HSV_THRESHOLDS
    hsv_image = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    detections: list[Detection] = []

    for color, color_ranges in thresholds.items():
        mask = build_color_mask(hsv_image, color_ranges, morph_kernel_size)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_contour_area:
                continue

            x, y, width, height = cv2.boundingRect(contour)
            center = contour_center(contour, x, y, width, height)
            detections.append(
                Detection(
                    color=color,
                    shape=classify_shape(contour),
                    center_px=center,
                    bounding_box=BoundingBox(x=x, y=y, width=width, height=height),
                    width_px=width,
                    height_px=height,
                    contour_area_px=round(float(area), 2),
                )
            )

    return sorted(detections, key=lambda item: (item.color, item.center_px[1], item.center_px[0]))


def build_color_mask(
    hsv_image: np.ndarray,
    color_ranges: Iterable[HSVRange],
    morph_kernel_size: int = MORPH_KERNEL_SIZE,
) -> np.ndarray:
    """Create a cleaned binary mask for one logical color."""

    mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
    for color_range in color_ranges:
        lower = np.array(color_range.lower, dtype=np.uint8)
        upper = np.array(color_range.upper, dtype=np.uint8)
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv_image, lower, upper))

    if morph_kernel_size > 1:
        kernel = np.ones((morph_kernel_size, morph_kernel_size), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


def contour_center(
    contour: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int,
) -> tuple[int, int]:
    """Calculate a contour center, falling back to the bounding box center."""

    moments = cv2.moments(contour)
    if moments["m00"] != 0:
        return int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"])
    return x + width // 2, y + height // 2


def classify_shape(contour: np.ndarray) -> str:
    """Classify a contour as a circle, rectangle, or unknown."""

    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return "unknown"

    approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    if len(approx) == 4:
        return "rectangle"

    area = cv2.contourArea(contour)
    circularity = (4 * math.pi * area) / (perimeter * perimeter)
    if len(approx) >= 6 and circularity >= 0.75:
        return "circle"

    return "unknown"


def detections_to_json(detections: Iterable[Detection]) -> dict[str, list[dict[str, object]]]:
    """Convert detections into a JSON-serializable object."""

    objects: list[dict[str, object]] = []
    for detection in detections:
        item = asdict(detection)
        item["center_px"] = list(detection.center_px)
        objects.append(item)
    return {"objects": objects}


def save_detections_json(detections: Iterable[Detection], output_path: str | Path) -> None:
    """Save detections as formatted JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(detections_to_json(detections), indent=2), encoding="utf-8")


def annotate_image(image_bgr: np.ndarray, detections: Iterable[Detection]) -> np.ndarray:
    """Draw bounding boxes, labels, and center points onto an image copy."""

    annotated = image_bgr.copy()
    for detection in detections:
        box = detection.bounding_box
        draw_color = DRAW_COLORS_BGR.get(detection.color, (255, 255, 255))
        top_left = (box.x, box.y)
        bottom_right = (box.x + box.width, box.y + box.height)

        cv2.rectangle(
            annotated,
            top_left,
            bottom_right,
            draw_color,
            ANNOTATION_LINE_THICKNESS,
        )
        cv2.circle(annotated, detection.center_px, 4, draw_color, -1)
        draw_label(annotated, f"{detection.color} {detection.shape}", top_left, draw_color)

    return annotated


def draw_label(
    image_bgr: np.ndarray,
    label: str,
    top_left: tuple[int, int],
    color_bgr: tuple[int, int, int],
) -> None:
    """Draw a readable label near a bounding box."""

    x, y = top_left
    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1
    text_size, baseline = cv2.getTextSize(label, font, ANNOTATION_FONT_SCALE, thickness)
    text_width, text_height = text_size
    label_y = max(y, text_height + baseline + 4)

    cv2.rectangle(
        image_bgr,
        (x, label_y - text_height - baseline - 4),
        (x + text_width + 6, label_y + baseline - 2),
        color_bgr,
        -1,
    )
    cv2.putText(
        image_bgr,
        label,
        (x + 3, label_y - 5),
        font,
        ANNOTATION_FONT_SCALE,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )


def save_annotated_image(
    image_bgr: np.ndarray,
    detections: Iterable[Detection],
    output_path: str | Path,
) -> None:
    """Save an annotated detection image to disk."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    annotated = annotate_image(image_bgr, detections)
    if not cv2.imwrite(str(path), annotated):
        raise OSError(f"Could not write annotated image: {path}")


def detect_image_file(
    input_path: str | Path,
    annotated_output_path: str | Path | None = None,
    json_output_path: str | Path | None = None,
) -> dict[str, list[dict[str, object]]]:
    """Run detection for an image file and optionally save outputs."""

    image = load_image(input_path)
    detections = detect_objects(image)

    if annotated_output_path is not None:
        save_annotated_image(image, detections, annotated_output_path)
    if json_output_path is not None:
        save_detections_json(detections, json_output_path)

    return detections_to_json(detections)
