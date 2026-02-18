#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🦞🧊 LOBSTER COOLER v1.0 — Antigravity Thermal Manager
# ═══════════════════════════════════════════════════════════════
# Tôm Hùm giữ Antigravity IDE mát lạnh trên M1 MacBook
#
# Strategy:
#   Load < 5  → NORMAL: restore full priority
#   Load 5-10 → WARM: renice IDE to +5 (lower priority)
#   Load > 10 → HOT: renice IDE to +15, suspend GPU helper
#   Load > 20 → NUCLEAR: suspend all non-essential IDE helpers
#
# Safe: NEVER kills Antigravity, only adjusts priority/suspend
# ═══════════════════════════════════════════════════════════════

set +e  # Don't exit on errors

LOG="/tmp/lobster-cooler.log"
PIDFILE="/tmp/lobster-cooler.pid"
CHECK_INTERVAL=30  # seconds
RENICE_COOL=0      # normal priority
RENICE_WARM=5      # slightly lower
RENICE_HOT=15      # much lower
LOAD_WARM=5
LOAD_HOT=10
LOAD_NUCLEAR=20

# Track state to avoid repeated actions
CURRENT_STATE="unknown"
PURGE_COUNTER=0

log() {
  echo "[$(date '+%H:%M:%S')] 🦞🧊 $1" >> "$LOG"
}

get_load() {
  sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}' | tr -d '{}' 
}

get_antigravity_pids() {
  # Main Electron process
  pgrep -f "Antigravity.app/Contents/MacOS/Electron" 2>/dev/null
}

get_antigravity_renderer_pids() {
  pgrep -f "Antigravity Helper (Renderer)" 2>/dev/null
}

get_antigravity_gpu_pids() {
  pgrep -f "Antigravity Helper (GPU)" 2>/dev/null
}

get_antigravity_plugin_pids() {
  pgrep -f "Antigravity Helper (Plugin)" 2>/dev/null
}

get_antigravity_helper_pids() {
  pgrep -f "Antigravity Helper.app" 2>/dev/null | head -3
}

get_language_server_pids() {
  pgrep -f "language_server_macos_arm" 2>/dev/null
}

get_tsserver_pids() {
  pgrep -f "tsserver.js" 2>/dev/null
}

renice_pids() {
  local nice_val=$1
  shift
  for pid in "$@"; do
    renice -n "$nice_val" -p "$pid" 2>/dev/null
  done
}

suspend_pids() {
  for pid in "$@"; do
    kill -STOP "$pid" 2>/dev/null
  done
}

resume_pids() {
  for pid in "$@"; do
    kill -CONT "$pid" 2>/dev/null
  done
}

apply_normal() {
  if [ "$CURRENT_STATE" = "normal" ]; then return; fi
  log "❄️ COOL — Load normal. Restoring full priority."
  
  local all_pids=$(get_antigravity_pids; get_antigravity_renderer_pids; get_antigravity_gpu_pids; get_antigravity_plugin_pids)
  renice_pids $RENICE_COOL $all_pids
  
  # Resume any suspended processes
  local gpu_pids=$(get_antigravity_gpu_pids)
  local helper_pids=$(get_antigravity_helper_pids)
  resume_pids $gpu_pids $helper_pids
  
  CURRENT_STATE="normal"
}

apply_warm() {
  if [ "$CURRENT_STATE" = "warm" ]; then return; fi
  log "🌡️ WARM — Reducing IDE priority to +${RENICE_WARM}"
  
  local main_pids=$(get_antigravity_pids)
  local renderer_pids=$(get_antigravity_renderer_pids)
  local gpu_pids=$(get_antigravity_gpu_pids)
  
  renice_pids $RENICE_WARM $main_pids $renderer_pids $gpu_pids
  
  # Resume any previously suspended
  resume_pids $gpu_pids
  
  CURRENT_STATE="warm"
}

apply_hot() {
  if [ "$CURRENT_STATE" = "hot" ]; then return; fi
  log "🔥 HOT — Aggressive throttle: renice +${RENICE_HOT}, suspend GPU"
  
  local main_pids=$(get_antigravity_pids)
  local renderer_pids=$(get_antigravity_renderer_pids)
  local gpu_pids=$(get_antigravity_gpu_pids)
  local lang_pids=$(get_language_server_pids)
  local ts_pids=$(get_tsserver_pids)
  
  # Renice everything hard
  renice_pids $RENICE_HOT $main_pids $renderer_pids $gpu_pids $lang_pids $ts_pids
  
  # Suspend GPU helper (least needed)
  suspend_pids $gpu_pids
  
  # Purge RAM
  purge 2>/dev/null &
  
  CURRENT_STATE="hot"
}

apply_nuclear() {
  if [ "$CURRENT_STATE" = "nuclear" ]; then return; fi
  log "☢️ NUCLEAR — Emergency cooling! Suspend non-essential IDE helpers"
  
  local main_pids=$(get_antigravity_pids)
  local renderer_pids=$(get_antigravity_renderer_pids)
  local gpu_pids=$(get_antigravity_gpu_pids)
  local lang_pids=$(get_language_server_pids)
  local ts_pids=$(get_tsserver_pids)
  local helper_pids=$(get_antigravity_helper_pids)
  
  # Max renice
  renice_pids $RENICE_HOT $main_pids $renderer_pids $gpu_pids $lang_pids $ts_pids
  
  # Suspend GPU + language server (heaviest non-essential)
  suspend_pids $gpu_pids $lang_pids
  
  # Purge RAM
  purge 2>/dev/null &
  
  # Clean temp files
  rm -rf /tmp/vite-* /tmp/turbo-* /tmp/next-* 2>/dev/null
  
  CURRENT_STATE="nuclear"
}

# ═══════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════

# Write PID
echo $$ > "$PIDFILE"

# Rotate log if too big (> 2MB)
if [ -f "$LOG" ] && [ "$(stat -f%z "$LOG" 2>/dev/null || echo 0)" -gt 2097152 ]; then
  mv "$LOG" "${LOG}.old"
fi

log "═══════════════════════════════════════════════════"
log "🦞🧊 LOBSTER COOLER v1.0 ONLINE — PID $$"
log "  Intervals: ${CHECK_INTERVAL}s"
log "  Thresholds: warm>${LOAD_WARM} hot>${LOAD_HOT} nuclear>${LOAD_NUCLEAR}"
log "═══════════════════════════════════════════════════"

while true; do
  LOAD=$(get_load)
  LOAD_INT=${LOAD%.*}  # truncate to integer
  
  # Periodic purge every 10 cycles (~5 min)
  PURGE_COUNTER=$((PURGE_COUNTER + 1))
  if [ "$PURGE_COUNTER" -ge 10 ]; then
    purge 2>/dev/null &
    PURGE_COUNTER=0
  fi
  
  if [ "$LOAD_INT" -ge "$LOAD_NUCLEAR" ]; then
    apply_nuclear
  elif [ "$LOAD_INT" -ge "$LOAD_HOT" ]; then
    apply_hot
  elif [ "$LOAD_INT" -ge "$LOAD_WARM" ]; then
    apply_warm
  else
    apply_normal
  fi
  
  # Log every 5th cycle (2.5 min) to reduce noise
  if [ $((PURGE_COUNTER % 5)) -eq 0 ] || [ "$CURRENT_STATE" != "normal" ]; then
    log "📊 Load: ${LOAD} | State: ${CURRENT_STATE}"
  fi
  
  sleep $CHECK_INTERVAL
done
