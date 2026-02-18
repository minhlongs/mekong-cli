#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# 🦞 AGI SUPERVISOR v2.0 — Fully Autonomous 24/7 Monitoring
# ═══════════════════════════════════════════════════════════════════════
# Binh Pháp Ch.13 用間: Intelligence Network — Watch Everything
# v2.0: Active CC CLI kick + CTO auto-recovery + smart idle detection
#
# Chạy:  nohup ./scripts/agi-supervisor.sh &
# Dừng:  kill $(cat /tmp/agi-supervisor.pid)
# Logs:  tail -f /tmp/agi-supervisor.log
# ═══════════════════════════════════════════════════════════════════════

set +e  # Don't exit on errors — health checks may fail expectedly

# --- CONFIGURATION ---
MEKONG_DIR="/Users/macbookprom1/mekong-cli"
APP_DIR="$MEKONG_DIR/apps/openclaw-worker"
SCRIPTS_DIR="$MEKONG_DIR/scripts"
LOG_FILE="/tmp/agi-supervisor.log"
PID_FILE="/tmp/agi-supervisor.pid"
SESSION="tom_hum_brain"

# Intervals (seconds)
LAYER1_INTERVAL=30    # Foundation: every 30s
LAYER2_INTERVAL=120   # Intelligence: every 2min
LAYER3_INTERVAL=600   # Analytics: every 10min
LAYER4_INTERVAL=1800  # Reporting: every 30min

# Telegram
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-5503922921}"

# Counters
CYCLE=0
LAST_L2=0
LAST_L3=0
LAST_L4=0
ADAPTER_RESTARTS=0
WATCHER_RESTARTS=0
BRAIN_RESPAWNS=0
IDLE_COUNT=0
MAX_IDLE_BEFORE_KICK=1  # Kick after 1 idle detection (2min)

# --- INIT ---
echo $$ > "$PID_FILE"

# Rotate log if > 5MB
if [ -f "$LOG_FILE" ] && [ "$(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0)" -gt 5242880 ]; then
  mv "$LOG_FILE" "${LOG_FILE}.old"
fi

# --- HELPERS ---
log() {
  local ts
  ts=$(date '+%H:%M:%S')
  echo "[$ts] 🦞 $1" >> "$LOG_FILE"
}

telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${TELEGRAM_CHAT_ID}\",\"text\":\"🦞 AGI Supervisor\\n\\n$1\"}" > /dev/null 2>&1 || true
}

check_port() {
  curl -sf -m 3 "http://localhost:$1/health" > /dev/null 2>&1
}

check_process() {
  pgrep -f "$1" > /dev/null 2>&1
}

# ═══════════════════════════════════════════════════════════════════════
# LAYER 1: FOUNDATION — Keep the stack alive (every 30s)
# ═══════════════════════════════════════════════════════════════════════
layer1_foundation() {
  local issues=0

  # --- 1A: Anthropic Adapter (Port 11436) ---
  if ! check_port 11436; then
    log "❌ L1: Adapter 11436 DOWN — restarting..."
    pkill -f "anthropic-adapter.js" 2>/dev/null || true
    sleep 1
    nohup node "$SCRIPTS_DIR/anthropic-adapter.js" 11436 >> /tmp/adapter_11436.log 2>&1 &
    sleep 3
    if check_port 11436; then
      ADAPTER_RESTARTS=$((ADAPTER_RESTARTS + 1))
      log "✅ L1: Adapter 11436 recovered (restarts: $ADAPTER_RESTARTS)"
      telegram "🔄 Adapter 11436 auto-recovered (restart #$ADAPTER_RESTARTS)"
    else
      log "🚨 L1: Adapter 11436 FAILED to restart!"
      telegram "🚨 CRITICAL: Adapter 11436 won't start!"
    fi
    issues=1
  fi

  # --- 1B: Task Watcher (CTO) ---
  if ! check_process "task-watcher.js"; then
    log "❌ L1: task-watcher.js DEAD — restarting..."
    cd "$APP_DIR"
    nohup node task-watcher.js >> "$HOME/tom_hum_cto.log" 2>&1 &
    sleep 3
    if check_process "task-watcher.js"; then
      WATCHER_RESTARTS=$((WATCHER_RESTARTS + 1))
      log "✅ L1: task-watcher recovered (restarts: $WATCHER_RESTARTS)"
    else
      log "🚨 L1: task-watcher FAILED to restart!"
      telegram "🚨 CRITICAL: task-watcher won't start!"
    fi
    issues=1
  fi

  # --- 1C: Tmux Brain Session ---
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    log "❌ L1: tmux session '$SESSION' DEAD — task-watcher will respawn"
    if check_process "task-watcher.js"; then
      local watcher_pid
      watcher_pid=$(pgrep -f "task-watcher.js" | head -1)
      kill -SIGUSR1 "$watcher_pid" 2>/dev/null || true
      BRAIN_RESPAWNS=$((BRAIN_RESPAWNS + 1))
      log "✅ L1: Sent SIGUSR1 to task-watcher (PID $watcher_pid) for brain respawn"
    fi
    issues=1
  fi

  # --- 1D: Upstream Proxies (9191/9192) — informational ---
  local upstream_ok=0
  check_port 9191 && upstream_ok=$((upstream_ok + 1))
  check_port 9192 && upstream_ok=$((upstream_ok + 1))
  if [ "$upstream_ok" -lt 1 ]; then
    log "⚠️ L1: Both upstream proxies (9191/9192) DOWN"
  fi

  return $issues
}

