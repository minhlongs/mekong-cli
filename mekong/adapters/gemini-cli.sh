#!/bin/bash
# Mekong CLI — Gemini CLI Adapter
# Usage: mekong/adapters/gemini-cli.sh --prompt "task" --cwd ./project
set -euo pipefail

GEMINI_PATH="${GEMINI_PATH:-gemini}"
MODEL="${MEKONG_MODEL:-gemini-2.5-pro}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"
PROMPT="" CWD="." INTERACTIVE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --sandbox) export MEKONG_PERMISSION_MODE=ask; shift;;
    --dangerously-skip-permissions) export MEKONG_PERMISSION_MODE=bypass; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

cd "$CWD"

# Resolve timeout command (macOS support)
TIMEOUT_CMD="timeout"
if ! command -v timeout >/dev/null 2>&1; then
  if command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_CMD="gtimeout"
  else
    TIMEOUT_CMD=""
  fi
fi

if [ "$INTERACTIVE" = true ]; then
  exec "$GEMINI_PATH"
elif [ -n "$PROMPT" ]; then
  if [ -n "$TIMEOUT_CMD" ]; then
    exec "$TIMEOUT_CMD" "$TIMEOUT" "$GEMINI_PATH" -p "$PROMPT"
  else
    exec "$GEMINI_PATH" -p "$PROMPT"
  fi
fi
