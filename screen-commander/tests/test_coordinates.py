from shared_utils.coordinates import (
    display_scale_for_image,
    quartz_to_top_left,
    screenshot_to_quartz,
    top_left_to_quartz,
)


def test_top_left_round_trip():
    height = 1080
    qx, qy = top_left_to_quartz(100, 200, height)
    x, y = quartz_to_top_left(qx, qy, height)
    assert (x, y) == (100.0, 200.0)


def test_screenshot_to_quartz_hidpi_center(monkeypatch):
    monkeypatch.delenv("SCREEN_COMMANDER_SCALE", raising=False)
    monkeypatch.setattr(
        "shared_utils.coordinates.main_display_point_size",
        lambda: (1920.0, 1080.0),
    )
    # 4K screenshot, UI looks like 1080p → scale 2
    assert display_scale_for_image(3840, 2160) == 2.0
    qx, qy = screenshot_to_quartz(1920, 1080, image_width=3840, image_height=2160)
    assert (qx, qy) == (960.0, 540.0)


def test_screenshot_to_quartz_scale_override(monkeypatch):
    monkeypatch.setenv("SCREEN_COMMANDER_SCALE", "2")
    # No Y flip: pixels/scale only (top-left CGEvent points)
    qx, qy = screenshot_to_quartz(100, 50, image_width=3840, image_height=2160)
    assert (qx, qy) == (50.0, 25.0)


def test_screenshot_bottom_maps_high_y(monkeypatch):
    monkeypatch.setenv("SCREEN_COMMANDER_SCALE", "2")
    # Claude-style near-bottom click must stay near bottom (high Y), not flip to top
    qx, qy = screenshot_to_quartz(2080, 1800, image_width=3840, image_height=2160)
    assert qx == 1040.0
    assert qy == 900.0
