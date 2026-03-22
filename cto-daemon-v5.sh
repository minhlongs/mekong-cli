#!/usr/bin/env bash
# CTO DAEMON v5.0 — Real CTO with Qwen 32B Brain
# The brain READS context and DECIDES. Bash just executes.
set -o pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$HOME/mekong-cli}"
SESSION="${1:-openclaw}"
INTERVAL="${2:-60}"
OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3:32b"
LOG="$HOME/.mekong/cto-v5.log"
STOP_FILE="$HOME/.openclaw/STOP"
LOCK_FILE="$HOME/.mekong/cto-v5.pid"

WORKERS=(
  "mekong-cli|.|pnpm run build"
  "algo-trader|apps/algo-trader|npx tsc --noEmit"
  "well|apps/well|npm run build"
)
PANE_COUNT=${#WORKERS[@]}

log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

# Singleton
if [[ -f "$LOCK_FILE" ]] && kill -0 "$(cat "$LOCK_FILE")" 2>/dev/null; then
  echo "CTO v5 already running. Exiting."; exit 1
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"; exit' INT TERM EXIT
mkdir -p "$(dirname "$LOG")"

# ---- QWEN BRAIN: Ask CTO what to do ----
ask_brain() {
  local project="$1" dir="$2" deploy="$3" pane_output="$4" pane_ctx="$5"
  echo "$pane_output" | python3 "${PROJECT_ROOT}/scripts/cto-brain.py" "$project" "$dir" "$deploy" "$pane_ctx" 2>/dev/null
}

# ---- TMUX HELPERS ----
capture() { tmux capture-pane -t "${SESSION}:0.$1" -p -S -30 2>/dev/null; }

is_idle() {
  local output="$1"
  local tail5=$(echo "$output" | tail -5)
  echo "$tail5" | grep -q "❯" || return 1
  echo "$tail5" | grep -qiE "Running|thinking|tokens" && return 1
  echo "$output" | tail -10 | grep -qiE "Press up to edit|queued" && return 1
  return 0
}

get_ctx() { echo "$1" | grep -oE '[0-9]+%' | tail -1 | tr -d '%'; }

send_cmd() {
  local pane=$1 cmd=$2
  local output=$(capture "$pane")
  is_idle "$output" || { log "BLOCKED P${pane}: busy"; return 1; }
  tmux send-keys -t "${SESSION}:0.${pane}" -l "$cmd"
  sleep 0.3
  tmux send-keys -t "${SESSION}:0.${pane}" Enter
  log "SENT P${pane}: $cmd"
}

# ---- BOOTSTRAP ----
bootstrap() {
  tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION" 2>/dev/null
  sleep 1
  tmux new-session -d -s "$SESSION" -x 200 -y 60
  for ((i=1; i<PANE_COUNT; i++)); do
    tmux split-window -t "${SESSION}:0" 2>/dev/null
  done
  tmux select-layout -t "${SESSION}" tiled
  sleep 1
  for ((i=0; i<PANE_COUNT; i++)); do
    tmux send-keys -t "${SESSION}:0.${i}" "source ~/.zshrc 2>/dev/null && cd ${PROJECT_ROOT} && mekong --interactive" Enter
    log "BOOTSTRAP: P${i} → mekong --interactive"
  done
  sleep 12
  for ((i=0; i<PANE_COUNT; i++)); do
    local content=$(capture "$i")
    if echo "$content" | grep -q "trust this folder"; then
      tmux send-keys -t "${SESSION}:0.${i}" Enter
      log "BOOTSTRAP: P${i} → confirmed trust"
    fi
  done
  sleep 5
  log "BOOTSTRAP: done"
}

# ---- MAIN LOOP ----
log "================================================"
log "CTO DAEMON v5.0 — Real CTO with Qwen Brain"
log "Session: $SESSION | Poll: ${INTERVAL}s | Workers: $PANE_COUNT"
log "================================================"

bootstrap

CYCLE=0
LAST_DISPATCH=()
LAST_CMD=()
for ((i=0; i<PANE_COUNT; i++)); do LAST_DISPATCH[$i]=0; LAST_CMD[$i]=""; done

while true; do
  CYCLE=$((CYCLE + 1))
  log "--- CYCLE $CYCLE ---"

  # L6: Kill switch
  [[ -f "$STOP_FILE" ]] && { log "L6-KILLSWITCH ACTIVE"; log "SLEEPING ${INTERVAL}s..."; sleep "$INTERVAL"; log "WOKE UP"; continue; }

  DISPATCHED=0
  for ((i=0; i<PANE_COUNT; i++)); do
    IFS='|' read -r name dir deploy <<< "${WORKERS[$i]}"
    output=$(capture "$i")
    ctx=$(get_ctx "$output")

    # Not idle = working
    if ! is_idle "$output"; then
      log "P${i} (${name}): WORKING [ctx:${ctx:-?}%]"
      # Auto-handle dialogs
      if echo "$output" | tail -5 | grep -qE "Enter to select|Esc to cancel"; then
        tmux send-keys -t "${SESSION}:0.${i}" Enter
      fi
      continue
    fi

    # 1 dispatch per cycle
    [[ $DISPATCHED -ge 1 ]] && { log "P${i} (${name}): IDLE (1-per-cycle)"; continue; }

    # Cooldown 90s
    now=$(date +%s)
    elapsed=$((now - ${LAST_DISPATCH[$i]}))
    [[ $elapsed -lt 90 ]] && { log "P${i} (${name}): IDLE (cooldown ${elapsed}/90s)"; continue; }

    # Context >= 85% → compact
    if [[ -n "$ctx" && "$ctx" -ge 85 ]]; then
      send_cmd "$i" "/compact"
      LAST_DISPATCH[$i]=$now
      DISPATCHED=1
      log "P${i} (${name}): ctx ${ctx}% → /compact"
      continue
    fi

    # ASK QWEN BRAIN — the real CTO decision
    log "P${i} (${name}): IDLE → asking brain..."
    brain_cmd=$(ask_brain "$name" "$dir" "$deploy" "$output" "${ctx:-0}")

    if [[ -n "$brain_cmd" ]]; then
      # Dedup: skip if exact same command
      cmd_key=$(echo "$brain_cmd" | awk '{print $1}')
      if [[ "${LAST_CMD[$i]}" == "$cmd_key" ]]; then
        # Rotate: pick different command instead of skipping
        case "$cmd_key" in
          /cook)          brain_cmd="/worker-build "Project: ${name}. Build + test. ${deploy}" --fast";;
          /worker-build)  brain_cmd="/eng-tech-debt "Project: ${name}. Scan tech debt." --fast";;
          /eng-tech-debt) brain_cmd="/dev-review "Project: ${name}. Review code quality." --fast";;
          /dev-review)    brain_cmd="/worker-test "Project: ${name}. Run all tests." --fast";;
          *)              brain_cmd="/worker-health "Project: ${name}. Health check." --fast";;
        esac
        cmd_key=$(echo "$brain_cmd" | awk '{print $1}')
        log "P${i} (${name}): DEDUP rotate ${LAST_CMD[$i]} → ${cmd_key}"
      fi

      log "BRAIN → P${i} (${name}): $brain_cmd"
      if send_cmd "$i" "$brain_cmd"; then
        LAST_DISPATCH[$i]=$now
        LAST_CMD[$i]=$cmd_key
        DISPATCHED=1
        log "DELEGATED P${i} (${name}) → ${brain_cmd}"
      fi
    else
      log "P${i} (${name}): BRAIN empty — skip"
      LAST_DISPATCH[$i]=$now
    fi
  done

  log "SLEEPING ${INTERVAL}s..."; sleep "$INTERVAL"; log "WOKE UP"
done
