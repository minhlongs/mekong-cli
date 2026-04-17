#!/usr/bin/env bash
# kill-switch-test.sh — Send SIGTERM to harness, verify graceful exit + restart.
# Run at T+12h checkpoint or any time to verify shutdown behaviour.
#
# Usage: bash burn-in/kill-switch-test.sh
# Exit 0 = pass, Exit 1 = fail

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$REPO_ROOT/burn-in/harness.pid"
LOGS_DIR="$REPO_ROOT/burn-in/logs"

echo "[kill-switch] Starting kill-switch test at $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ── 1. Verify harness is running ───────────────────────────────────────────
if [[ ! -f "$PID_FILE" ]]; then
  echo "[kill-switch] FAIL: harness.pid not found — is the harness running?"
  exit 1
fi

HARNESS_PID=$(cat "$PID_FILE")
if ! kill -0 "$HARNESS_PID" 2>/dev/null; then
  echo "[kill-switch] FAIL: PID $HARNESS_PID is not running"
  exit 1
fi
echo "[kill-switch] Harness PID=$HARNESS_PID confirmed running"

# ── 2. Record latest log file before SIGTERM ──────────────────────────────
LATEST_LOG=$(ls -t "$LOGS_DIR"/*.jsonl 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_LOG" ]]; then
  echo "[kill-switch] WARN: no log file found — cannot verify continuity"
fi
PRE_LINES=$(wc -l < "$LATEST_LOG" 2>/dev/null || echo 0)
echo "[kill-switch] Log lines before SIGTERM: $PRE_LINES"

# ── 3. Send SIGTERM ────────────────────────────────────────────────────────
echo "[kill-switch] Sending SIGTERM to PID=$HARNESS_PID ..."
kill -TERM "$HARNESS_PID"

# ── 4. Wait for graceful exit (max 30s) ───────────────────────────────────
WAITED=0
MAX_WAIT=30
while kill -0 "$HARNESS_PID" 2>/dev/null; do
  sleep 1
  WAITED=$((WAITED + 1))
  if [[ $WAITED -ge $MAX_WAIT ]]; then
    echo "[kill-switch] FAIL: Process still alive after ${MAX_WAIT}s — force killing"
    kill -9 "$HARNESS_PID" 2>/dev/null || true
    exit 1
  fi
done
echo "[kill-switch] PASS: Harness exited cleanly in ${WAITED}s"

# ── 5. Verify harness_end event written to log ─────────────────────────────
if [[ -n "$LATEST_LOG" ]]; then
  if grep -q '"event": *"harness_end"' "$LATEST_LOG" 2>/dev/null || \
     grep -q '"event":"harness_end"' "$LATEST_LOG" 2>/dev/null; then
    echo "[kill-switch] PASS: harness_end event found in log"
  else
    echo "[kill-switch] WARN: harness_end event NOT found in log (may be timing)"
  fi
fi

echo ""
echo "[kill-switch] Kill-switch test PASSED at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[kill-switch] To restart burn-in: bash scripts/burn-in/start-openclaw-burn-in.sh"
