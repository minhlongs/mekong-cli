#!/usr/bin/env bash
# stop-and-report.sh — Gracefully stop harness + generate summary report.
#
# Usage:
#   bash scripts/burn-in/stop-and-report.sh [--run-ts 20260417-120000]
#
# If --run-ts omitted, summarize picks the latest run automatically.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BURN_IN_DIR="$REPO_ROOT/burn-in"
PID_FILE="$BURN_IN_DIR/harness.pid"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python3"
PYTHON="${VENV_PYTHON:-python3}"
[[ ! -x "$VENV_PYTHON" ]] && PYTHON="$(command -v python3)"

RUN_TS_ARG=""
for arg in "$@"; do
  case "$arg" in
    --run-ts=*) RUN_TS_ARG="--run-ts=${arg#*=}" ;;
  esac
done

echo "============================================================"
echo "  OpenClaw Burn-In STOP + REPORT"
echo "  Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "============================================================"

# ── 1. Stop harness ────────────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
  HARNESS_PID=$(cat "$PID_FILE")
  if kill -0 "$HARNESS_PID" 2>/dev/null; then
    echo "[stop] Sending SIGTERM to harness PID=$HARNESS_PID ..."
    kill -TERM "$HARNESS_PID"

    # Wait up to 30s for clean exit
    WAITED=0
    while kill -0 "$HARNESS_PID" 2>/dev/null && [[ $WAITED -lt 30 ]]; do
      sleep 1
      WAITED=$((WAITED + 1))
    done

    if kill -0 "$HARNESS_PID" 2>/dev/null; then
      echo "[stop] WARN: still alive after 30s — sending SIGKILL"
      kill -9 "$HARNESS_PID" 2>/dev/null || true
    else
      echo "[stop] Harness exited cleanly in ${WAITED}s"
    fi
  else
    echo "[stop] PID $HARNESS_PID not running (already stopped)"
  fi
  rm -f "$PID_FILE"
else
  echo "[stop] No harness.pid found — may already be stopped"
fi

# ── 2. Kill caffeinate if we started one ──────────────────────────────────
pkill -f "caffeinate.*-dimsu" 2>/dev/null || true

# ── 3. Generate summary report ────────────────────────────────────────────
echo ""
echo "[stop] Generating summary report..."
cd "$REPO_ROOT"
"$PYTHON" burn-in/summarize.py $RUN_TS_ARG

echo ""
echo "[stop] Done. Check burn-in/reports/ for the summary."
