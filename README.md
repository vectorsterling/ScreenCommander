# ScreenCommander

ScreenCommander lets a language model see and operate a Mac. It captures the screen, finds text, and sends clicks, keystrokes, and scrolls through an [MCP](https://modelcontextprotocol.io) server. Mouse and keyboard events go through [MacosUseSDK](MacosUseSDK/README.md) (`InputControllerTool`, Swift / CGEvent).

The Python package lives in [`screen-commander/`](screen-commander/). This repository also contains the MacosUseSDK checkout the input tool is built from.

## Features

- **Computer use.** Screenshot, click, drag, scroll, type, and key actions. Coordinates are screenshot pixels from the top left and are converted to Quartz points, including on HiDPI displays.
- **Find and click.** OCR locates text on the screen (macOS Vision, with pytesseract as a fallback) and can click the match.
- **Shell.** Run a command with `/bin/zsh -lc` and get stdout, stderr, and an exit code.
- **Human help.** Show a full-screen overlay when the model needs a person, and wait until they click Done or the request times out.
- **Remote clients.** The MCP server speaks SSE and can listen on the LAN so Cursor on another machine can drive this Mac.

## Requirements

- macOS
- Python 3.10 or newer (3.13 is a good match for the current dependency set)
- Xcode with Swift 6 (Xcode 16+) to build `InputControllerTool`
- **Accessibility** and **Screen Recording** permission for the app that runs the server (Terminal, iTerm, or the Python process)

`find_and_click` uses the system Vision framework when PyObjC is installed. The pytesseract fallback needs the `tesseract` binary on `PATH`.

## Install

Clone the repository:

```bash
git clone https://github.com/vectorsterling/ScreenCommander.git
cd ScreenCommander
```

### Installer

From the repo root, double-click **Install Screen Commander.command**, or run:

```bash
chmod +x "Install Screen Commander.command" scripts/install.sh
./scripts/install.sh "$(pwd)"
```

Pass `--launch-agent` to install a LaunchAgent that starts the MCP server at login:

```bash
./scripts/install.sh "$(pwd)" --launch-agent
```

The installer builds `InputControllerTool` in release mode, creates `screen-commander/.venv`, installs `screen-commander/requirements.txt`, and writes `screen-commander/.env` from `.env.example` if that file is missing. It also opens the Accessibility and Screen Recording panes.

### Manual setup

```bash
cd screen-commander
chmod +x scripts/build-macos-use-sdk.sh scripts/run-mcp.sh
./scripts/build-macos-use-sdk.sh

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `MACOS_USE_SDK_ROOT` in `.env` if MacosUseSDK is not at `../MacosUseSDK`. LLM keys in `.env` are only needed for the older language-model integrations, not for the MCP server itself.

## Use the MCP server

From `screen-commander`, with the virtualenv activated:

```bash
./scripts/run-mcp.sh
```

That runs `python -m mcp_server`. Defaults (override them in `.env`):

| Setting | Default |
| --- | --- |
| `MCP_HOST` | `0.0.0.0` |
| `MCP_PORT` | `8080` |
| SSE path | `/sse` |
| Message path | `/messages/` |

A client on another machine uses:

```text
http://<this-mac-ip>:8080/sse
```

If the client is rejected, set `MCP_DISABLE_DNS_REBINDING=true` or set `MCP_ALLOWED_HOSTS` and `MCP_ALLOWED_ORIGINS` in `.env`. The installer writes `MCP_DISABLE_DNS_REBINDING=true`.

Restart the server after code changes. Tools are registered when the process starts, so a running server keeps its previous tool list until it is restarted.

### Tools

`computer` is the main input tool. `action` is one of:

`screenshot`, `left_click`, `right_click`, `middle_click`, `double_click`, `triple_click`, `mouse_move`, `left_click_drag`, `left_mouse_down`, `left_mouse_up`, `scroll`, `type`, `key`, `hold_key`, `wait`, `cursor_position`, `zoom`.

Coordinates are `[x, y]` in screenshot-pixel, top-left space. Optional `text` on clicks and scrolls holds modifiers (`cmd`, `shift`, `alt`/`option`, `ctrl`).

| Tool | What it does |
| --- | --- |
| `computer` | Screen and input actions listed above. |
| `find_and_click` | OCR-locate `text` and optionally click the center of the best match. Optional `region` is `[x0, y0, x1, y1]`. Returns `{found, x, y, confidence, clicked}`. |
| `run_shell` | Run a shell command. Returns `{stdout, stderr, exit_code}`. `timeout` is seconds (default 30, max 300). On timeout the process group is killed and `exit_code` is `-1`. |
| `human_help` | Ask a person for help. See below. |
| `get_screenshot` | Capture the main display as a PNG. Prefer `computer` with `action=screenshot`. |
| `mouse_click`, `mouse_move`, `mouse_scroll`, `keyboard_keypress`, `keyboard_type` | Older clients. Prefer the matching `computer` action. |

### `human_help`

Call `human_help` with one argument, `text`: a paragraph describing what the model needs a person to do.

The Mac shows that paragraph on a full-screen, always-on-top overlay with a **Done** button. A dim layer covers the displays. The message and button sit in a card on the main display. The overlay has no close button. Escape, Command-W, and clicks outside the card do not dismiss it.

- **Done.** The tool returns `{success: true, status: "completed", detail: "Human clicked Done."}`.
- **5 minutes with no click.** The overlay closes and the tool returns `{success: false, status: "timeout", detail: "Done was not clicked within 5 minutes."}`.
- **Chime.** When the overlay appears, and every 30 seconds after that, the server plays `/System/Library/Sounds/Sosumi.aiff` with `afplay`. Playback is non-blocking.

The call stays open until Done or the timeout, so the client waits with it. Empty or non-string `text` is rejected.

## Setup notes

- Grant **Accessibility** or clicks and keystrokes never arrive. Grant **Screen Recording** or screenshots and OCR fail. After changing those permissions, quit and reopen the app that runs the server.
- The server binds to all interfaces by default. Use a trusted network, or set `MCP_HOST=127.0.0.1` if only this Mac should connect.
- `human_help` draws an always-on-top window and plays a system sound every 30 seconds until the person clicks Done or 5 minutes pass.
- Logs for the LaunchAgent, when installed, go to `~/Library/Logs/ScreenCommander/`.
- More detail on the Python package is in [`screen-commander/README.md`](screen-commander/README.md). Architecture notes are in [`screen-commander/docs/architecture.md`](screen-commander/docs/architecture.md).

## Tests

From `screen-commander` with the virtualenv activated:

```bash
python -m pytest tests/test_human_help.py -q
python -m pytest
```

## Layout

```text
ScreenCommander/
  Install Screen Commander.command   # double-click installer
  scripts/install.sh                 # build Swift tool, venv, .env
  MacosUseSDK/                       # input tool (Swift)
  screen-commander/
    mcp_server/                      # MCP tools, including human_help
    scripts/run-mcp.sh               # start the SSE server
    action_executor/                 # MacosUseSDK input wrapper
    screen_analyzer/                 # screen capture
```
