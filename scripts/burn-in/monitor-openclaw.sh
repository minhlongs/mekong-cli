#!/usr/bin/env bash
# monitor-openclaw.sh — Poll harness metrics every 60s, append to CSV.
#
# This script is a lightweight shell-level monitor (separate from sampler.py).
# Run it in a second tmux pane for a live dashboard view.
#
# Usage:
#   bash scripts/burn-in/monitor-openclaw.sh
#   bash scripts/burn-in/monitor-openclaw.sh --once   # single snapshot

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BURN_IN_DIR="$REPO_ROOT/burn-in"
PID_FILE="$BURN_IN_DIR/harness.pid"
LOGS_DIR="$BURN_IN_DIR/logs"
METRICS_DIR="$BURN_IN_DIR/metrics"
RUN_TS="$(date -u +%Y%m%d-%H%M%S)"
CSV_OUT="$METRICS_DIR/monitor-$RUN_TS.csv"

ONCE=false
[[ "${1:-}" == "--once" ]] && ONCE=true

mkdir -p "$METRICS_DIR"

# Write CSV header
echo "ts_utc,elapsed_s,harness_pid,harness_alive,rss_mb,cpu_pct,log_lines,error_lines" \
  > "$CSV_OUT"

START_EPOCH=$(date +%s)

_snapshot() {
  local ts elapsed harness_pid harness_alive rss cpu log_lines err_lines
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  elapsed=$(( $(date +%s) - START_EPOCH ))

  # Harness PID status
  harness_pid="none"
  harness_alive=0
  if [[ -f "$PID_FILE" ]]; then
    harness_pid=$(cat "$PID_FILE")
    kill -0 "$harness_pid" 2>/dev/null && harness_alive=1 || harness_alive=0
  fi

  # RSS + CPU via ps (macOS compatible)
  rss="0"
  cpu="0"
  if [[ "$harness_alive" == "1" ]]; then
    rss=$(ps -o rss= -p "$harness_pid" 2>/dev/null | awk '{printf "%.1f", $1/1024}' || echo "0")
    cpu=$(ps -o %cpu= -p "$harness_pid" 2>/dev/null | tr -d ' ' || echo "0")
  fi

  # Log line counts
  local latest_log
  latest_log=$(ls -t "$LOGS_DIR"/*.jsonl 2>/dev/null | head -1 || true)
  log_lines=0
  err_lines=0
  if [[ -n "$latest_log" && -f "$latest_log" ]]; then
    log_lines=$(wc -l < "$latest_log" | tr -d ' ')
    err_lines=$(grep -c '"ERROR"\|"FATAL"\|CYCLE_ERROR' "$latest_log" 2>/dev/null || echo 0)
  fi

  # Append to CSV
  echo "$ts,$elapsed,$harness_pid,$harness_alive,$rss,$cpu,$log_lines,$err_lines" \
    >> "$CSV_OUT"

  # Print live dashboard line
  local status_icon
  [[ "$harness_alive" == "1" ]] && status_icon="✓" || status_icon="✗"
  printf "[monitor] %s  harness=%s%s  RSS=%sMB  CPU=%s%%  loglines=%s  errors=%s\n" \
    "$ts" "$status_icon" "$harness_pid" "$rss" "$cpu" "$log_lines" "$err_lines"
}

echo "[monitor] CSV: $CSV_OUT"
echo "[monitor] Press Ctrl-C to stop"
echo ""

if $ONCE; then
  _snapshot
  exit 0
fi

while true; do
  _snapshot
  sleep 60
done
