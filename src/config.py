"""Adjustable settings for the computer vision pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HSVRange:
    """Inclusive OpenCV HSV color range.

    OpenCV stores hue on a 0-179 scale, while saturation and value use 0-255.
    """

    lower: tuple[int, int, int]
    upper: tuple[int, int, int]


# Default thresholds for brightly colored red, green, and blue objects.
# Red wraps around the hue boundary, so it needs two ranges.
HSV_THRESHOLDS: dict[str, list[HSVRange]] = {
    "red": [
        HSVRange((0, 100, 70), (10, 255, 255)),
        HSVRange((170, 100, 70), (179, 255, 255)),
    ],
    "green": [
        HSVRange((40, 60, 50), (85, 255, 255)),
    ],
    "blue": [
        HSVRange((95, 80, 50), (130, 255, 255)),
    ],
}


MIN_CONTOUR_AREA = 200.0
MORPH_KERNEL_SIZE = 5
ANNOTATION_FONT_SCALE = 0.55
ANNOTATION_LINE_THICKNESS = 2
