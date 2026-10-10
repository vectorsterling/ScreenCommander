#!/usr/bin/env bash
# Install Screen Commander MCP on macOS (fresh or repeat run).
set -euo pipefail

BUNDLE_ROOT="${1:-}"
if [[ -z "$BUNDLE_ROOT" ]]; then
  BUNDLE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

INSTALL_LAUNCH_AGENT=false
for arg in "$@"; do
  if [[ "$arg" == "--launch-agent" ]]; then
    INSTALL_LAUNCH_AGENT=true
  fi
done

# Logs must go to stderr so command substitutions (pick_python, etc.) stay clean.
log() { printf '==> %s\n' "$*" >&2; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

find_screen_commander() {
  if [[ -f "$BUNDLE_ROOT/mcp_server/__main__.py" ]]; then
    echo "$BUNDLE_ROOT"
    return
  fi
  if [[ -f "$BUNDLE_ROOT/screen-commander/mcp_server/__main__.py" ]]; then
    echo "$BUNDLE_ROOT/screen-commander"
    return
  fi
  die "Could not find screen-commander next to this installer (expected mcp_server/ in bundle)."
}

find_macos_use_sdk() {
  local sc_root="$1"
  local candidates=(
    "$sc_root/../MacosUseSDK"
    "$BUNDLE_ROOT/MacosUseSDK"
    "$sc_root/MacosUseSDK"
  )
  for c in "${candidates[@]}"; do
    if [[ -f "$c/Package.swift" ]]; then
      echo "$(cd "$c" && pwd)"
      return
    fi
  done
  die "MacosUseSDK not found. Bundle it alongside screen-commander (see scripts/package-distributable.sh)."
}

require_xcode_swift() {
  if ! xcode-select -p &>/dev/null; then
    die "Xcode Command Line Tools missing. Install Xcode from the App Store, then run: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"
  fi
  local ver
  ver="$(swift --version 2>/dev/null | head -1 || true)"
  log "Swift: ${ver:-unknown}"
  if ! swift --version 2>/dev/null | grep -qE 'Swift version 6\.'; then
    log "WARNING: MacosUseSDK expects Swift 6 (Xcode 16+). Build may fail on older toolchains."
  fi
}

python_meets_minimum() {
  local bin="$1"
  "$bin" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null
}

pick_python() {
  local candidates=()
  local c
  for c in \
    "${PYTHON_BIN:-}" \
    /opt/homebrew/bin/python3.13 \
    /opt/homebrew/bin/python3.12 \
    /opt/homebrew/bin/python3.11 \
    /opt/homebrew/bin/python3 \
    /usr/local/bin/python3.13 \
    /usr/local/bin/python3.12 \
    /usr/local/bin/python3 \
    "$(command -v python3.13 2>/dev/null || true)" \
    "$(command -v python3.12 2>/dev/null || true)" \
    "$(command -v python3.11 2>/dev/null || true)" \
    "$(command -v python3 2>/dev/null || true)"; do
    [[ -n "$c" && -x "$c" ]] || continue
    candidates+=("$c")
  done

  for c in "${candidates[@]}"; do
    if python_meets_minimum "$c"; then
      echo "$c"
      return
    fi
  done

  if command -v brew &>/dev/null; then
    log "Python 3.10+ not found; installing python@3.13 via Homebrew..."
    brew install python@3.13 >&2
    c="$(brew --prefix python@3.13 2>/dev/null)/bin/python3.13"
    if [[ -x "$c" ]] && python_meets_minimum "$c"; then
      echo "$c"
      return
    fi
  fi

  die "Python 3.10+ is required for the MCP server. /usr/bin/python3 on macOS is often 3.9.

Install one of:
  brew install python@3.13
  https://www.python.org/downloads/macos/

Then re-run this installer."
}

SC_ROOT="$(find_screen_commander)"
SDK_ROOT="$(find_macos_use_sdk "$SC_ROOT")"
PYTHON="$(pick_python)"

log "Screen Commander: $SC_ROOT"
log "MacosUseSDK:       $SDK_ROOT"
PY_VER="$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
log "Python:            $PYTHON ($PY_VER)"

require_xcode_swift

INSTALLER_SDK_REV="2026-09-25-py310"
log "Installer SDK revision: $INSTALLER_SDK_REV"

STALE_FILESEARCH="$SDK_ROOT/Sources/MacosUseSDK/FileSearch.swift"
if [[ -f "$STALE_FILESEARCH" ]]; then
  log "Removing stale $STALE_FILESEARCH (FileSearch is not needed for InputControllerTool)"
  rm -f "$STALE_FILESEARCH"
fi

log "Building InputControllerTool (release, input-only)..."
rm -rf "$SDK_ROOT/.build"
(cd "$SDK_ROOT" && swift build -c release --product InputControllerTool)
INPUT_TOOL="$SDK_ROOT/.build/release/InputControllerTool"
[[ -x "$INPUT_TOOL" ]] || die "Build failed: $INPUT_TOOL"

log "Creating Python virtual environment..."
"$PYTHON" -m venv "$SC_ROOT/.venv"
# shellcheck disable=SC1091
source "$SC_ROOT/.venv/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$SC_ROOT/requirements.txt"

ENV_FILE="$SC_ROOT/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$SC_ROOT/.env.example" "$ENV_FILE"
fi

# Idempotent MCP / SDK lines
upsert_env() {
  local key="$1" val="$2"
  local file="$ENV_FILE"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    if [[ "$(uname)" == Darwin ]]; then
      sed -i '' "s|^${key}=.*|${key}=${val}|" "$file"
    else
      sed -i "s|^${key}=.*|${key}=${val}|" "$file"
    fi
  else
    printf '%s=%s\n' "$key" "$val" >>"$file"
  fi
}

upsert_env "MACOS_USE_SDK_ROOT" "$SDK_ROOT"
upsert_env "MACOS_USE_INPUT_TOOL" "$INPUT_TOOL"
upsert_env "MCP_HOST" "0.0.0.0"
upsert_env "MCP_PORT" "8080"
upsert_env "MCP_SSE_PATH" "/sse"
upsert_env "MCP_MESSAGE_PATH" "/messages/"
upsert_env "MCP_DISABLE_DNS_REBINDING" "true"

RUN_SCRIPT="$SC_ROOT/scripts/run-mcp.sh"
chmod +x "$RUN_SCRIPT" "$SC_ROOT/scripts/build-macos-use-sdk.sh" 2>/dev/null || true

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 'YOUR_MAC_IP')"

