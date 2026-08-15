#!/usr/bin/env bash
set -euo pipefail

TASK="${*:-}"

if [[ "$TASK" =~ (refactor|architecture|design|rewrite|security|migrate) ]]; then
  export ANTHROPIC_MODEL="claude-3-5-sonnet-latest"
  unset ANTHROPIC_BASE_URL || true
else
  export ANTHROPIC_MODEL="Qwen3.6-35B-A3B"
  export ANTHROPIC_BASE_URL="http://localhost:8080/v1"
fi

exec claude "$TASK"
