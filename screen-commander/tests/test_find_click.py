from unittest.mock import MagicMock

from mcp_server.find_click import find_and_click, synthetic_label_image
from mcp_server.ocr import recognize_text, vision_available


def test_ocr_prefers_vision_when_available():
    assert vision_available() is True
    image = synthetic_label_image("VisionPath")
    boxes, backend = recognize_text(image)
    assert backend == "vision"
    joined = " ".join(b.text for b in boxes).lower()
    assert "visionpath" in joined.replace(" ", "")


def test_ocr_falls_back_to_tesseract(monkeypatch):
    image = synthetic_label_image("TessFallback")
    monkeypatch.setattr("mcp_server.ocr.vision_available", lambda: False)
    boxes, backend = recognize_text(image)
    assert backend == "tesseract"
    joined = " ".join(b.text for b in boxes).lower()
    assert "tessfallback" in joined.replace(" ", "")


def test_find_without_click():
    image = synthetic_label_image("Submit")
    result = find_and_click("Submit", click=False, image=image)
    assert result["found"] is True
    assert result["clicked"] is False
    assert isinstance(result["x"], float)
    assert isinstance(result["y"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    assert 0 < result["x"] < image.width
    assert 0 < result["y"] < image.height


def test_find_and_click_invokes_input():
    image = synthetic_label_image("Cancel")
    mock = MagicMock()
    result = find_and_click("Cancel", click=True, image=image, input_controller=mock)
    assert result["found"] is True
    assert result["clicked"] is True
    mock.click.assert_called_once()
    args, kwargs = mock.click.call_args
    assert kwargs.get("button") == "left"
    assert len(args) == 2


def test_find_missing_text():
    image = synthetic_label_image("Hello")
    result = find_and_click("DefinitelyNotOnScreenXYZ", click=False, image=image)
    assert result == {
        "found": False,
        "x": None,
        "y": None,
        "confidence": 0.0,
        "clicked": False,
    }


def test_find_in_region_offsets_coords():
    from PIL import Image

    label = synthetic_label_image("Open", size=(400, 120))
    canvas = Image.new("RGB", (800, 400), "white")
    canvas.paste(label, (100, 50))
    result = find_and_click(
        "Open",
        click=False,
        region=[100, 50, 500, 170],
        image=canvas,
    )
    assert result["found"] is True
    assert 100 < result["x"] < 500
    assert 50 < result["y"] < 170


def test_rejects_empty_text():
    try:
        find_and_click("  ", click=False, image=synthetic_label_image("x"))
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "non-empty" in str(exc)