if $INSTALL_LAUNCH_AGENT; then
  PLIST="$HOME/Library/LaunchAgents/com.screencommander.mcp.plist"
  log "Installing LaunchAgent: $PLIST"
  mkdir -p "$HOME/Library/LaunchAgents"
  cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.screencommander.mcp</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$RUN_SCRIPT</string>
  </array>
  <key>WorkingDirectory</key>
  <string>$SC_ROOT</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/ScreenCommander/mcp.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/ScreenCommander/mcp-error.log</string>
</dict>
</plist>
EOF
  mkdir -p "$HOME/Library/Logs/ScreenCommander"
  launchctl bootout "gui/$(id -u)/com.screencommander.mcp" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  launchctl enable "gui/$(id -u)/com.screencommander.mcp"
  launchctl kickstart -k "gui/$(id -u)/com.screencommander.mcp" 2>/dev/null || true
fi

log "Opening Privacy settings (grant Accessibility + Screen Recording to Terminal or Python)."
open "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_Accessibility" || true
sleep 1
open "x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ScreenCapture" || true

cat <<EOF

Screen Commander install finished.

Start manually:
  cd "$SC_ROOT"
  source .venv/bin/activate
  ./scripts/run-mcp.sh

Cursor MCP URL (other machines on your LAN):
  http://${LAN_IP}:8080/sse

If macOS blocked downloads: the .command was already unquarantined by this installer.
If clicks/keys fail: Accessibility for the app running the server.
If screenshots fail: Screen Recording for the same app.

Re-run this installer anytime to rebuild Swift tools or refresh the venv.

EOF
