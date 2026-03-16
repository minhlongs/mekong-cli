#!/bin/bash
# FACTORY WATCHDOG — Auto-restart factory-loop.sh if it crashes
# Checks PID file every 60s. Does NOT kill active CC CLI tasks.
# Usage: nohup bash factory-watchdog.sh &
set -euo pipefail

PID_FILE="/tmp/factory.pid"
FACTORY_SCRIPT="$HOME/mekong-cli/factory-loop.sh"
CHECK_INTERVAL=60

echo "🐕 WATCHDOG started — PID: $$ — $(date)"
echo "🐕 Monitoring: $PID_FILE (every ${CHECK_INTERVAL}s)"

while true; do
  if [ -f "$PID_FILE" ]; then
    FACTORY_PID=$(cat "$PID_FILE" 2>/dev/null || echo "0")
    if kill -0 "$FACTORY_PID" 2>/dev/null; then
      # Factory is running
      sleep $CHECK_INTERVAL
      continue
    else
      echo "🐕 [$(date +%T)] Factory PID $FACTORY_PID is DEAD — restarting..."
      echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | watchdog_restart | - | - | crashed | 0s | -" >> /tmp/factory-metrics.log
    fi
  else
    echo "🐕 [$(date +%T)] No PID file — starting factory..."
  fi

  # Start factory loop in background
  nohup bash "$FACTORY_SCRIPT" >> "$HOME/tom_hum_cto.log" 2>&1 &
  NEW_PID=$!
  echo "🐕 [$(date +%T)] Factory restarted — new PID: $NEW_PID"

  # Wait before next check to avoid rapid restart loops
  sleep $CHECK_INTERVAL
done
