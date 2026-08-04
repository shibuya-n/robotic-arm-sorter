"""Camera integration placeholders.

The current project stage intentionally accepts image files only. This module
exists so a phone camera, USB camera, or network stream can be added later
without changing the detector interface.
"""

from __future__ import annotations

import numpy as np


class CameraUnavailableError(NotImplementedError):
    """Raised when camera capture is requested before it is implemented."""


def capture_frame() -> np.ndarray:
    """Capture one frame from a future camera source.

    Raises:
        CameraUnavailableError: Always, until camera support is implemented.
    """

    raise CameraUnavailableError(
        "Camera capture is not implemented yet. Use an image file with src.main."
    )
