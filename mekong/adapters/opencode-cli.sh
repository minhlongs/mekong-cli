#!/bin/bash
# Mekong CLI — OpenCode Adapter
set -euo pipefail

OPENCODE_PATH="${OPENCODE_PATH:-opencode}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"
PROMPT="" CWD="." INTERACTIVE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) shift 2;;  # OpenCode reads from config
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

cd "$CWD"

if [ "$INTERACTIVE" = true ]; then
  exec "$OPENCODE_PATH"
elif [ -n "$PROMPT" ]; then
  timeout "$TIMEOUT" "$OPENCODE_PATH" -p "$PROMPT"
fi
