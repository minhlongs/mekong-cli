#!/bin/bash
# 🧬 SUPREME HEALER (v1.0) — Resilience Layer for Tôm Hùm CTO
# Purpose: Auto-restart task-watcher and annihilate blocking thermal debris.

WATCHER_CMD="node task-watcher.js"
WATCHER_DIR="/Users/macbookprom1/mekong-cli/apps/openclaw-worker"
LOG_FILE="/Users/macbookprom1/tom_hum_cto.log"

echo "[$(date)] SUPREME HEALER ACTIVATED"

while true; do
  # 1. Surgical Kill of Blocking Debris
  pkill -9 -f "sudo purge" 2>/dev/null
  pkill -9 -f "pyright" 2>/dev/null
  pkill -9 -f "eslint" 2>/dev/null

  # 2. Check Load & Log
  LOAD=$(uptime | awk -F'load averages:' '{ print $2 }' | awk '{ print $1 }')
  echo "[$(date)] Load: $LOAD"

  # 3. Process Watchdog
  if ! pgrep -f "$WATCHER_CMD" > /dev/null; then
    echo "[$(date)] ⚠️ CTO DROPPED! Re-igniting..."
    cd "$WATCHER_DIR"
    nohup $WATCHER_CMD >> "$LOG_FILE" 2>&1 &
    echo "[$(date)] ✅ CTO REBORN (PID: $!)"
  fi

  sleep 15
done
