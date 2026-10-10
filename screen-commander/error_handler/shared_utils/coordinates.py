"""Convert between screenshot pixels (top-left) and CGEvent points (top-left)."""

from __future__ import annotations

import json
import os
import subprocess
from functools import lru_cache


def top_left_to_quartz(x: float, y: float, screen_height: float) -> tuple[float, float]:
    """Deprecated name: on modern macOS CGEvent mouse positions use top-left points.

    Kept for callers that still pass a height; Y is NOT flipped.
    """
    _ = screen_height
    return (float(x), float(y))


def quartz_to_top_left(x: float, y: float, screen_height: float) -> tuple[float, float]:
    """Identity for top-left CGEvent space (height unused)."""
    _ = screen_height
    return (float(x), float(y))


@lru_cache(maxsize=1)
def main_display_point_size() -> tuple[float, float] | None:
    """Return main display size in AppKit points, or None if unavailable."""
    script = """
ObjC.import("AppKit");
var s = $.NSScreen.mainScreen;
if (!s) { JSON.stringify(null); }
else {
  var f = s.frame;
  JSON.stringify({
    width: f.size.width,
    height: f.size.height,
    scale: s.backingScaleFactor
  });
}
"""
    try:
        result = subprocess.run(
            ["osascript", "-l", "JavaScript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        data = json.loads(result.stdout.strip())
        if not data:
            return None
        return (float(data["width"]), float(data["height"]))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def display_scale_for_image(image_width: int, image_height: int) -> float:
    """
    Scale factor from CGEvent points to screenshot pixels.

    HiDPI / TV: screenshot often 3840x2160 while UI is 1920x1080 points → scale 2.
    Override with SCREEN_COMMANDER_SCALE when auto-detect is wrong.
    """
    override = os.getenv("SCREEN_COMMANDER_SCALE", "").strip()
    if override:
        scale = float(override)
        if scale <= 0:
            raise ValueError("SCREEN_COMMANDER_SCALE must be positive")
        return scale

    points = main_display_point_size()
    if points:
        pts_w, pts_h = points
        if pts_w > 0 and pts_h > 0:
            return float(image_width) / pts_w

    return 1.0


def screenshot_to_quartz(
    x: float,
    y: float,
    *,
    image_width: int,
    image_height: int,
    scale: float | None = None,
) -> tuple[float, float]:
    """
    Map screenshot pixel coordinates (top-left) to CGEvent points (top-left).

    Only applies HiDPI scaling (pixels → points). Does not flip Y — CGEvent mouse
    positions on current macOS match top-left screenshot space.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError("image dimensions must be positive")

    resolved = scale if scale is not None else display_scale_for_image(image_width, image_height)
    if resolved <= 0:
        raise ValueError("scale must be positive")

    return (float(x) / resolved, float(y) / resolved)


def clear_display_geometry_cache() -> None:
    """Clear cached AppKit geometry (call after display changes)."""
    main_display_point_size.cache_clear()
