#!/opt/homebrew/bin/bash
# ═══════════════════════════════════════════════════════════════
# DOANH TRẠI TÔM HÙM — Master Multi-Department Daemon
# Polls all non-engineering tmux sessions, dispatches dept-specific tasks
# Engineering (tom_hum) managed by cto-daemon.sh separately
# Usage: bash scripts/doanh-trai-daemon.sh
# ═══════════════════════════════════════════════════════════════
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MEKONG_DIR="${PROJECT_ROOT}/.mekong"
CONFIG_FILE="${PROJECT_ROOT}/config/doanh-trai-departments.yaml"
LOG_FILE="${MEKONG_DIR}/doanh-trai.log"
API_USAGE_FILE="${MEKONG_DIR}/api-usage.log"
TASK_RUNNER="${SCRIPT_DIR}/dept-task-runner.sh"
POLL_INTERVAL=120
MAX_LOG_LINES=2000
DAILY_API_LIMIT=5000  # 2 API keys × 90k = 180k/mo = 6k/day, cap at 5k

# Departments that use LOCAL Ollama only (content gen — Qwen3:32b sufficient)
LOCAL_ONLY_DEPTS="mktg"
# Departments that use CC CLI API (code changes + RaaS-critical quality)
CODE_DEPTS="sales docs ops design"

mkdir -p "$MEKONG_DIR"

# ---- LOGGING ----
log() {
  local ts
  ts=$(date '+%H:%M:%S')
  echo "[$ts] $*" >> "$LOG_FILE"
  echo "[$ts] $*"
  # Rotate log
  if [[ $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_LINES ]]; then
    tail -$((MAX_LOG_LINES / 2)) "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
  fi
}

# ---- PARSE YAML CONFIG ----
# Returns: session|panes|task1|||task2|||task3 for each non-existing dept
parse_departments() {
  python3 -c "
import yaml, sys
with open('${CONFIG_FILE}') as f:
    cfg = yaml.safe_load(f)
for name, dept in cfg.get('departments', {}).items():
    if dept.get('existing', False):
        continue  # Skip engineering (managed by cto-daemon.sh)
    session = dept.get('session', '')
    panes = dept.get('panes', 2)
    tasks = '|||'.join(dept.get('fallback_tasks', []))
    print(f'{name}|{session}|{panes}|{tasks}')
" 2>/dev/null
}

# ---- IDLE DETECTION ----
is_pane_idle() {
  local output="$1"
  # LOCK 1: NOT idle if tool actively running
  if echo "$output" | tail -15 | grep -qE "⏺|✳|Quantumizing|Scurrying|Writing|Reading|Thinking|Searching|Running|Brewing|Cooked|Cogitating|Crunching"; then
    return 1
  fi
  # LOCK 1b: NOT idle if dialog/queued state
  if echo "$output" | tail -10 | grep -qiE "queued messages|Press up to edit|Exit plan mode|Enter to select|Yes.*No|arrow keys"; then
    return 1
  fi
  # CC CLI idle: shows prompt character or ">" at end
  echo "$output" | tail -5 | grep -qE '^\$|^>|^❯|waiting for input|^claude>|⏵⏵ bypass' 2>/dev/null
}

# ---- PANE LOCK (2-way dispatch protection) ----
PANE_LOCK_DIR="${MEKONG_DIR}/pane-lock"
mkdir -p "$PANE_LOCK_DIR"
LOCK_TIMEOUT=600

acquire_pane_lock() {
  local session=$1 pane=$2
  local lock_file="${PANE_LOCK_DIR}/${session}-${pane}.lock"
  if [[ -f "$lock_file" ]]; then
    local age=$(( $(date +%s) - $(stat -f %m "$lock_file" 2>/dev/null || echo 0) ))
    [[ $age -lt $LOCK_TIMEOUT ]] && return 1
    rm -f "$lock_file"
  fi
  touch "$lock_file"
  return 0
}

release_pane_lock() {
  local session=$1 pane=$2
  rm -f "${PANE_LOCK_DIR}/${session}-${pane}.lock"
}

