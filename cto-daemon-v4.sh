#!/usr/bin/env bash
# CTO DAEMON v4.0 — 7-Layer Manus Architecture
# Clean rewrite. No legacy. KISS.
set -uo pipefail

# ---- CONFIG ----
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/mekong-cli}"
MEKONG_DIR="$HOME/.mekong"
SESSION="${1:-openclaw}"
INTERVAL="${2:-30}"
OLLAMA_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3:32b"
LOG="$MEKONG_DIR/cto-v4.log"
STOP_FILE="$HOME/.openclaw/STOP"
LOCK_FILE="$MEKONG_DIR/cto-v4.pid"

# Workers: name|dir|deploy_cmd
WORKERS=(
  "mekong-cli|.|pnpm run build"
  "algo-trader|apps/algo-trader|npx tsc --noEmit"
  "well|apps/well|npm run build"
)
PANE_COUNT=${#WORKERS[@]}

# ---- LOGGING ----
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

# ---- SINGLETON ----
if [[ -f "$LOCK_FILE" ]] && kill -0 "$(cat "$LOCK_FILE")" 2>/dev/null; then
  echo "CTO v4 already running (PID $(cat "$LOCK_FILE")). Exiting."
  exit 1
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"; exit' INT TERM EXIT

mkdir -p "$MEKONG_DIR" "$(dirname "$LOG")"

# ---- L6: KILL SWITCH ----
check_killswitch() {
  if [[ -f "$STOP_FILE" ]]; then
    log "L6-KILLSWITCH: $STOP_FILE detected — ALL HALTED"
    return 0  # killswitch active
  fi
  return 1  # safe to proceed
}

# ---- TMUX: CAPTURE + SEND ----
capture() { tmux capture-pane -t "${SESSION}:0.$1" -p -S -30 2>/dev/null; }

is_idle() {
  local output="$1"
  local tail5
  tail5=$(echo "$output" | tail -5)
  # CC CLI idle: has ❯ prompt and no active work
  if echo "$tail5" | grep -q "❯"; then
    # Check NOT working
    if echo "$tail5" | grep -qiE "Running|thinking|tokens|Sautéed|Cooked|Baked"; then
      return 1  # still working/just finished
    fi
    # Check NOT queued (anti-x2)
    if echo "$output" | tail -10 | grep -qiE "Press up to edit|queued"; then
      return 1  # has queued messages
    fi
    return 0  # truly idle
  fi
  return 1  # no prompt = not idle
}

get_context_pct() {
  local output="$1"
  echo "$output" | grep -oE '[0-9]+%' | tail -1 | tr -d '%'
}

send_cmd() {
  local pane=$1 cmd=$2
  local output
  output=$(capture "$pane")

  # Anti-x2: block if not idle
  if ! is_idle "$output"; then
    log "BLOCKED P${pane}: not idle — ${cmd:0:60}"
    return 1
  fi


  # Send command
  tmux send-keys -t "${SESSION}:0.${pane}" -l "$cmd"
  sleep 0.3
  tmux send-keys -t "${SESSION}:0.${pane}" Enter
  log "SENT P${pane}: $cmd"
  return 0
}

# ---- L1: TIER SELECTION ----
select_tier() {
  local state="$1"
  case "$state" in
    error|test_fail)  echo "standard";;
    escalate)         echo "max";;
    *)                echo "lite";;
  esac
}

# ---- L2: RUN MODE ----
select_mode() {
  local tier="$1"
  case "$tier" in
    max)      echo "--auto";;
    standard) echo "--auto";;
    lite)     echo "--fast";;
  esac
}

# ---- DETECT PANE STATE ----
detect_state() {
  local output="$1"
  local tail20
  tail20=$(echo "$output" | tail -20)
  if echo "$tail20" | grep -qiE "FAIL|tests? failed|✕"; then echo "test_fail"; return; fi
  if echo "$tail20" | grep -qiE "SyntaxError|TypeError|Cannot find|build failed|npm ERR"; then echo "error"; return; fi
  if echo "$tail20" | grep -qiE "Cooked|Sautéed|Baked|Done|committed|✅"; then echo "complete"; return; fi
  echo "fresh"
}

# ---- L5: SELECT COMMAND ----
select_command() {
  local state="$1" name="$2" dir="$3" deploy="$4"
  local ctx="Project: ${name}, Dir: ${dir}"
  case "$state" in
    error)
      echo "/dev-debug \"${ctx}. Analyze root cause, fix errors. Verify: ${deploy}\"";;
    test_fail)
      echo "/worker-test \"${ctx}. Fix failing tests, run full suite.\"";;
    complete)
      echo "/worker-commit \"chore(${name}): auto-commit completed work\"";;
    fresh)
      # Project-specific commands via mekong-cli
      case "$name" in
        algo-trader)
          echo "/worker-build \"${ctx}. Build + test. ${deploy}\"";;
        mekong-cli)
          echo "/eng-tech-debt \"${ctx}. Scan + fix tech debt. ${deploy}\"";;
        well|sophia*)
          echo "/dev-feature \"${ctx}. Continue next feature. ${deploy}\"";;
        raas*)
          echo "/raas-scaffold \"${ctx}. Bootstrap RAAS package.\"";;
        *)
          echo "/worker-build \"${ctx}. Build + test. ${deploy}\"";;
      esac;;
  esac
}