# ═══════════════════════════════════════════════════════════════════════
# LAYER 2: INTELLIGENCE — Keep CC CLI working 24/7 (every 2min)
# ═══════════════════════════════════════════════════════════════════════
layer2_intelligence() {
  if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    return 0
  fi

  # Capture ONLY last 8 lines — prevents stale history false-positives
  local buffer
  buffer=$(tmux capture-pane -t "${SESSION}:0.0" -p -S -8 2>/dev/null || echo "")

  if [ -z "$buffer" ]; then
    return 0
  fi

  # --- 2A: Detect CC CLI STATE ---
  local is_busy=0
  local is_idle=0
  local is_stuck=0

  # BUSY patterns — CC CLI actively working (EXPANDED list)
  if echo "$buffer" | grep -qEi '(Thinking|Orbiting|Saut[eé]ing|Frolicking|Cooking|Crunching|Marinating|Fermenting|Calculating|Compacting|Simmering|Steaming|Vibing|Toasting|Photosynthesizing|Braising|Reducing|Blanching|Sketching|Initializing|Running|Waiting|Perambulating|Tinkering|Flowing|Roosting|Herding|Forging|Generating|Cooked)'; then
    is_busy=1
  fi

  # IDLE patterns — CC CLI waiting for input (prompt visible, no busy indicator)
  if echo "$buffer" | grep -qE '❯'; then
    if [ "$is_busy" -eq 0 ]; then
      is_idle=1
    fi
  fi

  # STUCK patterns — CC CLI needs intervention
  if echo "$buffer" | grep -qEi '(Interrupted|What should Claude do|Context left until auto-compact: [0-5]%)'; then
    is_stuck=1
  fi

  # --- 2B: Action based on state ---
  if [ "$is_busy" -eq 1 ]; then
    IDLE_COUNT=0
    # Don't log every cycle when busy to reduce noise
    return 0
  fi

  if [ "$is_stuck" -eq 1 ]; then
    log "🚨 L2: CC CLI STUCK/INTERRUPTED — force kick!"
    tmux send-keys -t "${SESSION}:0.0" Escape
    sleep 0.5
    tmux send-keys -t "${SESSION}:0.0" Enter
    sleep 1
    tmux send-keys -t "${SESSION}:0.0" Enter
    IDLE_COUNT=0
    return 0
  fi

  if [ "$is_idle" -eq 1 ]; then
    IDLE_COUNT=$((IDLE_COUNT + 1))
    log "⚠️ L2: CC CLI IDLE (count: $IDLE_COUNT/$MAX_IDLE_BEFORE_KICK)"

    if [ "$IDLE_COUNT" -ge "$MAX_IDLE_BEFORE_KICK" ]; then
      log "🔄 L2: CC CLI idle too long — sending Enter to trigger CTO dispatch"
      tmux send-keys -t "${SESSION}:0.0" Enter
      IDLE_COUNT=0
    fi
    return 0
  fi

  # Unknown state — log
  local last_line
  last_line=$(echo "$buffer" | grep -v '^$' | tail -1)
  log "❓ L2: CC CLI state: ${last_line:0:80}"

  # --- 2C: Verify CTO is alive ---
  if ! check_process "task-watcher.js"; then
    log "❌ L2: CTO DEAD — emergency restart!"
    cd "$APP_DIR"
    nohup node task-watcher.js >> "$HOME/tom_hum_cto.log" 2>&1 &
    sleep 3
    if check_process "task-watcher.js"; then
      WATCHER_RESTARTS=$((WATCHER_RESTARTS + 1))
      log "✅ L2: CTO emergency restart OK (#$WATCHER_RESTARTS)"
      telegram "🔄 CTO auto-recovered by L2 (#$WATCHER_RESTARTS)"
    fi
  fi

  # --- 2D: Clear stale mission locks ---
  local lock_file="$MEKONG_DIR/tasks/.mission_lock"
  if [ -f "$lock_file" ]; then
    local lock_age
    lock_age=$(( $(date +%s) - $(stat -f%m "$lock_file" 2>/dev/null || echo "$(date +%s)") ))
    if [ "$lock_age" -gt 1800 ]; then
      rm -f "$lock_file"
      log "🔓 L2: Cleared stale mission lock (age: ${lock_age}s)"
    fi
  fi

  # --- 2E: ConnectionRefused detection ---
  if echo "$buffer" | grep -q "ConnectionRefused"; then
    log "⚠️ L2: ConnectionRefused detected — checking adapter..."
    if ! check_port 11436; then
      log "🔄 L2: Adapter dead — triggering L1 recovery"
      layer1_foundation
    fi
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# LAYER 3: ANALYTICS — Track system health (every 10min)
# ═══════════════════════════════════════════════════════════════════════
layer3_analytics() {
  # --- 3A: Parse proxy health ---
  local health
  health=$(curl -s -m 5 "http://localhost:11436/health" 2>/dev/null)

  if [ -n "$health" ]; then
    local stats
    stats=$(echo "$health" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  reqs=d.get('requests',0)
  q=d.get('queue',0)
  t429=d.get('total429',0)
  bg=sum(1 for k in d.get('google',[]) if k.get('blocked'))
  tg=len(d.get('google',[]))
  ag=d.get('antigravity',{})
  print(f'R:{reqs} 429:{t429} Q:{q} G-blocked:{bg}/{tg} AG:{ag.get(\"total\",0)}')
except: print('PARSE_ERR')
" 2>/dev/null)
    log "📊 L3: Proxy | $stats"

    # Alert if queue is backed up
    local queue_depth
    queue_depth=$(echo "$health" | python3 -c "import sys,json; print(json.load(sys.stdin).get('queue',0))" 2>/dev/null || echo 0)
    if [ "$queue_depth" -gt 5 ]; then
      log "⚠️ L3: Request queue depth: $queue_depth"
    fi
  fi

  # --- 3B: Task queue status ---
  local pending_tasks
  pending_tasks=$(find "$MEKONG_DIR/tasks" -maxdepth 1 -name "*.txt" -not -name ".*" 2>/dev/null | wc -l | tr -d ' ')
  local processed_today
  processed_today=$(find "$MEKONG_DIR/tasks/processed" -maxdepth 1 -name "*.txt" -newer /tmp/agi-supervisor-day-marker 2>/dev/null | wc -l | tr -d ' ')

  log "📊 L3: Tasks | Pending: $pending_tasks | Processed today: $processed_today"

  # --- 3C: System load ---
  local load
  load=$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}')
  local ram_used
  ram_used=$(vm_stat 2>/dev/null | awk '/Pages active/ {printf "%.0f", $3*4096/1048576}')
  log "📊 L3: System | Load: $load | RAM active: ${ram_used:-?}MB"

  # Touch day marker for processed count
  touch /tmp/agi-supervisor-day-marker 2>/dev/null || true
}

# ═══════════════════════════════════════════════════════════════════════
# LAYER 4: REPORTING — Full dashboard (every 30min)
# ═══════════════════════════════════════════════════════════════════════
layer4_reporting() {
  log "═══════════════════════════════════════════════════"
  log "📋 FULL STATUS REPORT — Cycle $CYCLE"
  log "═══════════════════════════════════════════════════"

  # Stack health
  local adapter_status="❌ DOWN"
  check_port 11436 && adapter_status="✅ ONLINE"
  local watcher_status="❌ DOWN"
  check_process "task-watcher.js" && watcher_status="✅ ONLINE"
  local brain_status="❌ DOWN"
  tmux has-session -t "$SESSION" 2>/dev/null && brain_status="✅ ONLINE"
  local p9191="❌"
  check_port 9191 && p9191="✅"
  local p9192="❌"
  check_port 9192 && p9192="✅"

  log "  Adapter 11436: $adapter_status"
  log "  Task Watcher:  $watcher_status"
  log "  Brain Tmux:    $brain_status"
  log "  Upstream 9191: $p9191 | 9192: $p9192"
  log "  Restarts: Adapter=$ADAPTER_RESTARTS Watcher=$WATCHER_RESTARTS Brain=$BRAIN_RESPAWNS"

  # Pending tasks
  local pending
  pending=$(ls "$MEKONG_DIR/tasks/"*.txt 2>/dev/null | wc -l | tr -d ' ')
  log "  Pending Tasks: $pending"

  # CC CLI state
  local cli_state
  cli_state=$(tmux capture-pane -t "${SESSION}:0.0" -p -S -5 2>/dev/null | grep -oE '(Sautéing|Cooking|Flowing|Roosting|Herding|Forging|Simmering|Cooked|idle|❯|Error|bypass|Tinkering|Perambulating)' | tail -1)
  log "  CC CLI State:  ${cli_state:-unknown}"

  # AGI evolution score (from data file)
  local agi_score="?"
  if [ -f "$APP_DIR/data/evolution-state.json" ]; then
    agi_score=$(python3 -c "import json; print(json.load(open('$APP_DIR/data/evolution-state.json')).get('evolutionScore',0))" 2>/dev/null || echo "?")
  fi
  log "  AGI Score:     $agi_score/100"
  log "═══════════════════════════════════════════════════"

  # Telegram summary (only if there were restarts)
  local total_restarts=$((ADAPTER_RESTARTS + WATCHER_RESTARTS + BRAIN_RESPAWNS))
  if [ "$total_restarts" -gt 0 ]; then
    telegram "📋 Report C$CYCLE\\n$adapter_status Adapter\\n$watcher_status Watcher\\n$brain_status Brain\\nRestarts: $total_restarts\\nAGI: $agi_score/100"
  fi
}

# ═══════════════════════════════════════════════════════════════════════
# 🚀 MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════

log "═══════════════════════════════════════════════════"
log "🚀 AGI SUPERVISOR v2.0 ONLINE — FULLY AUTONOMOUS"
log "  PID: $$"
log "  Layer 1 (Foundation):    every ${LAYER1_INTERVAL}s"
log "  Layer 2 (Intelligence):  every ${LAYER2_INTERVAL}s — ACTIVE KICK"
log "  Layer 3 (Analytics):     every ${LAYER3_INTERVAL}s"
log "  Layer 4 (Reporting):     every ${LAYER4_INTERVAL}s"
log "═══════════════════════════════════════════════════"

# Initial day marker
touch /tmp/agi-supervisor-day-marker 2>/dev/null || true

# Initial full check
layer1_foundation
layer3_analytics
layer4_reporting

while true; do
  CYCLE=$((CYCLE + 1))
  NOW=$(date +%s)

  # Layer 1: Foundation (every cycle = 30s)
  layer1_foundation

  # Layer 2: Intelligence (every 2min)
  if [ $((NOW - LAST_L2)) -ge $LAYER2_INTERVAL ]; then
    layer2_intelligence
    LAST_L2=$NOW
  fi

  # Layer 3: Analytics (every 10min)
  if [ $((NOW - LAST_L3)) -ge $LAYER3_INTERVAL ]; then
    layer3_analytics
    LAST_L3=$NOW
  fi

  # Layer 4: Reporting (every 30min)
  if [ $((NOW - LAST_L4)) -ge $LAYER4_INTERVAL ]; then
    layer4_reporting
    LAST_L4=$NOW
  fi

  sleep "$LAYER1_INTERVAL"
done