# ---- CAPTURE PANE ----
capture_pane() {
  local session=$1 pane_idx=$2
  tmux capture-pane -t "${session}:0.${pane_idx}" -p -S -50 2>/dev/null || echo ""
}

# ---- SEND COMMAND TO PANE ----
send_to_pane() {
  local session=$1 pane_idx=$2 cmd=$3
  tmux send-keys -t "${session}:0.${pane_idx}" "$cmd" Enter 2>/dev/null
}

# ---- RESPAWN DEAD PANE ----
respawn_pane() {
  local session=$1 pane_idx=$2
  log "RESPAWN ${session}:${pane_idx} — launching CC CLI"
  tmux send-keys -t "${session}:0.${pane_idx}" \
    "cd ${PROJECT_ROOT} && claude --dangerously-skip-permissions" Enter 2>/dev/null
}

# ---- BRAIN DISPATCH (dept-aware) ----
OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:32b}"

brain_dispatch_dept() {
  local dept_name=$1 pane_output=$2
  local pane_tail
  pane_tail=$(echo "$pane_output" | tail -30 | tr '\n' ' ' | cut -c1-500)

  local prompt="CTO Brain. Department: ${dept_name}. Goal: Sell RaaS.
PANE: ${pane_tail}
Give ONE /cook command specific to ${dept_name} department work. Be specific with file paths.
Reply ONLY the command."

  local result
  result=$(OLLAMA_URL="$OLLAMA_URL" OLLAMA_MODEL="$OLLAMA_MODEL" \
    python3 "${SCRIPT_DIR}/brain_think.py" <<< "$prompt" 2>>"${MEKONG_DIR}/brain-errors.log" || echo "")

  # Extract /command
  if [[ -n "$result" ]]; then
    local cmd
    cmd=$(echo "$result" | sed 's/^[^/]*//' | head -1 | grep -oE '/[a-z][a-z0-9_:-]*([ ]+(".*"|.+))?' | head -1 | cut -c1-300)
    [[ -n "$cmd" ]] && echo "$cmd"
  fi
}

# ---- MAIN LOOP ----
log "═══════════════════════════════════════════════════════"
log "DOANH TRẠI DAEMON started — polling non-eng departments"
log "Config: ${CONFIG_FILE}"
log "Poll interval: ${POLL_INTERVAL}s"
log "═══════════════════════════════════════════════════════"

# Warmup Ollama + reset stuck panes
bash "${SCRIPT_DIR}/warmup-ollama.sh" 2>/dev/null || log "WARN: Ollama warmup failed"
bash "${SCRIPT_DIR}/reset-full-panes.sh" 2>/dev/null || true

# Parse departments once at startup
declare -A DEPT_SESSION DEPT_PANES DEPT_TASKS DEPT_TASK_IDX
while IFS='|' read -r name session panes tasks; do
  DEPT_SESSION[$name]="$session"
  DEPT_PANES[$name]="$panes"
  DEPT_TASKS[$name]="$tasks"
  DEPT_TASK_IDX[$name]=0
done < <(parse_departments)

log "Departments loaded: ${!DEPT_SESSION[*]}"

