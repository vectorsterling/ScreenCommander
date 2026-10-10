# ScreenCommander

An AI-driven application for controlling computer systems using natural language commands.

## Overview

ScreenCommander interprets natural language instructions to automate interactions with your computer interface. By combining advanced language models with computer vision, it can understand and execute commands like "click the save button" or "scroll down to the next section."

## Features

- Natural language command interpretation
- Real-time screen analysis and UI element detection
- Multi-LLM support for enhanced understanding
- Context-aware command execution
- Cross-platform compatibility (Windows, macOS, Linux)
- Extensible plugin architecture

## Project Structure

The project follows a domain-centric architecture, with each folder dedicated to a specific functionality:

- `command-parser`: Natural language processing and command interpretation
- `screen-analyzer`: Screen capture and UI element detection
- `action-executor`: Command execution and system interaction
- `llm-integrator`: LLM API integration and management
- `context-manager`: State and context management
- `error-handler`: Error detection and recovery
- `config-manager`: Configuration and settings management
- `testing-suite`: Automated tests and quality assurance
- `docs`: Project documentation

## Getting Started

### Prerequisites

- Python 3.9+
- Virtual environment tool (e.g., venv, conda)
- Required system dependencies (see setup guide)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/screen-commander.git
cd screen-commander
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

5. Run the application:
```bash
python main.py
```

### MCP server (macOS, LAN-friendly)

Screen Commander exposes screenshot and input tools over MCP SSE. Input is delegated to **MacosUseSDK** `InputControllerTool` (Swift / CGEvent), not pynput.

1. Build the Swift input tool (requires Xcode / Swift 6+ for MacosUseSDK):

```bash
chmod +x scripts/build-macos-use-sdk.sh
./scripts/build-macos-use-sdk.sh
```

2. Install Python deps and configure:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

3. On a **Mac Mini**, bind the MCP server on all interfaces:

```bash
chmod +x scripts/run-mcp.sh
./scripts/run-mcp.sh
```

Defaults: `MCP_HOST=0.0.0.0`, `MCP_PORT=8080`, SSE at `/sse`, messages at `/messages/`.

4. Point Cursor on another machine at `http://<mac-mini-ip>:8080/sse` (set `MCP_DISABLE_DNS_REBINDING=true` or `MCP_ALLOWED_HOSTS` in `.env` if the client is rejected).

**Tools:** `get_screenshot`, `mouse_click`, `mouse_move`, `mouse_scroll`, `keyboard_keypress`, `keyboard_type`, `human_help`. Mouse coordinates use **top-left** pixels matching `get_screenshot`.

`human_help` takes a paragraph describing what the model needs from a person. It shows that text in a full-screen, always-on-top overlay with a Done button. The call returns when Done is clicked (`success: true`, `status: completed`). If Done is not clicked within 5 minutes it returns a timeout (`success: false`). A chime (`afplay /System/Library/Sounds/Sosumi.aiff`) plays when the overlay appears and every 30 seconds until then. The overlay closes only via Done or that timeout.

Grant **Accessibility** and **Screen Recording** to Terminal (or whatever runs the MCP process) in System Settings.

### One-file-style install (send a zip)

On a machine that already has both repos:

```bash
chmod +x scripts/package-distributable.sh
./scripts/package-distributable.sh
```

This creates `ScreenCommander-MacInstaller.zip` containing:

- `Install Screen Commander.command`
- `screen-commander/`
- `MacosUseSDK/`

On the **fresh Mac Mini**: unzip, double-click **Install Screen Commander.command** (if Gatekeeper warns: **Right-click → Open**). The installer builds Swift tools, creates the venv, writes `.env`, and opens Privacy panes. Optional LaunchAgent runs MCP at login.

macOS may still require manual **Accessibility** and **Screen Recording** approvals; those cannot be bundled into an unsigned installer.

For distribution outside your own machines, notarizing the zip or a `.pkg` avoids Gatekeeper friction (Apple Developer account required).

## Documentation

For detailed documentation, please refer to the `/docs` directory:

- [Setup Guide](docs/setup.md)
- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Contributing Guidelines](docs/contributing.md)

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/contributing.md) for details on how to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 