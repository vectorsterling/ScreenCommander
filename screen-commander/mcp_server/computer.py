"""Anthropic computer-use action dispatcher for Screen Commander MCP."""

from __future__ import annotations

import io
import os
import time
from typing import Any, Literal

from PIL import Image as PILImage

from action_executor.macos_input import MacosInputController
from screen_analyzer.capture import ScreenCaptureError, capture_screen
from shared_utils.coordinates import (
    clear_display_geometry_cache,
    display_scale_for_image,
    quartz_to_top_left,
    screenshot_to_quartz,
)

SUPPORTED_ACTIONS: tuple[str, ...] = (
    "screenshot",
    "left_click",
    "right_click",
    "middle_click",
    "double_click",
    "triple_click",
    "mouse_move",
    "left_click_drag",
    "left_mouse_down",
    "left_mouse_up",
    "scroll",
    "type",
    "key",
    "hold_key",
    "wait",
    "cursor_position",
    "zoom",
)

ScrollDirection = Literal["up", "down", "left", "right"]


class ComputerActionError(ValueError):
    """Invalid computer-use arguments or unsupported action."""


def _require_coordinate(value: Any, name: str) -> tuple[float, float]:
    if value is None:
        raise ComputerActionError(f"Invalid argument: '{name}' is required as [x, y].")
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ComputerActionError(
            f"Invalid argument: '{name}' must be a [x, y] array of two numbers, got {value!r}."
        )
    try:
        return float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ComputerActionError(
            f"Invalid argument: '{name}' values must be numbers, got {value!r}."
        ) from exc


def _optional_coordinate(value: Any, name: str) -> tuple[float, float] | None:
    if value is None:
        return None
    return _require_coordinate(value, name)


def _normalize_modifiers(text: str | None) -> str | None:
    if text is None:
        return None
    raw = text.strip()
    if not raw:
        return None
    # Allow Anthropic "super" alias; Swift tool also accepts it.
    parts = [p.strip().lower() for p in raw.split("+") if p.strip()]
    allowed = {
        "cmd",
        "command",
        "super",
        "win",
        "meta",
        "shift",
        "alt",
        "option",
        "opt",
        "ctrl",
        "control",
        "fn",
        "function",
    }
    bad = [p for p in parts if p not in allowed]
    if bad:
        raise ComputerActionError(
            f"Invalid argument: modifier text {text!r} has unknown part(s) {bad}. "
            "Valid: cmd, shift, alt/option, ctrl, fn (combine with +)."
        )
    return "+".join(parts)


