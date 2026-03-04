#!/usr/bin/env bash
# 🦞 M1 RAM Guardian — 24/7 giám sát RAM cho 3 panes (P0/P1/P2)
# Chạy trong tmux: tmux new -d -s ram-guardian './scripts/m1-ram-guardian.sh'

set -euo pipefail

# Config
RAM_WARN_MB=2000      # Cảnh báo khi free < 2GB
RAM_CRIT_MB=1000      # Purge khi free < 1GB
CHECK_INTERVAL=30     # Check mỗi 30s
LOG_FILE="$HOME/ram-guardian.log"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

get_free_mb() {
  top -l 1 -s 0 2>/dev/null | grep PhysMem | sed 's/.*,//' | grep -o '[0-9]*M' | head -1 | tr -d 'M'
}

get_used_mb() {
  top -l 1 -s 0 2>/dev/null | grep PhysMem | grep -o '[0-9]*M' | head -1 | tr -d 'M'
}

kill_zombies() {
  # Kill zombie node processes (not CTO, not CC CLI)
  local killed=0
  
  # Kill hung npm test processes (>30 min)
  for pid in $(pgrep -f "npm test" 2>/dev/null || true); do
    local elapsed=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    if [[ "$elapsed" == *:*:* ]]; then  # HH:MM:SS = >1 hour
      kill -9 "$pid" 2>/dev/null && ((killed++)) || true
    fi
  done
  
  # Kill orphan jest/vitest workers
  for pid in $(pgrep -f "jest.*worker" 2>/dev/null || true); do
    kill -9 "$pid" 2>/dev/null && ((killed++)) || true
  done
  
  # Kill orphan turbo processes
  for pid in $(pgrep -f "turbo.*run.*build" 2>/dev/null || true); do
    local elapsed=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ')
    if [[ "$elapsed" == *:*:* ]]; then
      kill -9 "$pid" 2>/dev/null && ((killed++)) || true
    fi
  done
  
  echo "$killed"
}

compact_cc_cli() {
  # Send /compact to CC CLI panes with low context
  for pIdx in 0 1 2; do
    local pane="tom_hum:0.${pIdx}"
    local output=$(tmux capture-pane -t "$pane" -p 2>/dev/null || echo "")
    local tail3=$(echo "$output" | grep -v "^$" | tail -3)
    
    # Check if context < 15% and pane is idle
    if echo "$tail3" | grep -qE "auto-compact: [0-9]%" && echo "$tail3" | grep -q "❯"; then
      log "🧊 P${pIdx} context low — sending /compact"
      tmux send-keys -t "$pane" "/compact" 2>/dev/null
      tmux send-keys -t "$pane" Enter 2>/dev/null
      sleep 2
    fi
  done
}

log "🦞 M1 RAM Guardian ONLINE — threshold: warn=${RAM_WARN_MB}MB crit=${RAM_CRIT_MB}MB"

while true; do
  FREE_MB=$(get_free_mb)
  USED_MB=$(get_used_mb)
  
  if [[ -z "$FREE_MB" ]]; then
    sleep "$CHECK_INTERVAL"
    continue
  fi
  
  if (( FREE_MB < RAM_CRIT_MB )); then
    log "🔴 CRITICAL: ${FREE_MB}MB free — purging RAM!"
    
    # 1. Kill zombie processes
    KILLED=$(kill_zombies)
    [[ "$KILLED" -gt 0 ]] && log "💀 Killed $KILLED zombie processes"
    
    # 2. Compact CC CLI if context low
    compact_cc_cli
    
    # 3. Clear system caches
    # Note: sudo purge needs password, skip if not available
    
    sleep 5
    NEW_FREE=$(get_free_mb)
    log "🔴 After cleanup: ${NEW_FREE}MB free (was ${FREE_MB}MB)"
    
  elif (( FREE_MB < RAM_WARN_MB )); then
    log "🟡 WARN: ${FREE_MB}MB free — monitoring closely"
    KILLED=$(kill_zombies)
    [[ "$KILLED" -gt 0 ]] && log "💀 Killed $KILLED zombie processes"
    
  else
    # Healthy — log every 5 minutes (not every 30s)
    MINUTE=$(date +%M)
    if (( MINUTE % 5 == 0 )); then
      log "🟢 OK: ${FREE_MB}MB free, ${USED_MB}MB used"
    fi
  fi
  
  sleep "$CHECK_INTERVAL"
done
