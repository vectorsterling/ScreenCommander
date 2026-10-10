#!/usr/bin/env bash
# Build a zip you can send: Install .command + screen-commander + MacosUseSDK
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${MACOS_USE_SDK_ROOT:-$ROOT/../MacosUseSDK}"
OUT="${1:-$ROOT/../ScreenCommander-MacInstaller.zip}"
STAGING="$(mktemp -d)"
BUNDLE="$STAGING/ScreenCommander"

cleanup() { rm -rf "$STAGING"; }
trap cleanup EXIT

[[ -d "$SDK" ]] || { echo "MacosUseSDK not found at $SDK" >&2; exit 1; }

mkdir -p "$BUNDLE"
rsync -a \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'action_executor/venv' \
  --exclude '.git' \
  "$ROOT/" "$BUNDLE/screen-commander/"

rsync -a \
  --exclude '.build' \
  --exclude '.git' \
  "$SDK/" "$BUNDLE/MacosUseSDK/"

cp "$ROOT/Install Screen Commander.command" "$BUNDLE/"
# Top-level scripts/ so .command works if layout differs; zip layout uses screen-commander/scripts/
mkdir -p "$BUNDLE/scripts"
cp "$ROOT/scripts/install.sh" "$BUNDLE/scripts/"
cp "$ROOT/INSTALLER_VERSION" "$BUNDLE/INSTALLER_VERSION"
chmod +x "$BUNDLE/Install Screen Commander.command"
chmod +x "$BUNDLE/scripts/install.sh"
chmod +x "$BUNDLE/screen-commander/scripts/"*.sh

rm -f "$OUT"
(
  cd "$STAGING"
  zip -r "$OUT" ScreenCommander
)

echo "Created: $OUT"
echo "Send this zip; recipient unzips and double-clicks 'Install Screen Commander.command'."
