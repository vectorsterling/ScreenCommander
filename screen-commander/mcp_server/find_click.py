"""OCR find-and-click for Screen Commander MCP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from action_executor.macos_input import MacosInputController
from mcp_server.ocr import OcrBox, recognize_text
from screen_analyzer.capture import ScreenCaptureError, capture_screen
from shared_utils.coordinates import screenshot_to_quartz


@dataclass(frozen=True)
class _Hit:
    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float  # OCR confidence 0..1
    score: float = 0.0  # match quality used to pick the best hit

    @property
    def center(self) -> tuple[float, float]:
        return self.left + self.width / 2.0, self.top + self.height / 2.0


def find_and_click(
    text: str,
    click: bool = True,
    region: list[float] | None = None,
    *,
    input_controller: MacosInputController | None = None,
    image: Image.Image | None = None,
) -> dict[str, Any]:
    """
    Screenshot (full display, or crop to ``region``), OCR-locate ``text``,
    then return and optionally left-click the center of the best match.

    OCR prefers macOS Vision (``VNRecognizeTextRequest`` via PyObjC); falls
    back to pytesseract when Vision/PyObjC is unavailable.

    Coordinates are screenshot-pixel top-left (same space as the ``computer`` tool).
    Optional ``region`` is ``[x0, y0, x1, y1]`` in that space.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")

    needle = _normalize(text)
    offset_x, offset_y = 0, 0

    if image is None:
        try:
            full = capture_screen()
        except ScreenCaptureError as exc:
            raise RuntimeError(str(exc)) from exc
    else:
        full = image

    # Full screenshot, then crop when region is given (OCR only on that area).
    search_image = full
    if region is not None:
        x0, y0, x1, y1 = _parse_region(region, full.width, full.height)
        offset_x, offset_y = x0, y0
        search_image = full.crop((x0, y0, x1, y1))

    hit = _best_match(search_image, needle)
    if hit is None:
        return {
            "found": False,
            "x": None,
            "y": None,
            "confidence": 0.0,
            "clicked": False,
        }

    # Center of the best OCR match, mapped back into full-screenshot space.
    x = float(round(hit.center[0] + offset_x, 1))
    y = float(round(hit.center[1] + offset_y, 1))
    confidence = round(hit.score, 4)
    clicked = False

    if click:
        controller = input_controller or MacosInputController()
        qx, qy = screenshot_to_quartz(x, y, image_width=full.width, image_height=full.height)
        controller.click(qx, qy, button="left")
        clicked = True

    return {
        "found": True,
        "x": x,
        "y": y,
        "confidence": confidence,
        "clicked": clicked,
    }


def _parse_region(region: list[float], width: int, height: int) -> tuple[int, int, int, int]:
    if not isinstance(region, (list, tuple)) or len(region) != 4:
        raise ValueError("region must be [x0, y0, x1, y1] in screenshot pixels")
    try:
        x0, y0, x1, y1 = (int(region[0]), int(region[1]), int(region[2]), int(region[3]))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"region values must be numbers, got {region!r}") from exc
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"region must have x1>x0 and y1>y0, got {region!r}")
    x0 = max(0, min(x0, width - 1))
    y0 = max(0, min(y0, height - 1))
    x1 = max(x0 + 1, min(x1, width))
    y1 = max(y0 + 1, min(y1, height))
    return x0, y0, x1, y1


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _best_match(image: Image.Image, needle: str) -> _Hit | None:
    """OCR ``image`` and return the best center-match for ``needle``, or None."""
    boxes, _backend = recognize_text(image)
    candidates = [_box_to_hit(b) for b in boxes] + _phrase_hits(boxes, needle)

    best: _Hit | None = None
    best_score = 0.0
    for hit in candidates:
        hay = _normalize(hit.text)
        if not hay:
            continue
        if needle == hay:
            score = 1.0 * hit.confidence
        elif needle in hay:
            score = 0.85 * hit.confidence * (len(needle) / max(len(hay), 1))
        else:
            continue
        if score > best_score:
            best = _Hit(
                text=hit.text,
                left=hit.left,
                top=hit.top,
                width=hit.width,
                height=hit.height,
                confidence=hit.confidence,
                score=score,
            )
            best_score = score

    if best is None or best_score < 0.25:
        return None
    return best


def _box_to_hit(box: OcrBox) -> _Hit:
    return _Hit(
        text=box.text,
        left=box.left,
        top=box.top,
        width=box.width,
        height=box.height,
        confidence=box.confidence,
    )


def _phrase_hits(boxes: list[OcrBox], needle: str) -> list[_Hit]:
    """Join adjacent boxes on the same OCR line so multi-word queries match."""
    if len(boxes) < 2:
        return []

    by_line: dict[tuple[int, ...], list[OcrBox]] = {}
    for box in boxes:
        by_line.setdefault(box.line_key, []).append(box)

    needle_words = needle.split()
    need_n = max(1, len(needle_words))
    phrases: list[_Hit] = []
    for line_boxes in by_line.values():
        # Vision often returns whole phrases already; still try adjacent joins
        # for tesseract word tokens sharing a line_key.
        for start in range(len(line_boxes)):
            for end in range(start + 1, min(len(line_boxes), start + need_n + 2) + 1):
                chunk = line_boxes[start:end]
                left = min(b.left for b in chunk)
                top = min(b.top for b in chunk)
                right = max(b.left + b.width for b in chunk)
                bottom = max(b.top + b.height for b in chunk)
                phrases.append(
                    _Hit(
                        text=" ".join(b.text for b in chunk),
                        left=left,
                        top=top,
                        width=max(1, right - left),
                        height=max(1, bottom - top),
                        confidence=sum(b.confidence for b in chunk) / len(chunk),
                    )
                )
    return phrases


def synthetic_label_image(label: str, size: tuple[int, int] = (640, 200)) -> Image.Image:
    """Test helper: white canvas with black label text."""
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 70), label, fill="black", font=font)
    return image
