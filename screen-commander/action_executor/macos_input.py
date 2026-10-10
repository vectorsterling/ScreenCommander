"""Drive MacosUseSDK InputControllerTool for keyboard and mouse actions."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path

from errors import ActionError, InputError


class MacosInputController:
    """Shell out to MacosUseSDK's InputControllerTool (Swift / CGEvent)."""

    def __init__(self, tool_path: str | None = None):
        self.tool_path = tool_path or self._resolve_tool_path()
        self._left_button_held = False

    @staticmethod
    def _resolve_tool_path() -> str:
        env_path = os.getenv("MACOS_USE_INPUT_TOOL")
        if env_path:
            path = Path(env_path).expanduser()
            if path.is_file():
                return str(path)
            raise FileNotFoundError(f"MACOS_USE_INPUT_TOOL not found: {env_path}")

        sdk_root = Path(os.getenv("MACOS_USE_SDK_ROOT", "")).expanduser()
        if not sdk_root or not sdk_root.exists():
            sdk_root = Path(__file__).resolve().parents[1].parent / "MacosUseSDK"

        candidates = [
            sdk_root / ".build" / "release" / "InputControllerTool",
            sdk_root / ".build" / "debug" / "InputControllerTool",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)

        raise FileNotFoundError(
            "InputControllerTool not found. Build MacosUseSDK with "
            "`swift build -c release` and set MACOS_USE_INPUT_TOOL or MACOS_USE_SDK_ROOT."
        )

    def run(self, *args: str, capture_stdout: bool = False) -> str:
        command = [self.tool_path, *args]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise ActionError(f"InputControllerTool failed: {detail or command}")
        return (result.stdout or "").strip() if capture_stdout else ""

    def click(
        self,
        x: float,
        y: float,
        *,
        button: str = "left",
        double: bool = False,
        triple: bool = False,
        modifiers: str | None = None,
    ) -> None:
        if triple:
            action = "tripleclick"
        elif double:
            action = "doubleclick"
        elif button == "right":
            action = "rightclick"
        elif button == "middle":
            action = "middleclick"
        elif button == "left":
            action = "click"
        else:
            raise InputError(f"Unsupported mouse button: {button}")

        args = [action, str(x), str(y)]
        if modifiers:
            args.append(modifiers)
        self.run(*args)

    def mouse_down(self, x: float, y: float) -> None:
        self.run("mousedown", str(x), str(y))
        self._left_button_held = True

    def mouse_up(self, x: float, y: float) -> None:
        self.run("mouseup", str(x), str(y))
        self._left_button_held = False

    def move(self, x: float, y: float) -> None:
        if self._left_button_held:
            self.run("mousedragto", str(x), str(y))
        else:
            self.run("mousemove", str(x), str(y))

    def drag(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        steps: int = 16,
        modifiers: str | None = None,
    ) -> None:
        args = ["drag", str(x1), str(y1), str(x2), str(y2), str(steps)]
        if modifiers:
            args.append(modifiers)
        self.run(*args)
        self._left_button_held = False

    def scroll(
        self,
        x: float,
        y: float,
        delta_y: int,
        delta_x: int = 0,
        *,
        modifiers: str | None = None,
    ) -> None:
        args = ["scroll", str(x), str(y), str(int(delta_y)), str(int(delta_x))]
        if modifiers:
            args.append(modifiers)
        self.run(*args)

    def keypress(self, key_combo: str) -> None:
        combo = key_combo.strip()
        if not combo:
            raise InputError("key_combo must not be empty")
        self.run("keypress", combo)

    def hold_key(self, key_combo: str, duration: float) -> None:
        combo = key_combo.strip()
        if not combo:
            raise InputError("key_combo must not be empty")
        if duration is None:
            raise InputError("duration is required for hold_key")
        self.run("holdkey", combo, str(float(duration)))

    def type_text(self, text: str) -> None:
        if not text:
            raise InputError("text must not be empty")
        self.run("writetext", text)

    def cursor_position_quartz(self) -> tuple[float, float]:
        out = self.run("cursorpos", capture_stdout=True)
        parts = out.split()
        if len(parts) < 2:
            raise ActionError(f"cursorpos returned unexpected output: {out!r}")
        return float(parts[0]), float(parts[1])

    @property
    def left_button_held(self) -> bool:
        return self._left_button_held

    @staticmethod
    def quote_for_log(*args: str) -> str:
        return " ".join(shlex.quote(part) for part in args)
