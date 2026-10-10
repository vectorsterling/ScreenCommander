"""Screen Commander MCP server — Anthropic computer-use + MacosUseSDK input."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Literal

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "action_executor"))

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.utilities.types import Image
from mcp.server.transport_security import TransportSecuritySettings

from action_executor.macos_input import MacosInputController
from mcp_server.computer import (
    SUPPORTED_ACTIONS,
    ComputerActionError,
    ComputerUseController,
    image_to_png_bytes,
)
from mcp_server.find_click import find_and_click as _find_and_click
from mcp_server.human_help import human_help as _human_help
from mcp_server.shell import run_shell as _run_shell
from shared_utils.coordinates import screenshot_to_quartz

load_dotenv()

_mcp = MCPServer("screen-commander")
_input: MacosInputController | None = None
_computer: ComputerUseController | None = None


def _input_controller() -> MacosInputController:
    global _input
    if _input is None:
        _input = MacosInputController()
    return _input


def _computer_controller() -> ComputerUseController:
    global _computer
    if _computer is None:
        _computer = ComputerUseController(_input_controller())
    return _computer


@_mcp.tool(
    name="computer",
    description=(
        "Anthropic computer-use actions on the Mac (screenshot pixels → Quartz points, HiDPI-aware). "
        f"Supported actions: {', '.join(SUPPORTED_ACTIONS)}. "
        "Coordinates are [x, y] in screenshot-pixel top-left space. "
        "For clicks/scroll, optional text holds modifiers (cmd, shift, alt/option, ctrl). "
        "scroll_direction left/right uses horizontal scroll-wheel axis 2."
    ),
)
def computer(
    action: Literal[
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
    ],
    coordinate: list[float] | None = None,
    start_coordinate: list[float] | None = None,
    text: str | None = None,
    duration: float | None = None,
    scroll_direction: Literal["up", "down", "left", "right"] | None = None,
    scroll_amount: int | None = None,
    repeat: int | None = None,
    region: list[float] | None = None,
    display_index: int | None = None,
) -> Any:
    params: dict[str, Any] = {
        "coordinate": coordinate,
        "start_coordinate": start_coordinate,
        "text": text,
        "duration": duration,
        "scroll_direction": scroll_direction,
        "scroll_amount": scroll_amount if scroll_amount is not None else 3,
        "repeat": repeat if repeat is not None else 1,
        "region": region,
        "display_index": display_index,
    }
    try:
        result = _computer_controller().dispatch(action, params)
    except ComputerActionError as exc:
        raise RuntimeError(str(exc)) from exc

    if hasattr(result, "save"):
        return Image(data=image_to_png_bytes(result), format="png")
    if isinstance(result, dict):
        return result
    return str(result)


@_mcp.tool(
    name="run_shell",
    description=(
        "Execute a shell command on this Mac with /bin/zsh -lc (headless; no Terminal.app). "
        "Returns structured JSON object: {stdout, stderr, exit_code}. "
        "timeout is seconds (default 30, max 300). On timeout the process group is killed "
        "and exit_code is -1. Same transport auth/allow-list as other tools "
        "(MCP_ALLOWED_HOSTS / MCP_ALLOWED_ORIGINS); no per-command allow-list."
    ),
)
def run_shell(command: str, timeout: int = 30) -> dict[str, Any]:
    try:
        return _run_shell(command, timeout=timeout)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


@_mcp.tool(
    name="find_and_click",
    description=(
        "Takes a screenshot (or crops to optional region [x0,y0,x1,y1]), runs OCR to locate "
        "the given text, and returns/clicks the center of the best match. "
        "OCR prefers macOS Vision (VNRecognizeTextRequest); falls back to pytesseract. "
        "Coordinates are screenshot-pixel top-left (same as computer tool). "
        "Returns {found, x, y, confidence, clicked}. click defaults to true."
    ),
)
def find_and_click(
    text: str,
    click: bool = True,
    region: list[float] | None = None,
) -> dict[str, Any]:
    try:
        return _find_and_click(text, click=click, region=region, input_controller=_input_controller())
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


@_mcp.tool(
    name="human_help",
    description=(
        "Ask a person for help. Shows `text` (a paragraph describing what you need) "
        "in a full-screen always-on-top overlay with a Done button. "
        "Returns {success: true, status: 'completed', detail} when they click Done. "
        "If Done is not clicked within 5 minutes, returns "
        "{success: false, status: 'timeout', detail}. "
        "A chime plays immediately and then every 30 seconds while waiting. "
        "The overlay closes only when Done is clicked or the 5 minutes elapse."
    ),
)
def human_help(text: str) -> dict[str, Any]:
    try:
        return _human_help(text)
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc


# --- Legacy tools (kept for existing clients) ---


@_mcp.tool(
    name="get_screenshot",
    description="Capture the main display PNG. Prefer action=screenshot on the computer tool.",
)
def get_screenshot(display_index: int | None = None) -> Image:
    try:
        image = _computer_controller().screenshot(display_index)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    return Image(data=image_to_png_bytes(image), format="png")


@_mcp.tool(description="Legacy click. Prefer computer tool left_click/right_click/double_click.")
def mouse_click(
    x: float,
    y: float,
    button: Literal["left", "right"] = "left",
    double_click: bool = False,
    screen_height: int | None = None,
) -> str:
    _ = screen_height
    action = "double_click" if double_click else ("right_click" if button == "right" else "left_click")
    return str(_computer_controller().dispatch(action, {"coordinate": [x, y]}))


@_mcp.tool(description="Legacy move. Prefer computer tool mouse_move.")
def mouse_move(x: float, y: float, screen_height: int | None = None) -> str:
    _ = screen_height
    return str(_computer_controller().dispatch("mouse_move", {"coordinate": [x, y]}))


@_mcp.tool(description="Legacy scroll by deltas. Prefer computer tool scroll with scroll_direction.")
def mouse_scroll(
    x: float,
    y: float,
    delta_y: int,
    delta_x: int = 0,
    screen_height: int | None = None,
) -> str:
    _ = screen_height
    from screen_analyzer.capture import capture_screen

    image = capture_screen()
    qx, qy = screenshot_to_quartz(x, y, image_width=image.width, image_height=image.height)
    _input_controller().scroll(qx, qy, delta_y, delta_x)
    return f"Scrolled at ({x}, {y}) delta_y={delta_y} delta_x={delta_x}"


@_mcp.tool(description="Legacy keypress. Prefer computer tool key.")
def keyboard_keypress(key_combo: str) -> str:
    return str(_computer_controller().dispatch("key", {"text": key_combo}))


@_mcp.tool(description="Legacy type. Prefer computer tool type.")
def keyboard_type(text: str) -> str:
    return str(_computer_controller().dispatch("type", {"text": text}))


def create_server() -> MCPServer:
    return _mcp


def transport_security_settings() -> TransportSecuritySettings | None:
    if os.getenv("MCP_DISABLE_DNS_REBINDING", "").lower() in {"1", "true", "yes"}:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    allowed = os.getenv("MCP_ALLOWED_HOSTS", "").strip()
    if not allowed:
        return None

    hosts = [part.strip() for part in allowed.split(",") if part.strip()]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[
            part.strip()
            for part in os.getenv("MCP_ALLOWED_ORIGINS", "").split(",")
            if part.strip()
        ],
    )
