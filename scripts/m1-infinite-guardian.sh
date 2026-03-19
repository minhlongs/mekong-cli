#!/bin/bash
# M1 Infinite Guardian — Cấm off, giữ mát, watchdog CC CLI agents
# Usage: nohup ./m1-infinite-guardian.sh &
# Kill:  kill $(cat /tmp/m1-guardian.pid)

set -uo pipefail

PID_FILE="/tmp/m1-guardian.pid"
LOG="/tmp/m1-guardian.log"
COOLER_SCRIPT="/Users/macbookprom1/mekong-cli/scripts/m1-cooler.sh"
TMUX_SESSION="tom_hum"

echo $$ > "$PID_FILE"

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }

cleanup() {
  log "🛑 Guardian stopping..."
  # Don't kill caffeinate — let user decide
  rm -f "$PID_FILE"
  exit 0
}
trap cleanup SIGINT SIGTERM

# ═══ 1. Prevent Sleep — FOREVER ═══
ensure_no_sleep() {
  if ! pgrep -q caffeinate; then
    caffeinate -dims &
    log "☕ caffeinate started — M1 will NEVER sleep"
  fi
  # Also disable display sleep via pmset
  sudo pmset -a displaysleep 0 sleep 0 disksleep 0 2>/dev/null || true
}

# ═══ 2. Ensure M1 Cooler Running ═══
ensure_cooler() {
  local cooler_pid
  cooler_pid=$(cat /tmp/m1-cooler.pid 2>/dev/null || echo "")
  if [[ -z "$cooler_pid" ]] || ! kill -0 "$cooler_pid" 2>/dev/null; then
    log "❄️ Restarting M1 Cooler daemon..."
    nohup "$COOLER_SCRIPT" --aggressive >> /tmp/m1-cooler.log 2>&1 &
    log "❄️ Cooler restarted (PID $!)"
  fi
}

# ═══ 3. Watchdog CC CLI agents in tmux ═══
check_cc_cli_pane() {
  local pane=$1
  local last_line
  last_line=$(tmux capture-pane -p -t "${TMUX_SESSION}:${pane}" 2>/dev/null | grep -v '^$' | tail -1)
  
  # Check if pane is stuck/idle (waiting for input with no activity)
  if [[ "$last_line" == *"❯"* && "$last_line" != *"⏵⏵"* ]]; then
    # Agent finished or stuck — re-send bootstrap
    log "🔄 Pane $pane idle — re-sending /bootstrap:auto:parallel"
    tmux send-keys -t "${TMUX_SESSION}:${pane}" "/bootstrap:auto:parallel" Enter
  elif [[ "$last_line" == *"Context low"* || "$last_line" == *"0% remaining"* ]]; then
    # Context exhausted — compact and restart
    log "🧹 Pane $pane context exhausted — compacting and restarting"
    tmux send-keys -t "${TMUX_SESSION}:${pane}" "/compact" Enter
    sleep 10
    tmux send-keys -t "${TMUX_SESSION}:${pane}" "/bootstrap:auto:parallel" Enter
  fi
}

# ═══ 4. System health snapshot ═══
health_check() {
  local load=$(sysctl -n vm.loadavg | awk '{print $2}')
  local mem_pages_free=$(vm_stat | awk '/Pages free/ {gsub(/\./,"",$3); print $3}')
  local swap=$(sysctl -n vm.swapusage | awk '{print $6}' | sed 's/M//' 2>/dev/null || echo "0")
  log "📊 Load: $load | Free pages: $mem_pages_free | Swap: ${swap}M"
}

# ═══ Main Loop — INFINITE ═══
log "╔══════════════════════════════════════════╗"
log "║  🛡️  M1 INFINITE GUARDIAN v1.0           ║"
log "║  PID: $$ | Session: $TMUX_SESSION        ║"
log "║  Mode: NEVER SLEEP + COOL + WATCHDOG     ║"
log "╚══════════════════════════════════════════╝"

ensure_no_sleep

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  
  # Every cycle (30s): basic checks
  ensure_no_sleep
  ensure_cooler
  
  # Every cycle: check CC CLI agents
  for pane in 0.0 0.1 0.2; do
    check_cc_cli_pane "$pane"
  done
  
  # Every 4 cycles (2min): health snapshot
  if (( CYCLE % 4 == 0 )); then
    health_check
  fi
  
  # Every 20 cycles (10min): purge memory
  if (( CYCLE % 20 == 0 )); then
    purge 2>/dev/null && log "💧 Memory purged (cycle $CYCLE)"
  fi
  
  sleep 30
done