# ---- BOOTSTRAP: CREATE TMUX + START MEKONG ----
bootstrap() {
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    log "BOOTSTRAP: session '$SESSION' exists — killing"
    tmux kill-session -t "$SESSION" 2>/dev/null
    sleep 1
  fi

  log "BOOTSTRAP: creating session '$SESSION' with $PANE_COUNT panes"
  tmux new-session -d -s "$SESSION" -x 200 -y 60

  # Create panes
  for ((i=1; i<PANE_COUNT; i++)); do
    if ((i % 2 == 1)); then
      tmux split-window -h -t "${SESSION}:0"
    else
      tmux split-window -v -t "${SESSION}:0"
    fi
  done
  tmux select-layout -t "${SESSION}" tiled
  sleep 1

  # Start mekong --interactive in each pane
  for ((i=0; i<PANE_COUNT; i++)); do
    tmux send-keys -t "${SESSION}:0.${i}" "source ~/.zshrc 2>/dev/null && cd ${PROJECT_ROOT} && mekong --interactive" Enter
    log "BOOTSTRAP: P${i} → mekong --interactive"
  done

  # Wait for CC CLI to boot
  sleep 12

  # Auto-confirm trust
  for ((i=0; i<PANE_COUNT; i++)); do
    local content
    content=$(capture "$i")
    if echo "$content" | grep -q "trust this folder"; then
      tmux send-keys -t "${SESSION}:0.${i}" Enter
      log "BOOTSTRAP: P${i} → confirmed trust"
    fi
  done
  sleep 5
  log "BOOTSTRAP: done — $PANE_COUNT workers ready"
}

# ---- MAIN LOOP ----
log "================================================"
log "CTO DAEMON v4.0 — 7-Layer Manus Architecture"
log "Session: $SESSION | Poll: ${INTERVAL}s | Workers: $PANE_COUNT"
log "================================================"

bootstrap

CYCLE=0
LAST_DISPATCH=()
for ((i=0; i<PANE_COUNT; i++)); do LAST_DISPATCH[$i]=0; done
LAST_CMD=()
for ((i=0; i<PANE_COUNT; i++)); do LAST_CMD[$i]=""; done

while true; do
  CYCLE=$((CYCLE + 1))
  log "--- CYCLE $CYCLE ---"

  # L6: Kill switch
  if check_killswitch; then sleep "$INTERVAL"; continue; fi

  DISPATCHED=0
  for ((i=0; i<PANE_COUNT; i++)); do
    IFS='|' read -r name dir deploy <<< "${WORKERS[$i]}"
    local_output=$(capture "$i")

    # Skip if not idle
    if ! is_idle "$local_output"; then
      local state_info
      state_info=$(detect_state "$local_output")
      log "P${i} (${name}): WORKING [${state_info}]"

      # Auto-handle CC CLI dialogs
      if echo "$local_output" | tail -5 | grep -qE "Enter to select|Esc to cancel"; then
        tmux send-keys -t "${SESSION}:0.${i}" Enter
        log "P${i}: auto-confirmed dialog"
      fi
      continue
    fi

    # 1-dispatch-per-cycle limit
    if [[ $DISPATCHED -ge 1 ]]; then
      log "P${i} (${name}): IDLE (1-per-cycle limit)"
      continue
    fi

    # Cooldown: 300s between dispatches per pane
    now=0; elapsed=0
    now=$(date +%s)
    elapsed=$((now - ${LAST_DISPATCH[$i]}))
    if [[ $elapsed -lt 90 ]]; then
      log "P${i} (${name}): IDLE (cooldown ${elapsed}/90s)"
      continue
    fi

    # Detect state + select command via 7-Layer
    state=""; tier=""; mode=""; cmd=""
    state=$(detect_state "$local_output")
    tier=$(select_tier "$state")
    mode=$(select_mode "$tier")
    cmd=$(select_command "$state" "$name" "$dir" "$deploy")
    cmd="${cmd} ${mode}"

    log "L1-TIER P${i}(${name}): ${tier^^} | L2-MODE: ${mode} | STATE: ${state}"

    # DEDUP: skip if same command as last dispatch
    cmd_key=$(echo "$cmd" | awk "{print \$1}")
    if [[ "${LAST_CMD[$i]}" == "$cmd_key" && "$state" == "fresh" ]]; then
      log "DEDUP P${i} (${name}): skip repeat ${cmd_key} — rotating"
      # Rotate: pick different command for fresh state
      case "$cmd_key" in
        /eng-tech-debt) cmd="/worker-scan \"Project: ${name}. Scan codebase health.\" --fast";;
        /worker-build)  cmd="/worker-test \"Project: ${name}. Run all tests.\" --fast";;
        /dev-feature)   cmd="/dev-review \"Project: ${name}. Review code quality.\" --fast";;
        *)              cmd="/worker-health \"Project: ${name}. Health check.\" --fast";;
      esac
    fi

    if send_cmd "$i" "$cmd"; then
      LAST_DISPATCH[$i]=$(date +%s)
      DISPATCHED=$((DISPATCHED + 1))
      LAST_CMD[$i]=$(echo "$cmd" | awk "{print \$1}")
      log "DELEGATED P${i} (${name}) → ${cmd:0:80}"
    fi
  done

  sleep "$INTERVAL"
done
