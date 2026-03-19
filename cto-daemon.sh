#!/usr/bin/env bash
set -u

# ============================================================
# CTO DAEMON v2.0 — Full P→D→V→S Loop Implementation
# Source: apps/openclaw-worker/openclaw-cto-agent.md
#
# USAGE: ./cto-daemon.sh [--session NAME] [--interval SECS]
#
# Any dev cloning the repo can configure via:
#   .mekong/cto-config.json  (auto-created on first run)
# ============================================================

# ---- CONFIG (portable — auto-detect project root) ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$SCRIPT_DIR}"

# ---- TOOL ADAPTER (universal CLI support) ----
if [[ -f "$PROJECT_ROOT/mekong/adapters/registry.sh" ]]; then
  source "$PROJECT_ROOT/mekong/adapters/registry.sh"
  CTO_TOOL=$(select_tool "${MEKONG_TOOL:-auto}" 2>/dev/null || echo "claude")
else
  CTO_TOOL="claude"
fi
MEKONG_DIR="${PROJECT_ROOT}/.mekong"
CONFIG_FILE="${PROJECT_ROOT}/config/cto-config.json"
LOG_FILE="${MEKONG_DIR}/cto-daemon.log"
MEMORY_FILE="${MEKONG_DIR}/cto-memory.md"
JIDOKA_FILE="${MEKONG_DIR}/jidoka-alerts.log"

# Defaults (overridable via CLI flags)
CTO_SESSION="${CTO_SESSION:-tom_hum}"
POLL_INTERVAL="${POLL_INTERVAL:-30}"
MAX_LOG_LINES=1000

# Parse CLI flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --session) CTO_SESSION="$2"; shift 2 ;;
    --interval) POLL_INTERVAL="$2"; shift 2 ;;
    --project) PROJECT_ROOT="$2"; shift 2 ;;
    --help) echo "Usage: $0 [--session tmux_session] [--interval poll_secs] [--project /path]"; exit 0 ;;
    *) shift ;;
  esac
done

# ---- INIT ----
mkdir -p "$MEKONG_DIR"

# Auto-create config if not exists
if [[ ! -f "$CONFIG_FILE" ]]; then
  mkdir -p "$(dirname "$CONFIG_FILE")"
  cat > "$CONFIG_FILE" << 'CONF'
{
  "panes": {
    "0": { "project": "mekong-cli", "dir": "", "model": "qwen3.5-plus", "stack": "nodejs", "deploy_cmd": "pnpm run build" },
    "1": { "project": "algo-trader", "dir": "apps/algo-trader", "model": "qwen3-coder-plus", "stack": "typescript", "deploy_cmd": "npx tsc --noEmit" },
    "2": { "project": "sophia-ai-factory", "dir": "apps/sophia-proposal", "model": "qwen3.5-plus", "stack": "nextjs", "deploy_cmd": "npm run build" },
    "3": { "project": "well", "dir": "apps/well", "model": "qwen3.5-plus", "stack": "nextjs", "deploy_cmd": "npm run build" },
    "4": { "project": "opus-strategic", "dir": "", "model": "claude-opus-4-6", "stack": "strategic", "deploy_cmd": "" }
  },
  "daemon": {
    "auto_approve": true,
    "jidoka_enabled": true,
    "delegation_template": true,
    "max_retries": 3
  }
}
CONF
  echo "[CTO] Created default config at $CONFIG_FILE — edit to match your project."
fi

# ---- LOGGING ----
log() {
  local msg="[$(date '+%H:%M:%S')] $*"
  echo "$msg" | tee -a "$LOG_FILE"
  # Rotate log if too large
  if [[ $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0) -gt $MAX_LOG_LINES ]]; then
    tail -500 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
  fi
}

# ---- CTO BRAIN: Ollama qwen3:32b via scripts/brain_think.py ----
OLLAMA_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
OLLAMA_MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:32b}"

