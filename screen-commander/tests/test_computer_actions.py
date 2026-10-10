"""Unit tests for computer-use action dispatch (no live CGEvent required for most)."""

from __future__ import annotations

import pytest

from mcp_server.computer import (
    SUPPORTED_ACTIONS,
    ComputerActionError,
    ComputerUseController,
    _normalize_modifiers,
    _require_coordinate,
)


class FakeInput:
    def __init__(self):
        self.calls: list[tuple] = []
        self._left_button_held = False
        self._cursor = (100.0, 200.0)

    def click(self, x, y, *, button="left", double=False, triple=False, modifiers=None):
        self.calls.append(("click", x, y, button, double, triple, modifiers))

    def mouse_down(self, x, y):
        self._left_button_held = True
        self.calls.append(("mouse_down", x, y))

    def mouse_up(self, x, y):
        self._left_button_held = False
        self.calls.append(("mouse_up", x, y))

    def move(self, x, y):
        kind = "mousedragto" if self._left_button_held else "mousemove"
        self.calls.append((kind, x, y))
        self._cursor = (x, y)

    def drag(self, x1, y1, x2, y2, *, steps=16, modifiers=None):
        self.calls.append(("drag", x1, y1, x2, y2, steps, modifiers))
        self._left_button_held = False

    def scroll(self, x, y, delta_y, delta_x=0, *, modifiers=None):
        self.calls.append(("scroll", x, y, delta_y, delta_x, modifiers))

    def keypress(self, key_combo):
        self.calls.append(("keypress", key_combo))

    def hold_key(self, key_combo, duration):
        self.calls.append(("hold_key", key_combo, duration))

    def type_text(self, text):
        self.calls.append(("type_text", text))

    def cursor_position_quartz(self):
        return self._cursor


@pytest.fixture
def ctrl(monkeypatch):
    fake = FakeInput()
    c = ComputerUseController(fake)  # type: ignore[arg-type]

    class FakeImage:
        width = 3840
        height = 2160

        def crop(self, box):
            self.last_crop = box
            return self

        def save(self, *a, **k):
            pass

    monkeypatch.setattr("mcp_server.computer.capture_screen", lambda *a, **k: FakeImage())
    monkeypatch.setattr(
        "mcp_server.computer.display_scale_for_image",
        lambda w, h: 2.0,
    )
    monkeypatch.setattr(
        "mcp_server.computer.main_display_point_size"
        if False
        else "shared_utils.coordinates.main_display_point_size",
        lambda: (1920.0, 1080.0),
    )
    return c, fake


def test_supported_actions_include_new_ones():
    for name in (
        "left_click_drag",
        "left_mouse_down",
        "left_mouse_up",
        "middle_click",
        "triple_click",
        "hold_key",
    ):
        assert name in SUPPORTED_ACTIONS


def test_require_coordinate_errors():
    with pytest.raises(ComputerActionError, match="required"):
        _require_coordinate(None, "coordinate")
    with pytest.raises(ComputerActionError, match="two numbers"):
        _require_coordinate([1], "coordinate")


def test_normalize_modifiers():
    assert _normalize_modifiers("cmd+shift") == "cmd+shift"
    with pytest.raises(ComputerActionError, match="unknown"):
        _normalize_modifiers("cmd+foo")


def test_left_click_drag(ctrl):
    c, fake = ctrl
    c.dispatch(
        "left_click_drag",
        {"start_coordinate": [100, 200], "coordinate": [300, 400]},
    )
    assert fake.calls[0][0] == "drag"
    # HiDPI scale 2, top-left points (no Y flip): (100,200)->(50,100), (300,400)->(150,200)
    assert fake.calls[0][1:5] == (50.0, 100.0, 150.0, 200.0)


def test_left_mouse_down_up_and_dragged_move(ctrl):
    c, fake = ctrl
    c.dispatch("left_mouse_down", {"coordinate": [100, 100]})
    assert fake.calls[-1][0] == "mouse_down"
    c.dispatch("mouse_move", {"coordinate": [200, 100]})
    assert fake.calls[-1][0] == "mousedragto"
    c.dispatch("left_mouse_up", {"coordinate": [200, 100]})
    assert fake.calls[-1][0] == "mouse_up"


def test_middle_and_triple_click(ctrl):
    c, fake = ctrl
    c.dispatch("middle_click", {"coordinate": [10, 10]})
    assert fake.calls[-1][3] == "middle"
    c.dispatch("triple_click", {"coordinate": [10, 10]})
    assert fake.calls[-1][5] is True  # triple


def test_modifier_click(ctrl):
    c, fake = ctrl
    c.dispatch("left_click", {"coordinate": [10, 10], "text": "cmd+shift"})
    assert fake.calls[-1][6] == "cmd+shift"


def test_hold_key(ctrl):
    c, fake = ctrl
    c.dispatch("hold_key", {"text": "shift", "duration": 1.5})
    assert fake.calls[-1] == ("hold_key", "shift", 1.5)
    with pytest.raises(ComputerActionError, match="duration"):
        c.dispatch("hold_key", {"text": "shift"})


def test_scroll_horizontal_and_modifiers(ctrl):
    c, fake = ctrl
    c.dispatch(
        "scroll",
        {
            "coordinate": [100, 100],
            "scroll_direction": "left",
            "scroll_amount": 5,
            "text": "shift",
        },
    )
    kind, x, y, dy, dx, mods = fake.calls[-1]
    assert kind == "scroll"
    assert dy == 0 and dx == -5 * 40  # default SCROLL_FACTOR
    assert mods == "shift"
    c.dispatch(
        "scroll",
        {"coordinate": [100, 100], "scroll_direction": "right", "scroll_amount": 2},
    )
    assert fake.calls[-1][4] == 2 * 40
    c.dispatch(
        "scroll",
        {"coordinate": [100, 100], "scroll_direction": "down", "scroll_amount": 3},
    )
    # down → negative wheel1 (CGEvent convention)
    assert fake.calls[-1][3] == -3 * 40


def test_unsupported_action(ctrl):
    c, _ = ctrl
    with pytest.raises(ComputerActionError, match="Unsupported action"):
        c.dispatch("teleport", {})
