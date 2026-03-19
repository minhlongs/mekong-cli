#!/bin/bash
# Mekong CLI — Aider Adapter
set -euo pipefail

AIDER_PATH="${AIDER_PATH:-aider}"
MODEL="${MEKONG_MODEL:-}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"
PROMPT="" CWD="." INTERACTIVE=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

cd "$CWD"
ARGS=(--yes-always)
[ -n "$MODEL" ] && ARGS+=(--model "$MODEL")

if [ "$INTERACTIVE" = true ]; then
  exec "$AIDER_PATH" "${ARGS[@]}"
elif [ -n "$PROMPT" ]; then
  timeout "$TIMEOUT" "$AIDER_PATH" "${ARGS[@]}" --message "$PROMPT"
fi
