#!/bin/bash
# Double-click installer for Screen Commander MCP (macOS).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# Gmail/browser downloads add quarantine; strip for the whole bundle.
xattr -cr "$DIR" 2>/dev/null || true

resolve_install_sh() {
  if [[ -f "$DIR/scripts/install.sh" ]]; then
    echo "$DIR/scripts/install.sh"
  elif [[ -f "$DIR/screen-commander/scripts/install.sh" ]]; then
    echo "$DIR/screen-commander/scripts/install.sh"
  else
    echo "ERROR: install.sh not found. Expected:" >&2
    echo "  $DIR/scripts/install.sh" >&2
    echo "  $DIR/screen-commander/scripts/install.sh" >&2
    exit 1
  fi
}

INSTALL_SH="$(resolve_install_sh)"
chmod +x "$INSTALL_SH" 2>/dev/null || true

clear
echo "Screen Commander MCP Installer"
echo "================================"
echo ""
read -r -p "Install LaunchAgent to run MCP at login? [y/N] " LA
ARGS=("$DIR")
if [[ "$LA" =~ ^[Yy]$ ]]; then
  ARGS+=("--launch-agent")
fi

exec "$INSTALL_SH" "${ARGS[@]}"
