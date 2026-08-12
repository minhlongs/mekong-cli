#!/usr/bin/env bash
# bootstrap-init.sh — mekong init entry point
# Dispatches to mekong/bootstrap/index.cjs
# Supports --quiet for silent auto-init on terminal start

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MEKONG_ROOT="${MEKONG_ROOT:-$(dirname "$SCRIPT_DIR")}"

# --quiet: run silently, only output on error
# NOTE: Use 'return' not 'exit' — this script is SOURCED from shell-init.sh
if [[ "${1:-}" == "--quiet" ]]; then
  HEALTH=$(node "$MEKONG_ROOT/mekong/bootstrap/index.cjs" health 2>/dev/null)
  if echo "$HEALTH" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('healthy') else 1)" 2>/dev/null; then
    return 0 2>/dev/null || exit 0
  fi
  node "$MEKONG_ROOT/mekong/bootstrap/index.cjs" init --self --fix >/dev/null 2>&1
  return 0 2>/dev/null || exit 0
fi

exec node "$MEKONG_ROOT/mekong/bootstrap/index.cjs" "$@"