# Load 135-command catalog for brain dispatch (loaded once at startup)
COMMAND_CATALOG_FILE="${MEKONG_DIR}/commands-catalog.txt"
COMMAND_CATALOG=""
if [[ -f "$COMMAND_CATALOG_FILE" ]]; then
  COMMAND_CATALOG=$(cat "$COMMAND_CATALOG_FILE")
fi

# Call Ollama via standalone Python script (handles thinking mode, /no_think, keep_alive)
cto_brain_think() {
  local prompt="$1"
  local sd; sd="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  OLLAMA_URL="${OLLAMA_URL}" OLLAMA_MODEL="${OLLAMA_MODEL}" python3 "${sd}/scripts/brain_think.py" <<< "$prompt" 2>/dev/null || echo ""
}

# Build context-rich prompt and dispatch via brain
cto_brain_dispatch() {
  local pane_idx=$1 pane_output="$2"
  local name="${WORKER_NAME[$pane_idx]}"
  local dir="${WORKER_DIR[$pane_idx]}"
  local deploy="${WORKER_DEPLOY[$pane_idx]}"

  # Extract recent pane output (last 45 lines, collapsed)
  local pane_tail
  pane_tail=$(echo "$pane_output" | tail -45 | tr '\n' ' ' | cut -c1-800)

  # Detect errors in pane output for targeted dispatch
  local error_lines
  error_lines=$(echo "$pane_output" | tail -20 | grep -iE "error|failed|FAIL|TypeError|Cannot find|SyntaxError" | head -3 | tr '\n' ' ' | cut -c1-200)

  # Build catalog section
  local catalog_section
  if [[ -n "$COMMAND_CATALOG" ]]; then
    catalog_section="AVAILABLE COMMANDS:
${COMMAND_CATALOG}
Pick the MOST SPECIFIC command."
  else
    catalog_section="Commands: /cook \"task\" /debug \"issue\" /fix \"bug\" /test \"scope\" /plan:hard \"feature\" /review"
  fi

  local prompt="CTO daemon. Project: ${name} (dir: ${dir}). Deploy: ${deploy}.

PANE OUTPUT: ${pane_tail}
${error_lines:+ERRORS: ${error_lines}}

${catalog_section}

Give ONE slash command. Be SPECIFIC — include exact file paths, error descriptions, or feature names.
Examples:
- /debug \"TypeError in src/strategies/RsiSmaStrategy.ts line 45\"
- /eng-tech-debt \"clean up dead imports in src/core/\"
- /backend-api-build \"add rate limiting to /api/v1/missions\"
- /sre-morning-check
Reply with ONLY the command."

  local result
  result=$(cto_brain_think "$prompt")
  # Sanitize: extract only the /command part
  local cmd
  cmd=$(echo "$result" | grep -oE '/[a-z][a-z0-9_:-]*[[:space:]]+"[^"]*"' | head -1)
  if [[ -z "$cmd" ]]; then
    cmd=$(echo "$result" | grep -oE '/[a-z][a-z0-9_:-]*([[:space:]]+.*)?' | head -1 | cut -c1-200)
  fi
  echo "${cmd:-}"
}

# ---- WORKER CONFIG (read from config/cto-config.json — unified source of truth) ----
get_pane_config() {
  local idx=$1 field=$2
  if command -v python3 &>/dev/null && [[ -f "$CONFIG_FILE" ]]; then
    python3 -c "import json; c=json.load(open('$CONFIG_FILE')); print(c.get('panes',{}).get('$idx',{}).get('$field',''))" 2>/dev/null
  fi
}

