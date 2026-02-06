#!/bin/bash

# 🛡️ VibeMonitor - MacBook M1 Optimization Daemon
# Continuous monitoring for RAM and CC CLI Priority
# Author: Antigravity

# Settings
RAM_THRESHOLD=200 # MB
LOG_FILE="/tmp/vibemonitor.log"

# function to log messages
log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# 1. Check RAM and Purge
UNUSED_RAM=$(top -l 1 -n 0 | grep "PhysMem" | awk '{print $6}' | sed 's/M//')
if [ "$UNUSED_RAM" -lt "$RAM_THRESHOLD" ]; then
  log "⚠️ RAM low ($UNUSED_RAM MB). Purging..."
  # Use the password provided by user in the background if possible, 
  # but assuming the launchd daemon runs with necessary permissions or sudoers is set.
  # For now, we'll try standard purge.
  purge
  log "✅ Purge complete."
fi

# 2. Prioritize CC CLI Processes (renice)
# Find PIDs for 'claude' and 'node' (dev server)
CC_PIDS=$(pgrep -f "claude")
DEV_SERVER_PIDS=$(pgrep -f "npm run dev")

if [ -n "$CC_PIDS" ]; then
  for PID in $CC_PIDS; do
    renice -n -20 -p "$PID" >/dev/null 2>&1
  done
  log "🚀 Prioritized CC CLI processes."
fi

if [ -n "$DEV_SERVER_PIDS" ]; then
  for PID in $DEV_SERVER_PIDS; do
    renice -n -15 -p "$PID" >/dev/null 2>&1
  done
  log "🚀 Prioritized Dev Server processes."
fi
