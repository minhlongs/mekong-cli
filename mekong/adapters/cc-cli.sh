#!/bin/bash
# Mekong CLI — CC CLI Adapter (SINGLE SOURCE OF TRUTH)
#
# ALL calls to Claude Code CLI go through this file.
# When Anthropic updates CC CLI flags → fix HERE, not 22 places.
#
# Usage:
#   mekong/adapters/cc-cli.sh --prompt "task" --model sonnet --cwd ./project
#   mekong/adapters/cc-cli.sh --interactive --cwd ./project

set -euo pipefail

# Defaults
CC_CLI_PATH="${CC_CLI_PATH:-claude}"
MODEL="${MEKONG_MODEL:-claude-sonnet-4-6-20250514}"
TIMEOUT="${MEKONG_TIMEOUT:-3600}"

# Parse args
PROMPT=""
CWD="."
INTERACTIVE=false
DANGEROUSLY_SKIP=true

while [[ $# -gt 0 ]]; do
  case $1 in
    --prompt|-p) PROMPT="$2"; shift 2;;
    --model|-m) MODEL="$2"; shift 2;;
    --cwd) CWD="$2"; shift 2;;
    --interactive) INTERACTIVE=true; shift;;
    --safe) DANGEROUSLY_SKIP=false; shift;;
    --timeout) TIMEOUT="$2"; shift 2;;
    *) PROMPT="$1"; shift;;
  esac
done

# Build command
CMD="$CC_CLI_PATH"
ARGS=()

if [ "$DANGEROUSLY_SKIP" = true ]; then
  ARGS+=(--dangerously-skip-permissions)
fi

ARGS+=(--model "$MODEL")

if [ -n "$PROMPT" ]; then
  ARGS+=(-p "$PROMPT")
fi

# Execute
cd "$CWD"
timeout "$TIMEOUT" "$CMD" "${ARGS[@]}"
