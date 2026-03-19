#!/bin/bash
# M1 Cooler Daemon — Infinite thermal management for heavy parallel workloads
# Usage: ./m1-cooler.sh [--aggressive] [--daemon]
# Kill: kill $(cat /tmp/m1-cooler.pid)

set +e  # Daemon mode: tolerate non-critical errors

MODE="${1:---normal}"
LOG="/tmp/m1-cooler.log"
PID_FILE="/tmp/m1-cooler.pid"

# Thresholds (CPU % per process)
if [[ "$MODE" == "--aggressive" ]]; then
  CPU_WARN=60    # Start throttling
  CPU_CRIT=80    # Hard throttle
  MEM_CRIT=80    # Memory pressure %
  PAUSE_SEC=30   # Pause duration when critical
else
  CPU_WARN=75
  CPU_CRIT=90
  MEM_CRIT=85
  PAUSE_SEC=15
fi

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo $$ > "$PID_FILE"

cleanup() {
  echo -e "\n${RED}🛑 M1 Cooler stopped${NC}"
  rm -f "$PID_FILE"
  exit 0
}
trap cleanup SIGINT SIGTERM

log() {
  local msg="[$(date '+%H:%M:%S')] $1"
  echo -e "$msg"
  echo "$msg" >> "$LOG"
}

get_cpu_load() {
  sysctl -n vm.loadavg | awk '{print $2}'
}

get_mem_pressure() {
  local total=$(sysctl -n hw.memsize)
  local free_pages=$(vm_stat | awk '/Pages free/ {gsub(/\./,"",$3); print $3}')
  local inactive=$(vm_stat | awk '/Pages inactive/ {gsub(/\./,"",$3); print $3}')
  local page_size=16384
  local free=$(( (free_pages + inactive) * page_size ))
  local used=$(( total - free ))
  echo $(( used * 100 / total ))
}

get_swap_mb() {
  sysctl -n vm.swapusage | awk '{print $6}' | sed 's/M//'
}

throttle_heavy_processes() {
  # Find node/claude processes using > CPU_WARN% CPU, lower their priority
  ps -eo pid,%cpu,comm -r | awk -v limit="$CPU_WARN" 'NR>1 && $2+0 > limit {print $1, $2, $3}' | while read pid cpu cmd; do
    # Don't touch system processes or WindowServer
    if [[ "$cmd" != *"WindowServer"* && "$cmd" != *"kernel"* ]]; then
      renice 10 "$pid" 2>/dev/null && log "${YELLOW}⚡ Throttled PID $pid ($cmd) at ${cpu}% CPU → nice 10${NC}"
    fi
  done
}

kill_zombie_processes() {
  # Kill orphan stress test / dd processes
  pkill -f 'stress_test_' 2>/dev/null && log "${RED}🗑 Killed orphan stress_test processes${NC}" || true
  pkill -f 'parallel_hammer' 2>/dev/null && log "${RED}🗑 Killed orphan parallel_hammer${NC}" || true
}

purge_memory() {
  # macOS memory pressure relief — purge inactive memory
  # Requires no sudo on recent macOS
  purge 2>/dev/null && log "${CYAN}💧 Memory purged${NC}" || true
}

clear_temp_files() {
  # Clean up large temp files that stress SSD
  find /tmp -name "*.dat" -size +50M -delete 2>/dev/null
  find /tmp -name "test_file*" -delete 2>/dev/null
}

pause_if_critical() {
  local load=$(get_cpu_load)
  local load_int=$(echo "$load" | awk '{printf "%d", $1}')
  
  if (( load_int > 7 )); then  # M1 has 8 cores, >7 = maxed out
    log "${RED}🔥 CRITICAL LOAD: $load — Pausing heavy processes for ${PAUSE_SEC}s${NC}"
    
    # SIGSTOP heaviest non-essential processes temporarily
    ps -eo pid,%cpu,comm -r | awk 'NR>1 && NR<=4 {print $1, $3}' | while read pid cmd; do
      if [[ "$cmd" == *"node"* || "$cmd" == *"bc"* || "$cmd" == *"dd"* ]]; then
        kill -STOP "$pid" 2>/dev/null && log "${YELLOW}⏸ Paused PID $pid ($cmd)${NC}"
        (sleep "$PAUSE_SEC" && kill -CONT "$pid" 2>/dev/null && log "${GREEN}▶ Resumed PID $pid${NC}") &
      fi
    done
    
    sleep "$PAUSE_SEC"
  fi
}

# ─── Main Loop ───
echo -e "${CYAN}"
echo "╔══════════════════════════════════════╗"
echo "║   ❄️  M1 Cooler Daemon v1.0  ❄️      ║"
echo "║   Mode: $MODE                        "
echo "║   PID: $$                            "
echo "║   Log: $LOG                          "
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

log "Starting M1 Cooler (mode=$MODE, cpu_warn=$CPU_WARN%, cpu_crit=$CPU_CRIT%)"

kill_zombie_processes
clear_temp_files

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  
  LOAD=$(get_cpu_load)
  MEM=$(get_mem_pressure)
  SWAP=$(get_swap_mb 2>/dev/null || echo "0")
  
  # Status line
  LOAD_INT=$(echo "$LOAD" | awk '{printf "%d", $1}')
  if (( LOAD_INT > 6 )); then
    ICON="🔥"
  elif (( LOAD_INT > 4 )); then
    ICON="🌡️"
  else
    ICON="❄️"
  fi
  
  log "$ICON Cycle #$CYCLE | Load: $LOAD | RAM: ${MEM}% | Swap: ${SWAP}M"
  
  # Actions based on thresholds
  throttle_heavy_processes
  
  # Critical load detection
  pause_if_critical
  
  # Memory management every 5 cycles
  if (( CYCLE % 5 == 0 )); then
    if (( MEM > MEM_CRIT )); then
      log "${RED}⚠️ Memory pressure HIGH (${MEM}%) — purging${NC}"
      purge_memory
    fi
    clear_temp_files
  fi
  
  # Kill zombies every 10 cycles
  if (( CYCLE % 10 == 0 )); then
    kill_zombie_processes
  fi
  
  sleep 10
done