CYCLE=0
while true; do
  CYCLE=$((CYCLE + 1))
  log "--- CYCLE $CYCLE ---"

  for dept_name in "${!DEPT_SESSION[@]}"; do
    session="${DEPT_SESSION[$dept_name]}"
    panes="${DEPT_PANES[$dept_name]}"

    # Check if session exists
    if ! tmux has-session -t "$session" 2>/dev/null; then
      log "${dept_name} (${session}): SESSION NOT RUNNING — skip"
      continue
    fi

    for ((pane_idx=0; pane_idx<panes; pane_idx++)); do
      output=$(capture_pane "$session" "$pane_idx")

      if [[ -z "$output" ]]; then
        log "${dept_name} P${pane_idx}: DEAD — respawning"
        respawn_pane "$session" "$pane_idx"
        continue
      fi

      # Context 90%+ or 100% → /clear (hard reset)
      if echo "$output" | tail -10 | grep -qE "Context:.*100%|Context:.*9[0-9]%|auto-compact|Auto-compacting"; then
        log "${dept_name} P${pane_idx}: CONTEXT ≥90% → /clear"
        send_to_pane "$session" "$pane_idx" "/clear"
        continue
      fi
      # Context 80-89% → /compact
      if echo "$output" | tail -10 | grep -qE "Context:.*8[0-9]%"; then
        log "${dept_name} P${pane_idx}: CONTEXT 80-89% → /compact"
        send_to_pane "$session" "$pane_idx" "/compact"
        continue
      fi

      # Only dispatch if idle
      if ! is_pane_idle "$output"; then
        log "${dept_name} P${pane_idx}: WORKING"
        continue
      fi

      # Release lock if truly idle
      release_pane_lock "$session" "$pane_idx"

      # Acquire lock before dispatch
      if ! acquire_pane_lock "$session" "$pane_idx"; then
        log "${dept_name} P${pane_idx}: LOCKED — skip"
        continue
      fi

      # Check API budget — if over limit, force local-only for ALL depts
      daily_usage=0
      today=$(date '+%Y-%m-%d')
      if [[ -f "$API_USAGE_FILE" ]]; then
        daily_usage=$(grep -c "^${today}" "$API_USAGE_FILE" 2>/dev/null || echo 0)
      fi
      budget_exceeded=false
      [[ "$daily_usage" -gt "$DAILY_API_LIMIT" ]] && budget_exceeded=true

      # Route: LOCAL_ONLY depts → Ollama directly (no CC CLI burn)
      if echo "$LOCAL_ONLY_DEPTS" | grep -qw "$dept_name" || [[ "$budget_exceeded" == true ]]; then
        # Use dept-task-runner.sh with Ollama — zero API cost
        IFS='|||' read -ra task_arr <<< "${DEPT_TASKS[$dept_name]}"
        if [[ ${#task_arr[@]} -gt 0 ]]; then
          tidx=${DEPT_TASK_IDX[$dept_name]:-0}
          task="${task_arr[$tidx]}"
          if [[ -z "$task" || "$task" == "|||" ]]; then continue; fi
          # Strip /cook prefix — task runner takes raw description
          task_desc=$(echo "$task" | sed 's|^/[a-z_:-]* *"*||; s|"*$||')
          DEPT_TASK_IDX[$dept_name]=$(( (tidx + 1) % ${#task_arr[@]} ))
          log "${dept_name} P${pane_idx}: LOCAL[${tidx}] → ${task_desc}"
          bash "$TASK_RUNNER" "$dept_name" "$task_desc" >> "$LOG_FILE" 2>&1 &
        fi
        continue
      fi

      # CODE depts (ops, design) → use CC CLI pane but with budget tracking
      echo "${today} ${dept_name} P${pane_idx}" >> "$API_USAGE_FILE"

      # Try brain dispatch first
      brain_cmd=""
      brain_cmd=$(brain_dispatch_dept "$dept_name" "$output" 2>/dev/null || echo "")
      if [[ -n "$brain_cmd" ]]; then
        log "${dept_name} P${pane_idx}: BRAIN → ${brain_cmd}"
        send_to_pane "$session" "$pane_idx" "$brain_cmd"
        continue
      fi

      # Fallback for code depts
      IFS='|||' read -ra task_arr <<< "${DEPT_TASKS[$dept_name]}"
      if [[ ${#task_arr[@]} -gt 0 ]]; then
        tidx=${DEPT_TASK_IDX[$dept_name]:-0}
        task="${task_arr[$tidx]}"
        DEPT_TASK_IDX[$dept_name]=$(( (tidx + 1) % ${#task_arr[@]} ))
        if [[ -z "$task" || "$task" == "|||" ]]; then
          log "${dept_name} P${pane_idx}: SKIP empty task"
          continue
        fi
        log "${dept_name} P${pane_idx}: CC-CLI[${tidx}] → ${task}"
        send_to_pane "$session" "$pane_idx" "$task"
      else
        log "${dept_name} P${pane_idx}: NO TASKS CONFIGURED"
      fi
    done
  done

  sleep "$POLL_INTERVAL"
done
