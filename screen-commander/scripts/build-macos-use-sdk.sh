#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SDK="${MACOS_USE_SDK_ROOT:-$ROOT/../MacosUseSDK}"

if [[ ! -d "$SDK" ]]; then
  echo "MacosUseSDK not found at $SDK" >&2
  exit 1
fi

echo "Building InputControllerTool in $SDK ..."
rm -rf "$SDK/.build"
rm -f "$SDK/Sources/MacosUseSDK/FileSearch.swift"
(cd "$SDK" && swift build -c release --product InputControllerTool)

BIN="$SDK/.build/release/InputControllerTool"
if [[ ! -x "$BIN" ]]; then
  echo "Build failed: $BIN missing" >&2
  exit 1
fi

echo "Built: $BIN"
echo "Export: export MACOS_USE_INPUT_TOOL=$BIN"
