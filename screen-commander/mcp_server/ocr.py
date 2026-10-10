"""Screen OCR: prefer macOS Vision (PyObjC), fall back to pytesseract."""

from __future__ import annotations

import io
import logging
import os
from dataclasses import dataclass
from typing import Literal

from PIL import Image

logger = logging.getLogger(__name__)

OcrBackend = Literal["vision", "tesseract"]

_vision_available: bool | None = None


@dataclass(frozen=True)
class OcrBox:
    """One recognized text region in screenshot-pixel top-left space."""

    text: str
    left: int
    top: int
    width: int
    height: int
    confidence: float  # 0..1
    # Line grouping key (Vision: observation index; Tesseract: block/par/line).
    line_key: tuple[int, ...] = (0,)


def vision_available() -> bool:
    global _vision_available
    if _vision_available is not None:
        return _vision_available
    try:
        import Vision  # noqa: F401
        from Foundation import NSData  # noqa: F401

        _vision_available = True
    except Exception:
        _vision_available = False
    return _vision_available


def recognize_text(image: Image.Image) -> tuple[list[OcrBox], OcrBackend]:
    """
    Run OCR on ``image``.

    Prefers ``VNRecognizeTextRequest`` via PyObjC; falls back to pytesseract
    when Vision/PyObjC is unavailable or fails.
    """
    if vision_available():
        try:
            return _recognize_vision(image), "vision"
        except Exception as exc:
            logger.warning("Vision OCR failed (%s); falling back to pytesseract", exc)

    return _recognize_tesseract(image), "tesseract"


def _recognize_vision(image: Image.Image) -> list[OcrBox]:
    import Vision
    from Foundation import NSData

    rgb = image.convert("RGB")
    width, height = rgb.size
    buf = io.BytesIO()
    rgb.save(buf, format="PNG")
    png = buf.getvalue()
    ns_data = NSData.dataWithBytes_length_(png, len(png))

    request = Vision.VNRecognizeTextRequest.alloc().init()
    # Accurate is still fast on Apple Silicon and better for UI labels.
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(False)
    lang = os.getenv("OCR_LANGUAGE", "").strip()
    if lang and lang not in {"eng", "en"}:
        # Vision wants BCP-47-ish codes; map common tesseract-style names.
        mapped = {"eng": "en-US", "en": "en-US"}.get(lang, lang)
        try:
            request.setRecognitionLanguages_([mapped])
        except Exception:
            pass

    handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(ns_data, None)
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(f"VNRecognizeTextRequest failed: {error}")

    boxes: list[OcrBox] = []
    results = request.results() or []
    for idx, observation in enumerate(results):
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue
        candidate = candidates[0]
        text = str(candidate.string() or "").strip()
        if not text:
            continue
        confidence = float(candidate.confidence())
        # Vision boundingBox: normalized, origin bottom-left.
        bbox = observation.boundingBox()
        ox = float(bbox.origin.x)
        oy = float(bbox.origin.y)
        ow = float(bbox.size.width)
        oh = float(bbox.size.height)
        left = int(round(ox * width))
        top = int(round((1.0 - oy - oh) * height))
        box_w = max(1, int(round(ow * width)))
        box_h = max(1, int(round(oh * height)))
        boxes.append(
            OcrBox(
                text=text,
                left=left,
                top=top,
                width=box_w,
                height=box_h,
                confidence=confidence,
                line_key=(idx,),
            )
        )
    return boxes


def _recognize_tesseract(image: Image.Image) -> list[OcrBox]:
    import pytesseract

    _DEFAULT_TESSERACT = "/opt/homebrew/bin/tesseract"
    if os.path.isfile(_DEFAULT_TESSERACT):
        pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", _DEFAULT_TESSERACT)

    lang = os.getenv("OCR_LANGUAGE", "eng")
    data = pytesseract.image_to_data(image, lang=lang, output_type=pytesseract.Output.DICT)
    boxes: list[OcrBox] = []
    n = len(data["text"])
    for i in range(n):
        raw = (data["text"][i] or "").strip()
        if not raw:
            continue
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if conf < 0:
            continue
        boxes.append(
            OcrBox(
                text=raw,
                left=int(data["left"][i]),
                top=int(data["top"][i]),
                width=max(1, int(data["width"][i])),
                height=max(1, int(data["height"][i])),
                confidence=conf / 100.0,
                line_key=(
                    int(data.get("block_num", [0] * n)[i]),
                    int(data.get("par_num", [0] * n)[i]),
                    int(data.get("line_num", [0] * n)[i]),
                ),
            )
        )
    return boxes
