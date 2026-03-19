#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WATCHDOG TỰ HỒI SINH — Auto-resurrect Doanh Trại every 5 min
# Crontab: */5 * * * * /opt/homebrew/bin/bash ~/mekong-cli/scripts/watchdog.sh
# ═══════════════════════════════════════════════════════════════
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export HOME="${HOME:-/Users/macbookprom1}"

PROJECT_ROOT="$HOME/mekong-cli"
MEKONG_DIR="$PROJECT_ROOT/.mekong"
LOG_FILE="$MEKONG_DIR/watchdog.log"
OLLAMA_BIN="/Applications/Ollama.app/Contents/Resources/ollama"
OLLAMA_MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:8b}"

mkdir -p "$MEKONG_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG_FILE"; }

# Rotate log (keep last 500 lines)
[[ -f "$LOG_FILE" ]] && tail -500 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"

log "=== WATCHDOG CHECK ==="

FIXES=0

# ── 1. CHECK SESSIONS ──
REQUIRED_SESSIONS="tom_hum tom_hum_sales tom_hum_docs tom_hum_ops"
MISSING=""
for s in $REQUIRED_SESSIONS; do
  tmux has-session -t "$s" 2>/dev/null || MISSING+="$s "
done
if [[ -n "$MISSING" ]]; then
  log "RESURRECT: Missing sessions: $MISSING"
  cd "$PROJECT_ROOT" && bash scripts/start-all-departments.sh all >> "$LOG_FILE" 2>&1
  FIXES=$((FIXES + 1))
else
  log "Sessions: OK ($(tmux list-sessions 2>/dev/null | grep -c tom_hum))"
fi

# ── 2. CHECK DAEMONS ──
if ! pgrep -f "cto-daemon.sh" >/dev/null 2>&1; then
  log "RESURRECT: CTO daemon dead → restarting"
  cd "$PROJECT_ROOT"
  OPENCLAW_WORKER_MODEL="$OLLAMA_MODEL" nohup bash cto-daemon.sh >> "$MEKONG_DIR/cto-daemon.log" 2>&1 &
  log "CTO daemon PID: $!"
  FIXES=$((FIXES + 1))
else
  # Kill duplicates (keep latest)
  pids=$(pgrep -f "cto-daemon.sh" | sort -n)
  count=$(echo "$pids" | wc -l | tr -d ' ')
  if [[ $count -gt 1 ]]; then
    echo "$pids" | head -$((count-1)) | xargs kill -9 2>/dev/null
    log "Killed $((count-1)) duplicate CTO daemons"
  fi
fi

if ! pgrep -f "doanh-trai-daemon.sh" >/dev/null 2>&1; then
  log "RESURRECT: DT daemon dead → restarting"
  cd "$PROJECT_ROOT"
  nohup /opt/homebrew/bin/bash scripts/doanh-trai-daemon.sh >> "$MEKONG_DIR/doanh-trai.log" 2>&1 &
  log "DT daemon PID: $!"
  FIXES=$((FIXES + 1))
fi

# ── 3. CHECK OLLAMA ──
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
  # Check if model loaded
  loaded=$(curl -s http://localhost:11434/api/ps 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('models',[])))" 2>/dev/null || echo 0)
  if [[ "$loaded" == "0" ]]; then
    log "WARMUP: No models loaded → warming $OLLAMA_MODEL"
    curl -s --max-time 90 http://localhost:11434/api/generate \
      -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"hello\",\"stream\":false,\"keep_alive\":\"24h\",\"options\":{\"num_predict\":1}}" >/dev/null 2>&1 &
    FIXES=$((FIXES + 1))
  fi
else
  # Start Ollama server
  if [[ -f "$OLLAMA_BIN" ]]; then
    log "RESURRECT: Ollama not running → starting"
    "$OLLAMA_BIN" serve &>/dev/null &
    sleep 3
    FIXES=$((FIXES + 1))
  fi
fi

# ── 4. CHECK CONTEXT (90%+ → /clear) ──
for session in $(tmux list-sessions -F '#{session_name}' 2>/dev/null | grep tom_hum); do
  for pane_idx in $(tmux list-panes -t "$session" -F '#{pane_index}' 2>/dev/null); do
    output=$(tmux capture-pane -t "${session}:0.${pane_idx}" -p -S -15 2>/dev/null || echo "")
    [[ -z "$output" ]] && continue

    # Context 90%+ or 100% → /clear
    if echo "$output" | grep -qE "Context:.*100%|Context:.*9[0-9]%|Auto-compacting"; then
      log "CLEAR: ${session}:${pane_idx} context full"
      tmux send-keys -t "${session}:0.${pane_idx}" "/clear" Enter 2>/dev/null
      FIXES=$((FIXES + 1))
    fi

    # ── 5. CHECK STUCK on dialog ──
    if echo "$output" | tail -5 | grep -qiE "Enter to select|arrow keys|choose.*option"; then
      log "UNSTICK: ${session}:${pane_idx} dialog stuck"
      tmux send-keys -t "${session}:0.${pane_idx}" Escape 2>/dev/null
      sleep 0.5
      tmux send-keys -t "${session}:0.${pane_idx}" "q" Enter 2>/dev/null
      FIXES=$((FIXES + 1))
    fi
  done
done

# ── 6. CHECK RAM ──
free_pct=$(vm_stat 2>/dev/null | awk '/Pages free/{free=$3} /speculative/{spec=$3} END{total=free+spec; print int(total*16384/1073741824*100/16)}')
if [[ "${free_pct:-5}" -lt 3 ]]; then
  log "RAM CRITICAL: ${free_pct}% free → killing zombie nodes"
  # Kill orphan node processes
  bash "$PROJECT_ROOT/scripts/reset-full-panes.sh" 2>/dev/null || true
  # Cleanup orphan nodes
  node_count=$(pgrep -f 'node' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$node_count" -gt 30 ]]; then
    log "RAM: $node_count node processes → killall"
    killall -9 node 2>/dev/null || true
    FIXES=$((FIXES + 1))
  fi
fi

log "Watchdog done: $FIXES fixes applied"
