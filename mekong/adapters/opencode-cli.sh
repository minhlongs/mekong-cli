#!/bin/bash
# Mekong CLI — OpenCode Adapter
set -euo pipefail

OPENCODE_PATH="${OPENCODE_PATH:-opencode}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"

# Defaults
PROMPT=""
CWD="."
INTERACTIVE=false
DANGEROUSLY_SKIP=true
MODEL=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --dangerously-skip-permissions) DANGEROUSLY_SKIP=true; shift;;
    --sandbox) DANGEROUSLY_SKIP=false; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

cd "$CWD"

ARGS=()

if [ "$INTERACTIVE" = true ]; then
  if [ -n "$MODEL" ]; then
    ARGS+=(-m "$MODEL")
  fi
  exec "$OPENCODE_PATH" "${ARGS[@]}"
else
  # Run non-interactive agent
  ARGS+=(run)
  if [ "$DANGEROUSLY_SKIP" = true ]; then
    ARGS+=(--dangerously-skip-permissions)
  fi
  if [ -n "$MODEL" ]; then
    ARGS+=(-m "$MODEL")
  fi
  if [ -n "$PROMPT" ]; then
    ARGS+=("$PROMPT")
  fi
  
  # Redirect stdin from /dev/null to prevent blocking in non-interactive mode
  exec timeout "$TIMEOUT" "$OPENCODE_PATH" "${ARGS[@]}" < /dev/null
fi