# Load worker names and dirs from unified panes config
declare -A WORKER_NAME WORKER_DIR WORKER_DEPLOY WORKER_RETRIES
for idx in 1 2 3; do
  WORKER_NAME[$idx]=$(get_pane_config "$idx" "project")
  WORKER_DIR[$idx]=$(get_pane_config "$idx" "dir")
  WORKER_DEPLOY[$idx]=$(get_pane_config "$idx" "deploy_cmd")
  WORKER_RETRIES[$idx]=0
  [[ -z "${WORKER_NAME[$idx]}" ]] && WORKER_NAME[$idx]="Worker-$idx"
  [[ -z "${WORKER_DIR[$idx]}" ]] && WORKER_DIR[$idx]="."
  [[ -z "${WORKER_DEPLOY[$idx]}" ]] && WORKER_DEPLOY[$idx]="npm run build"
done

# Dynamic pane-to-project mapping: detect project from tmux pane_current_path
# This runs EVERY cycle so pane index changes (respawns/splits) are auto-detected
refresh_worker_mapping() {
  for idx in 1 2 3; do
    local pane_path
    pane_path=$(tmux display-message -t "${CTO_SESSION}:0.${idx}" -p '#{pane_current_path}' 2>/dev/null || echo "")
    if [[ -n "$pane_path" ]]; then
      local detected=""
      case "$pane_path" in
        */apps/algo-trader*)    detected="algo-trader"; WORKER_DIR[$idx]="apps/algo-trader"; WORKER_DEPLOY[$idx]="npx tsc --noEmit" ;;
        */apps/well*)           detected="well"; WORKER_DIR[$idx]="apps/well"; WORKER_DEPLOY[$idx]="npm run build" ;;
        */apps/sophia-proposal*|*/apps/sophia-ai-factory*) detected="sophia-ai-factory"; WORKER_DIR[$idx]="apps/sophia-proposal"; WORKER_DEPLOY[$idx]="npm run build" ;;
        */mekong-cli)           detected="mekong-cli"; WORKER_DIR[$idx]="."; WORKER_DEPLOY[$idx]="pnpm run build" ;;
      esac
      if [[ -n "$detected" && "$detected" != "${WORKER_NAME[$idx]}" ]]; then
        log "REMAP P${idx}: ${WORKER_NAME[$idx]} → ${detected} (path: ${pane_path})"
        WORKER_NAME[$idx]="$detected"
      fi
    fi
  done
}

# ---- TMUX HELPERS ----
capture_pane() {
  tmux capture-pane -t "${CTO_SESSION}:0.${1}" -p -S -50 2>/dev/null || echo ""
}

send_to_pane() {
  local pane_idx=$1; shift
  tmux send-keys -t "${CTO_SESSION}:0.${pane_idx}" "$*" Enter
}

# Launch/respawn a CLI pane via mekong-wrapper (unified entry point)
launch_pane_cc() {
  local pane_idx=$1
  local tool="${2:-$CTO_TOOL}"
  bash "${PROJECT_ROOT}/scripts/launch-pane-cc.sh" "$pane_idx" "${WORKER_DIR[$pane_idx]}" "$CTO_SESSION" "$tool"
}