class ComputerUseController:
    """Maps Anthropic computer-use actions onto MacosInputController + capture."""

    def __init__(self, input_controller: MacosInputController | None = None):
        self.input = input_controller or MacosInputController()

    def _image_size(self) -> tuple[int, int]:
        image = capture_screen()
        return image.width, image.height

    def _to_quartz(self, x: float, y: float, width: int, height: int) -> tuple[float, float]:
        return screenshot_to_quartz(x, y, image_width=width, image_height=height)

    def _resolve_point(
        self,
        coordinate: Any,
        *,
        required: bool,
        name: str = "coordinate",
        width: int | None = None,
        height: int | None = None,
    ) -> tuple[float, float]:
        if width is None or height is None:
            width, height = self._image_size()
        if coordinate is None:
            if required:
                raise ComputerActionError(f"Invalid argument: '{name}' is required as [x, y].")
            qx, qy = self.input.cursor_position_quartz()
            return qx, qy
        x, y = _require_coordinate(coordinate, name)
        return self._to_quartz(x, y, width, height)

    def screenshot(self, display_index: int | None = None) -> PILImage.Image:
        clear_display_geometry_cache()
        try:
            return capture_screen(display_index)
        except ScreenCaptureError as exc:
            raise RuntimeError(str(exc)) from exc

    def zoom(self, region: Any) -> PILImage.Image:
        """Return a cropped screenshot for region [x0, y0, x1, y1] in screenshot pixels."""
        if not isinstance(region, (list, tuple)) or len(region) != 4:
            raise ComputerActionError(
                "Invalid argument: 'region' must be [x0, y0, x1, y1] in screenshot pixels."
            )
        try:
            x0, y0, x1, y1 = (int(region[0]), int(region[1]), int(region[2]), int(region[3]))
        except (TypeError, ValueError) as exc:
            raise ComputerActionError(
                f"Invalid argument: 'region' values must be numbers, got {region!r}."
            ) from exc
        if x1 <= x0 or y1 <= y0:
            raise ComputerActionError(
                f"Invalid argument: 'region' must have x1>x0 and y1>y0, got {region!r}."
            )
        image = self.screenshot()
        x0 = max(0, min(x0, image.width - 1))
        y0 = max(0, min(y0, image.height - 1))
        x1 = max(x0 + 1, min(x1, image.width))
        y1 = max(y0 + 1, min(y1, image.height))
        return image.crop((x0, y0, x1, y1))

    def cursor_position(self) -> dict[str, float]:
        width, height = self._image_size()
        qx, qy = self.input.cursor_position_quartz()
        scale = display_scale_for_image(width, height)
        # Quartz bottom-left points → screenshot top-left pixels
        x_pt, y_from_top_pt = quartz_to_top_left(qx, qy, height / scale)
        return {"x": x_pt * scale, "y": y_from_top_pt * scale}

    def wait(self, duration: Any) -> str:
        if duration is None:
            raise ComputerActionError("Invalid argument: 'duration' is required for wait (seconds).")
        try:
            seconds = float(duration)
        except (TypeError, ValueError) as exc:
            raise ComputerActionError(
                f"Invalid argument: 'duration' must be a number of seconds, got {duration!r}."
            ) from exc
        if seconds < 0:
            raise ComputerActionError("Invalid argument: 'duration' must be >= 0.")
        seconds = min(seconds, 30.0)
        time.sleep(seconds)
        return f"waited {seconds}s"

    def dispatch(self, action: str, params: dict[str, Any]) -> Any:
        action = (action or "").strip()
        if action not in SUPPORTED_ACTIONS:
            raise ComputerActionError(
                f"Unsupported action {action!r}. Supported actions: {', '.join(SUPPORTED_ACTIONS)}."
            )

        if action == "screenshot":
            return self.screenshot(params.get("display_index"))

        if action == "zoom":
            return self.zoom(params.get("region") or params.get("coordinate"))

        if action == "wait":
            return self.wait(params.get("duration"))

        if action == "cursor_position":
            return self.cursor_position()

        if action == "type":
            text = params.get("text")
            if not isinstance(text, str) or text == "":
                raise ComputerActionError("Invalid argument: 'text' is required for type.")
            self.input.type_text(text)
            return f"typed {len(text)} characters"

        if action == "key":
            text = params.get("text")
            if not isinstance(text, str) or not text.strip():
                raise ComputerActionError("Invalid argument: 'text' is required for key.")
            repeat = int(params.get("repeat") or 1)
            if repeat < 1 or repeat > 100:
                raise ComputerActionError("Invalid argument: 'repeat' must be 1..100.")
            for _ in range(repeat):
                self.input.keypress(text)
            return f"key {text!r} x{repeat}"

        if action == "hold_key":
            text = params.get("text")
            duration = params.get("duration")
            if not isinstance(text, str) or not text.strip():
                raise ComputerActionError("Invalid argument: 'text' is required for hold_key.")
            if duration is None:
                raise ComputerActionError(
                    "Invalid argument: 'duration' (seconds) is required for hold_key."
                )
            try:
                seconds = float(duration)
            except (TypeError, ValueError) as exc:
                raise ComputerActionError(
                    f"Invalid argument: 'duration' must be a number, got {duration!r}."
                ) from exc
            if seconds < 0:
                raise ComputerActionError("Invalid argument: 'duration' must be >= 0.")
            self.input.hold_key(text, min(seconds, 30.0))
            return f"held {text!r} for {min(seconds, 30.0)}s"

        width, height = self._image_size()
        mods = _normalize_modifiers(params.get("text") if action != "type" else None)

        if action == "mouse_move":
            qx, qy = self._resolve_point(params.get("coordinate"), required=True, width=width, height=height)
            self.input.move(qx, qy)
            return f"mouse_move -> quartz ({qx:.1f}, {qy:.1f})"

        if action == "left_mouse_down":
            qx, qy = self._resolve_point(
                params.get("coordinate"), required=False, width=width, height=height
            )
            self.input.mouse_down(qx, qy)
            return f"left_mouse_down at quartz ({qx:.1f}, {qy:.1f})"

        if action == "left_mouse_up":
            qx, qy = self._resolve_point(
                params.get("coordinate"), required=False, width=width, height=height
            )
            self.input.mouse_up(qx, qy)
            return f"left_mouse_up at quartz ({qx:.1f}, {qy:.1f})"

        if action == "left_click_drag":
            start = _require_coordinate(params.get("start_coordinate"), "start_coordinate")
            end = _require_coordinate(params.get("coordinate"), "coordinate")
            sx, sy = self._to_quartz(start[0], start[1], width, height)
            ex, ey = self._to_quartz(end[0], end[1], width, height)
            self.input.drag(sx, sy, ex, ey, steps=16, modifiers=mods)
            return f"left_click_drag ({start}) -> ({end})"

        if action == "scroll":
            direction = params.get("scroll_direction")
            if direction not in ("up", "down", "left", "right"):
                raise ComputerActionError(
                    "Invalid argument: 'scroll_direction' must be one of up, down, left, right."
                )
            amount = params.get("scroll_amount", 3)
            try:
                amount_i = int(amount)
            except (TypeError, ValueError) as exc:
                raise ComputerActionError(
                    f"Invalid argument: 'scroll_amount' must be an integer, got {amount!r}."
                ) from exc
            if amount_i < 0 or amount_i > 100:
                raise ComputerActionError("Invalid argument: 'scroll_amount' must be 0..100.")
            qx, qy = self._resolve_point(
                params.get("coordinate"), required=False, width=width, height=height
            )
            # CGEvent wheel1: positive scrolls up; Claude "down" = content moves down = negative.
            # Amplify so scroll_amount 5–10 actually moves TextEdit / chat views.
            factor = int(os.getenv("SCREEN_COMMANDER_SCROLL_FACTOR", "40"))
            delta_y = 0
            delta_x = 0
            if direction == "down":
                delta_y = -amount_i * factor
            elif direction == "up":
                delta_y = amount_i * factor
            elif direction == "right":
                delta_x = amount_i * factor
            else:
                delta_x = -amount_i * factor
            # text on scroll is modifiers only
            scroll_mods = _normalize_modifiers(params.get("text"))
            self.input.scroll(qx, qy, delta_y, delta_x, modifiers=scroll_mods)
            return f"scroll {direction} amount={amount_i} at quartz ({qx:.1f}, {qy:.1f})"

        # Clicks
        click_map = {
            "left_click": ("left", False, False),
            "right_click": ("right", False, False),
            "middle_click": ("middle", False, False),
            "double_click": ("left", True, False),
            "triple_click": ("left", False, True),
        }
        if action in click_map:
            button, double, triple = click_map[action]
            # coordinate optional for clicks (defaults to current cursor)
            qx, qy = self._resolve_point(
                params.get("coordinate"), required=False, width=width, height=height
            )
            self.input.click(qx, qy, button=button, double=double, triple=triple, modifiers=mods)
            return f"{action} at quartz ({qx:.1f}, {qy:.1f})"

        raise ComputerActionError(f"Unhandled action {action!r}.")


def image_to_png_bytes(image: PILImage.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
