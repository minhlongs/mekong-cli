#!/bin/bash
# Mekong CLI — AGY (Antigravity) CLI Adapter
#
# ALL calls to Antigravity CLI go through this file.
#
# Usage:
#   mekong/adapters/agy-cli.sh --prompt "task" --cwd ./project
#   mekong/adapters/agy-cli.sh --interactive --cwd ./project

set -euo pipefail

# Defaults
AGY_CLI_PATH="${AGY_CLI_PATH:-agy}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"

# Parse args
PROMPT=""
CWD="."
INTERACTIVE=false
DANGEROUSLY_SKIP=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) shift 2;; # AGY CLI does not support model override, ignore silently
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --safe) DANGEROUSLY_SKIP=false; shift;;
    --sandbox) DANGEROUSLY_SKIP=false; export MEKONG_PERMISSION_MODE=ask; shift;;
    --dangerously-skip-permissions|--auto) DANGEROUSLY_SKIP=true; export MEKONG_PERMISSION_MODE=bypass; shift;;
    --parallel) PARALLEL=true; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

# Build command
CMD="$AGY_CLI_PATH"
ARGS=()

if [ "$DANGEROUSLY_SKIP" = true ]; then
  ARGS+=(--dangerously-skip-permissions)
fi

if [ "$INTERACTIVE" = false ] && [ -n "$PROMPT" ]; then
  ARGS+=(-p "$PROMPT")
fi

# Execute
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

if [ -n "$TIMEOUT_CMD" ]; then
  exec "$TIMEOUT_CMD" "$TIMEOUT" "$CMD" "${ARGS[@]}"
else
  exec "$CMD" "${ARGS[@]}"
fi
