"""Execute mouse and keyboard actions via MacosUseSDK InputControllerTool."""

from __future__ import annotations

from typing import Optional

from command_parser.parser import Command
from screen_analyzer.capture import capture_screen
from shared_utils.coordinates import top_left_to_quartz

from errors import ActionError, InputError, ValidationError
from macos_input import MacosInputController
from validation import (
    validate_coordinates,
    validate_platform,
    validate_safety_zone,
    validate_text_input,
)


class ActionExecutor:
    """Executes commands by performing system-level actions."""

    def __init__(self, config_manager=None, input_controller: MacosInputController | None = None):
        self.config = config_manager
        self.input = input_controller or MacosInputController()
        self.safe_zones = self.config.get("safety.zones", []) if self.config else []
        validate_platform()

    def _screen_height(self) -> int:
        return capture_screen().height

    def _quartz_point(self, x: int, y: int) -> tuple[float, float]:
        validate_coordinates(x, y)
        return top_left_to_quartz(float(x), float(y), self._screen_height())

    async def execute(self, command: Command, target_element=None) -> bool:
        try:
            if command.intent == "click":
                return await self._execute_click(target_element)
            if command.intent == "type":
                return await self._execute_type(command.parameters.get("text", ""))
            if command.intent == "scroll":
                direction = command.parameters.get("direction", "down")
                return await self._execute_scroll(direction)
            if command.intent == "keypress":
                return await self._execute_keypress(command.parameters.get("key_combo", ""))
            raise InputError(f"Unsupported command intent: {command.intent}")
        except Exception as exc:
            if not isinstance(exc, ActionError):
                raise ActionError(f"Unexpected error during execution: {exc}") from exc
            raise

    async def _execute_click(self, target_element) -> bool:
        if not target_element or not hasattr(target_element, "center"):
            raise ValidationError("Invalid target element")

        x, y = target_element.center
        if self.safe_zones:
            validate_safety_zone(x, y, self.safe_zones)

        qx, qy = self._quartz_point(x, y)
        self.input.click(qx, qy, button="left", double=False)
        return True

    async def _execute_type(self, text: str) -> bool:
        validate_text_input(text)
        self.input.type_text(text)
        return True

    async def _execute_keypress(self, key_combo: str) -> bool:
        if not key_combo or not str(key_combo).strip():
            raise ValidationError("key_combo must not be empty")
        self.input.keypress(str(key_combo))
        return True

    async def _execute_scroll(self, direction: str) -> bool:
        if direction not in ["up", "down"]:
            raise InputError(f"Invalid scroll direction: {direction}")

        scroll_speed = self.config.get("action.scroll_speed", 100) if self.config else 100
        delta_y = scroll_speed if direction == "down" else -scroll_speed

        height = self._screen_height()
        qx, qy = top_left_to_quartz(height / 2, height / 2, height)
        self.input.scroll(qx, qy, delta_y, 0)
        return True
