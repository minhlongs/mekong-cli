#!/usr/bin/env bash
# start-openclaw-burn-in.sh — Launch OpenClaw 24h burn-in harness on M1 Max.
#
# Usage:
#   bash scripts/burn-in/start-openclaw-burn-in.sh [--dry-run] [--duration 86400]
#
# This script is designed to run inside a tmux session on M1 Max:
#   tmux new-session -d -s burn-in-260417 \
#     'bash scripts/burn-in/start-openclaw-burn-in.sh 2>&1 | tee burn-in/start.log'

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BURN_IN_DIR="$REPO_ROOT/burn-in"
PID_FILE="$BURN_IN_DIR/harness.pid"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python3"
PYTHON="${VENV_PYTHON:-python3}"

# Fall back to system python if venv absent
if [[ ! -x "$VENV_PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

# ── Parse args ─────────────────────────────────────────────────────────────
DRY_RUN=""
DURATION="86400"
for arg in "$@"; do
  case "$arg" in
    --dry-run)   DRY_RUN="--dry-run" ;;
    --duration=*) DURATION="${arg#*=}" ;;
  esac
done

echo "============================================================"
echo "  OpenClaw Burn-In START"
echo "  Repo:     $REPO_ROOT"
echo "  Duration: ${DURATION}s"
echo "  DryRun:   ${DRY_RUN:-false}"
echo "  Python:   $PYTHON"
echo "  Time:     $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

# ── Guard: prevent double-start ────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID=$(cat "$PID_FILE")
  if kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "[start] ERROR: Harness already running (PID=$EXISTING_PID). Stop it first:"
    echo "  bash scripts/burn-in/stop-and-report.sh"
    exit 1
  else
    echo "[start] Stale PID file found — removing"
    rm -f "$PID_FILE"
  fi
fi

# ── Env guards: prevent prod calls during burn-in ──────────────────────────
export MEKONG_ENV=burn-in
export DAEMON_LLM_MODEL="${DAEMON_LLM_MODEL:-qwen2.5-coder:7b}"
# Strip real tokens so daemon uses offline mode
unset GITHUB_TOKEN 2>/dev/null || true

echo "[start] MEKONG_ENV=$MEKONG_ENV"
echo "[start] DAEMON_LLM_MODEL=$DAEMON_LLM_MODEL"

# ── Keep M1 Max awake for full run ─────────────────────────────────────────
if command -v caffeinate &>/dev/null; then
  caffeinate -dimsu -t "$DURATION" &
  echo "[start] caffeinate started (PID=$!)"
fi

# ── Launch harness ─────────────────────────────────────────────────────────
cd "$REPO_ROOT"
echo "[start] Launching harness..."
exec "$PYTHON" burn-in/harness.py --duration "$DURATION" $DRY_RUN
