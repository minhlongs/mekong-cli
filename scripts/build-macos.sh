#!/usr/bin/env bash
set -euo pipefail

BIN_NAME="mekong"
SPEC="mekong.spec"
DIST_DIR="dist"

echo ">> Cleaning"
rm -rf "$DIST_DIR" build

echo ">> PyInstaller"
poetry run pyinstaller "$SPEC" --clean --noconfirm

BIN_PATH="${DIST_DIR}/${BIN_NAME}"
if [[ ! -x "$BIN_PATH" ]]; then
  echo "ERROR: binary not found: $BIN_PATH" >&2
  exit 1
fi

echo ">> OK: $BIN_PATH ($(du -h "$BIN_PATH" | cut -f1))"
