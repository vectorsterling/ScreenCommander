"""Platform-specific screen capture."""

from __future__ import annotations

import platform
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


class ScreenCaptureError(RuntimeError):
    """Raised when screen capture fails."""


def capture_screen(display_index: int | None = None) -> Image.Image:
    """Capture the screen and return a PIL image (top-left origin, pixels)."""
    system = platform.system()
    if system == "Darwin":
        return _capture_macos(display_index)
    raise ScreenCaptureError(f"Screen capture is not implemented for {system}")


def _capture_macos(display_index: int | None) -> Image.Image:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
        path = Path(handle.name)

    command = ["screencapture", "-x", "-m", str(path)]
    if display_index is not None:
        command = ["screencapture", "-x", "-D", str(display_index), str(path)]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ScreenCaptureError(
                "screencapture failed (grant Screen Recording in System Settings). "
                f"exit={result.returncode} {detail}"
            )
        if not path.exists() or path.stat().st_size == 0:
            raise ScreenCaptureError("screencapture produced an empty file")

        with Image.open(path) as image:
            return image.convert("RGB").copy()
    finally:
        path.unlink(missing_ok=True)