# ---- PHASE 1: SCAN ----
# Reads codebase context on startup (per spec: CLAUDE.md, package.json, src/, git log)
phase_scan() {
  log "PHASE 1: SCAN — Reading codebase context"
  local scan_summary=""

  # 1. CLAUDE.md / AGENTS.md
  if [[ -f "${PROJECT_ROOT}/CLAUDE.md" ]]; then
    scan_summary+="Conventions: CLAUDE.md exists. "
  fi

  # 2. Stack detection
  if [[ -f "${PROJECT_ROOT}/package.json" ]]; then
    local stack
    stack=$(python3 -c "import json; p=json.load(open('${PROJECT_ROOT}/package.json')); deps=list(p.get('dependencies',{}).keys()); print(','.join(deps[:5]))" 2>/dev/null || echo "node")
    scan_summary+="Stack: Node ($stack). "
  elif [[ -f "${PROJECT_ROOT}/pyproject.toml" ]]; then
    scan_summary+="Stack: Python. "
  fi

  # 3. src/ structure
  local src_count
  src_count=$(find "${PROJECT_ROOT}/src" -name "*.py" -o -name "*.ts" -o -name "*.js" 2>/dev/null | wc -l | tr -d ' ')
  scan_summary+="Source files: ${src_count}. "

  # 4. Git log
  local last_commit
  last_commit=$(cd "$PROJECT_ROOT" && git log --oneline -1 2>/dev/null || echo "no git")
  scan_summary+="Last commit: ${last_commit}. "

  # 5. Apps directory
  local apps=""
  for app_dir in "${PROJECT_ROOT}"/apps/*/; do
    [[ -d "$app_dir" ]] && apps+="$(basename "$app_dir") "
  done
  scan_summary+="Apps: ${apps:-none}. "

  log "SCAN RESULT: $scan_summary"
  save_memory "SCAN" "$scan_summary"
}

# ---- DETECTION FUNCTIONS ----

# CC CLI activity patterns — if ANY of these appear in recent output, pane is BUSY
# Covers all known CC CLI spinner/status words + interactive prompts
BUSY_PATTERNS="thinking|Cooking|Baking|Stewing|Sautéed|Elucidating|Imagining|Crunching|Writing|Reading|Running|Searching|Bootstrapping|Wandering|Swooping|Pondering|Brewing|Frosting|Moonwalking|Concocting|Sautéing|Churning|Orbiting|Compacting|Ebbing|Hatching|Committing|Generating|Creating|Hashing|Blanching"
STUCK_PATTERNS="queued messages|Press up to edit queued"
QUESTION_PATTERNS="Do you want to proceed|Would you like"

is_idle() {
  local output="$1"

  # PRIORITY 1: Multi-tool idle detection (claude/gemini/opencode/aider)
  if echo "$output" | tail -3 | grep -qE "^❯|⏵⏵ bypass|Type your message|aider>|codex>|^>"; then
    return 0  # IDLE — pane is at prompt
  fi

  # No prompt → check if stuck/busy/question
  return 1  # NOT idle
}

# Check if pane is actively working (inverse of idle, but also catches stuck state)
is_busy() {
  local output="$1"
  local tail_lines
  tail_lines=$(echo "$output" | tail -15)
  echo "$tail_lines" | grep -qE "$BUSY_PATTERNS|$STUCK_PATTERNS|$QUESTION_PATTERNS"
}

has_question() {
  local output="$1"
  echo "$output" | tail -15 | grep -vE "🔋|⏰|📁|🌿|bypass|auto-compact|compact|model" | grep -qE "\?|Do you want|Would you like|proceed"
}

get_question() {
  local output="$1"
  echo "$output" | tail -15 | grep -vE "🔋|⏰|📁|🌿|bypass|auto-compact|compact|model" | grep -E "\?|Do you want|Would you like" | tail -1
}

has_error() {
  local output="$1"
  # Exclude CC CLI meta lines (✶ ◼ ⏺ ✻ ▸ ⎿ ●) which contain task titles with error-like words
  echo "$output" | tail -20 | grep -vE "^[[:space:]]*(✶|◼|⏺|✻|▸|⎿|●|⏵⏵|🤖|🔋|⏰|📁|🌿|Cooked|Worked|Crunched|Cogitated|bypass|auto-compact)" | grep -qiE "Error:|SyntaxError|TypeError|ImportError|ModuleNotFoundError|FAILED|exit code [1-9]|Build failed|Compilation failed"
}

get_error() {
  local output="$1"
  echo "$output" | tail -15 | grep -vE "^[[:space:]]*(✶|◼|⏺|✻|▸|⎿|●|⏵⏵)" | grep -iE "Error:|SyntaxError|TypeError|FAILED|exit code|Build failed" | tail -1
}

# Jidoka: detect stop-the-line conditions (per spec)
check_jidoka() {
  local output="$1" pane_idx="$2"
  # Detect: breaking tests, schema changes, security issues
  if echo "$output" | grep -qiE "BREAKING|security vulnerability|database migration|schema change"; then
    local alert="🚨 STOP-THE-LINE P${pane_idx}: $(echo "$output" | grep -iE 'BREAKING|security|migration|schema' | tail -1)"
    log "$alert"
    echo "$alert" >> "$JIDOKA_FILE"
    return 0  # jidoka triggered
  fi
  return 1  # no jidoka
}

# ---- COMMAND CATALOG (config/cto-command-catalog.json) ----
CATALOG_FILE="${PROJECT_ROOT}/config/cto-command-catalog.json"

# Read a field from the command catalog via python3 (cached per cycle)
_catalog_cache=""
catalog_query() {
  local query="$1"
  if [[ -z "$_catalog_cache" && -f "$CATALOG_FILE" ]]; then
    _catalog_cache=$(cat "$CATALOG_FILE" 2>/dev/null || echo "{}")
  fi
  if [[ -n "$_catalog_cache" ]]; then
    python3 -c "
import json, sys
c = json.loads(sys.stdin.read())
keys = '${query}'.split('.')
v = c
for k in keys:
    if isinstance(v, dict):
        v = v.get(k, '')
    elif isinstance(v, list):
        v = v[int(k)] if k.isdigit() and int(k) < len(v) else ''
    else:
        v = ''
        break
if isinstance(v, list): print(' '.join(v))
else: print(v)
" <<< "$_catalog_cache" 2>/dev/null || echo ""
  fi
}

# Get project profile field from catalog
get_project_profile() {
  local project="$1" field="$2"
  catalog_query "project_profiles.${project}.${field}"
}

# ---- PHASE 2: PLAN — Analyze pane state and build proper mekong-cli command ----

# Classify pane state from captured output
# Returns: error|test_fail|lint_error|complete|fresh
detect_pane_state() {
  local output="$1"
  local tail20
  tail20=$(echo "$output" | tail -20)

  # Test failures
  if echo "$tail20" | grep -qiE "FAIL\s|tests? failed|✕|✗|test.*error"; then
    echo "test_fail"
    return
  fi

  # Lint errors (distinct from build errors)
  if echo "$tail20" | grep -qiE "lint.*error|eslint|prettier.*error"; then
    echo "lint_error"
    return
  fi

  # Build/runtime errors
  if echo "$tail20" | grep -qiE "error|failed|SyntaxError|TypeError|Cannot find"; then
    echo "error"
    return
  fi

  # Completed work (success indicators from CC CLI)
  if echo "$tail20" | grep -qiE "Cooked|Sautéed|Baked|Brewed|Stewed|Done|committed|pushed|✅"; then
    echo "complete"
    return
  fi

  echo "fresh"
}

# Extract error context from pane output for targeted debugging
extract_error_context() {
  local output="$1"
  echo "$output" | tail -20 | grep -iE "error|failed|FAIL|Cannot|TypeError|SyntaxError" | head -3 | tr '\n' ' ' | cut -c1-200
}

# Build the right mekong-cli command based on pane state + project profile from catalog
build_delegation_task() {
  local pane_idx=$1
  local pane_output="${2:-}"
  local name="${WORKER_NAME[$pane_idx]}"
  local dir="${WORKER_DIR[$pane_idx]}"
  local deploy="${WORKER_DEPLOY[$pane_idx]}"
  local retries="${WORKER_RETRIES[$pane_idx]}"

  local state="fresh"
  if [[ -n "$pane_output" ]]; then
    state=$(detect_pane_state "$pane_output")
  fi

  # Read project profile from catalog
  local layer idle_cmd error_cmd
  layer=$(get_project_profile "$name" "layer")
  idle_cmd=$(get_project_profile "$name" "idle_command")
  error_cmd=$(get_project_profile "$name" "error_command")
  # Defaults if catalog missing
  layer="${layer:-engineering}"
  idle_cmd="${idle_cmd:-/cook}"
  error_cmd="${error_cmd:-/debug}"

  local ctx="Project: ${name}, Dir: ${dir}"
  local constraints="Do NOT touch files outside ${dir}. Follow existing patterns."

  case "$state" in
    error)
      local error_ctx
      error_ctx=$(extract_error_context "$pane_output")
      if [[ "$retries" -ge 3 ]]; then
        # Escalate: switch to /plan:hard after 3 failed retries
        echo "/plan:hard \"${ctx}. ESCALATION: ${retries} retries failed. Error: ${error_ctx}. Analyze root cause deeply, create plan before fixing.\""
      elif [[ "$retries" -gt 0 ]]; then
        echo "${error_cmd} \"RETRY #${retries}. ${ctx}. Error: ${error_ctx}. Analyze root cause, fix, verify: ${deploy}\""
      else
        echo "${error_cmd} \"${ctx}. Error: ${error_ctx}. Fix all errors then verify: ${deploy}\""
      fi
      ;;
    test_fail)
      echo "/test \"${ctx}. Tests failing. Analyze failures, fix source or tests. ${constraints}\""
      ;;
    lint_error)
      echo "/fix \"${ctx}. Lint errors detected. Fix all lint issues. ${constraints}\""
      ;;
    complete)
      echo "/git \"chore(${name}): auto-commit completed work\""
      ;;
    fresh|*)
      # Use project-specific idle command from catalog
      echo "${idle_cmd} \"${ctx}. Run: ${deploy}. Fix ALL errors. ${constraints}\" --auto"
      ;;
  esac
}

# ---- PHASE 3: DELEGATE ----
# Accepts: pane_idx [pane_output]
dispatch_worker() {
  local pane_idx=$1
  local pane_output="${2:-}"
  local name="${WORKER_NAME[$pane_idx]}"

  # Priority 1: Check for pending mission files matching this worker's project
  local mission_dir="${MEKONG_DIR}/missions"
  if [[ -d "$mission_dir" ]]; then
    for mf in "$mission_dir"/*.json; do
      [[ -f "$mf" ]] || continue
      local m_parsed
      m_parsed=$(python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('project','')); print(d.get('goal',''))" < "$mf" 2>/dev/null || echo "")
      local m_project m_goal
      m_project=$(echo "$m_parsed" | head -1)
      m_goal=$(echo "$m_parsed" | tail -n +2)
      if [[ "$m_project" == "$name" && -n "$m_goal" ]]; then
        # Mission files may contain explicit commands (/cook, /debug, etc.)
        local m_first_word
        m_first_word=$(echo "$m_goal" | awk '{print $1}')
        local cmd
        if [[ "$m_first_word" == /* ]]; then
          cmd="$m_goal"  # Already a command
        else
          cmd="/cook \"$m_goal\""  # Wrap in /cook
        fi
        log "MISSION FILE: $mf → P${pane_idx} (${name}) [${m_first_word}]"
        send_to_pane "$pane_idx" "$cmd"
        mv "$mf" "${mf}.done"
        log "DELEGATED P${pane_idx} (${name}) — MISSION from file"
        return
      fi
    done
  fi

  # Priority 2: Ask CTO Brain (Ollama qwen3:32b) for intelligent dispatch
  local brain_cmd
  brain_cmd=$(cto_brain_dispatch "$pane_idx" "$pane_output")
  if [[ -n "$brain_cmd" ]]; then
    log "P${pane_idx} (${name}): BRAIN → ${brain_cmd}"
    send_to_pane "$pane_idx" "$brain_cmd"
    log "DELEGATED P${pane_idx} (${name}) — BRAIN dispatch"
    return
  fi

  # Priority 3: Fallback to static state-aware command selection
  local task
  task=$(build_delegation_task "$pane_idx" "$pane_output")
  local chosen_cmd
  chosen_cmd=$(echo "$task" | awk '{print $1}')
  log "P${pane_idx} (${name}): FALLBACK STATE=$(detect_pane_state "$pane_output") → CMD=${chosen_cmd}"
  send_to_pane "$pane_idx" "$task"
  log "DELEGATED P${pane_idx} (${name}) — ${chosen_cmd}"
}

# ---- PHASE 4: VERIFY ----
verify_worker() {
  local pane_idx=$1 output="$2"
  local name="${WORKER_NAME[$pane_idx]}"

  # Check for questions → auto-answer
  if has_question "$output"; then
    local question
    question=$(get_question "$output")
    log "VERIFY P${pane_idx}: QUESTION: $question → AUTO-ANSWERING (key=1)"
    # Send just the option number — NOT a full sentence (CC CLI interprets text as new prompt)
    send_to_pane "$pane_idx" "1"
    save_memory "VERIFY" "Auto-answered P${pane_idx}: ${question}"
    return 0
  fi

  # Check for errors → only re-delegate if pane is IDLE (not busy/stuck)
  if has_error "$output" && is_idle "$output" && ! is_busy "$output"; then
    local error_msg
    error_msg=$(get_error "$output")
    WORKER_RETRIES[$pane_idx]=$((${WORKER_RETRIES[$pane_idx]} + 1))

    if [[ ${WORKER_RETRIES[$pane_idx]} -le 3 ]]; then
      log "VERIFY P${pane_idx}: ERROR DETECTED — re-delegating (retry ${WORKER_RETRIES[$pane_idx]})"
      log "  Error: $error_msg"
      dispatch_worker "$pane_idx" "$output"
      save_memory "RE-DELEGATE" "P${pane_idx} retry ${WORKER_RETRIES[$pane_idx]}: ${error_msg}"
    else
      log "VERIFY P${pane_idx}: MAX RETRIES REACHED — escalating"
      save_memory "ESCALATE" "P${pane_idx} failed after 3 retries: ${error_msg}"
    fi
    return 0
  fi

  # Jidoka check
  if check_jidoka "$output" "$pane_idx"; then
    log "VERIFY P${pane_idx}: JIDOKA TRIGGERED — halting worker"
    return 0
  fi

  return 1  # no action needed
}

# ---- PHASE 5: INTEGRATE ----
phase_integrate() {
  cd "$PROJECT_ROOT" || return

  # Check for merge conflicts
  if git diff --name-only --diff-filter=U 2>/dev/null | grep -q .; then
    log "INTEGRATE: MERGE CONFLICTS DETECTED"
    save_memory "INTEGRATE" "Merge conflicts found"
    return
  fi

  # Push any unpushed commits
  local unpushed
  unpushed=$(git log origin/master..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$unpushed" -gt "0" ]]; then
    log "INTEGRATE: Pushing $unpushed commits..."
    if git push origin master 2>&1 | tail -3 >> "$LOG_FILE"; then
      log "INTEGRATE: Push SUCCESS"
      save_memory "SHIP" "Pushed $unpushed commits to master"
    else
      log "INTEGRATE: Push FAILED"
    fi
  fi
}

# ---- MEMORY PERSISTENCE (spec Rule 5) ----
save_memory() {
  local phase="$1" detail="$2"
  {
    echo "## $(date '+%Y-%m-%d %H:%M:%S') — ${phase}"
    echo "- ${detail}"
    echo ""
  } >> "$MEMORY_FILE"
}

# ---- M1 HEALTH CHECK ----
health_check() {
  local load ram ssd
  load=$(sysctl -n vm.loadavg 2>/dev/null || echo "N/A")
  ram=$(vm_stat 2>/dev/null | awk '/free/ {print $3}' | head -1 || echo "N/A")
  ssd=$(df -h / 2>/dev/null | awk 'NR==2{print $4}' || echo "N/A")
  log "HEALTH: Load=${load} RAM_free=${ram} SSD_free=${ssd}"
}

# ============================================================
# MAIN LOOP — P→D→V→S forever
# Hardened: trap errors so daemon never exits
# ============================================================

# Safety net: log but don't exit on errors
trap 'log "TRAP: Error at line $LINENO (ignored — daemon continues)"' ERR

log "============================================="
log "CTO DAEMON v3.0 — Universal CLI + P→D→V→S"
log "Session: ${CTO_SESSION} | Poll: ${POLL_INTERVAL}s"
log "Tool: ${CTO_TOOL} | Project: ${PROJECT_ROOT}"
log "Workers: P1=${WORKER_NAME[1]} P2=${WORKER_NAME[2]} P3=${WORKER_NAME[3]}"
log "Config: ${CONFIG_FILE}"
log "============================================="

# PHASE 1: Initial SCAN on startup
phase_scan

CYCLE=0
LAST_DISPATCH_1=0
LAST_DISPATCH_2=0
LAST_DISPATCH_3=0
DISPATCH_COOLDOWN=90
while true; do
  CYCLE=$((CYCLE + 1))
  NOW=$(date +%s)
  _catalog_cache=""  # Clear catalog cache each cycle (pick up config changes)
  log "--- CYCLE $CYCLE ---"

  # Re-detect which project is in which pane (handles index shifts from respawns)
  refresh_worker_mapping

  # PHASE 3+4: For each worker, DELEGATE if idle or VERIFY if active
  for pane_idx in 1 2 3; do
    # Guard: any failure in per-pane logic must not kill the loop
    {
      output=$(capture_pane "$pane_idx") || output=""
      name="${WORKER_NAME[$pane_idx]:-Worker-${pane_idx}}"

      if [[ -z "$output" ]]; then
        log "P${pane_idx} (${name}): NO OUTPUT (pane dead?) — respawning via mekong-wrapper ($CTO_TOOL)"
        launch_pane_cc "$pane_idx" "$CTO_TOOL" || true
        continue
      fi

      # PHASE 4: VERIFY — check questions, errors, jidoka
      if verify_worker "$pane_idx" "$output"; then
        continue  # verify handled the worker
      fi

      # If idle and not recently dispatched → DELEGATE new task (with cooldown)
      if is_idle "$output"; then
        ld_var="LAST_DISPATCH_${pane_idx}"
        last_dispatch="${!ld_var:-0}"
        elapsed=$((NOW - last_dispatch))
        if [[ $elapsed -ge $DISPATCH_COOLDOWN ]]; then
          log "P${pane_idx} (${name}): IDLE → DELEGATING"
          WORKER_RETRIES[$pane_idx]=0
          dispatch_worker "$pane_idx" "$output"
          eval "LAST_DISPATCH_${pane_idx}=$NOW"
        else
          log "P${pane_idx} (${name}): IDLE (cooldown ${elapsed}/${DISPATCH_COOLDOWN}s)"
        fi
      else
        # Worker is active — extract status from expanded pattern set
        status_word=$(echo "$output" | tail -15 | grep -oE "$BUSY_PATTERNS|$STUCK_PATTERNS|Commit" | tail -1) || status_word=""
        log "P${pane_idx} (${name}): WORKING (${status_word:-active})"
      fi
    } || log "CYCLE $CYCLE P${pane_idx}: ERROR IN PANE LOOP (continuing)"
  done

  # PHASE 5: INTEGRATE — push, check conflicts
  phase_integrate || log "CYCLE $CYCLE: INTEGRATE ERROR (continuing)"

  # Health check every 5 cycles
  if [[ $((CYCLE % 5)) -eq 0 ]]; then
    health_check || true
  fi

  # Re-scan every 20 cycles to update context
  if [[ $((CYCLE % 20)) -eq 0 ]]; then
    phase_scan || true
  fi

  sleep "$POLL_INTERVAL"
done
