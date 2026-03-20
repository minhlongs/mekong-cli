#!/usr/bin/env -S bash
# Requires bash 4+ (macOS: /opt/homebrew/bin/bash)
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

# ---- CTO DNA: MISSION ----
RAAS_GOAL="Sell RaaS (ROI-as-a-Service). Packages: raas-landing, raas-dashboard, mekong-engine. Priority: landing page polish → API hardening → dashboard working → tests green → deploy pipeline."

# ---- DOANH TRẠI: Pane Roles (Binh Pháp military model) ----
# P1=TIÊN PHONG (complex/plan), P2=CÔNG BINH (build/fix), P3=HIẾN BINH (review/test)
PANE_ROLE_0="tien_phong"   # Pane 0: mekong-cli monorepo — complex/planning tasks
PANE_ROLE_1="tien_phong"   # Complex tasks: /plan hard, /cook complex features, /debug hard bugs
PANE_ROLE_2="cong_binh"    # Build tasks: /cook build, /fix, /code, /backend-api-build
PANE_ROLE_3="hien_binh"    # Review tasks: /review, /test, /check-and-commit

# Role-specific fallback tasks (indexed arrays — bash 3.2 compatible)
ROLE_FB_0_0='/idea "OpenClaw RaaS Gateway: Robot-as-a-Service platform API. Metered AI agent execution, multi-tenant billing, Cloudflare edge. Target: SaaS founders. Revenue: MCU billing."'
ROLE_FB_0_1='/cook "Read .mekong/company.json and execute next 5-layer command toward $1M ARR. If no company.json, run /idea first."'
ROLE_FB_0_2='/studio-strategy "Portfolio analysis: evaluate all apps/ projects for RaaS readiness and $1M ARR potential."'
ROLE_FB_0_COUNT=3

ROLE_FB_1_0='/idea "Algo-Trader: AI-powered crypto arbitrage engine. Multi-exchange spread detection, automated execution. Target: institutional traders. Revenue: SaaS + performance fees."'
ROLE_FB_1_1='/cook "Read .mekong/company.json and execute 5-layer GTM toward $1M ARR. Focus: fix bugs → build features → deploy production."'
ROLE_FB_1_2='/sales-pipeline-build "Build sales pipeline for current project. ICP, outreach sequences, deal stages."'
ROLE_FB_1_COUNT=3

ROLE_FB_2_0='/idea "WellNexus: B2B healthcare platform for VN hospitals. Patient management, telemedicine, pharmacy integration. Target: 1000+ private clinics. Revenue: SaaS per-clinic."'
ROLE_FB_2_1='/cook "Harden mekong-engine API — input validation on all routes"'
ROLE_FB_2_2='/cook "Build missing frontend components in dashboard pages"'
ROLE_FB_2_COUNT=3

ROLE_FB_3_0='/idea "Sophia AI Factory: AI proposal generator for agencies. Auto-generates pitch decks, SOWs, contracts. Target: digital agencies. Revenue: tiered SaaS."'
ROLE_FB_3_1='/test "Run all tests in packages/mekong-engine — fix any failures"'
ROLE_FB_3_2='/cook "Add error handling and edge case coverage to API endpoints"'
ROLE_FB_3_COUNT=3

# ---- DEDUP GUARD: track last dispatched command per pane ----
DEDUP_STATE_FILE="${MEKONG_DIR:-$HOME/.mekong}/dedup-state"
declare -A LAST_DISPATCH_CMD  # pane_idx → last command sent
declare -A LAST_DISPATCH_TIME # pane_idx → epoch when sent
declare -A PANE_RESPAWN_COUNT   # FIX #12: replace eval with associative array
declare -A LAST_ANSWER_TIME     # FIX #12: replace eval with associative array
DEDUP_MIN_INTERVAL=300        # seconds before allowing same command again

# FIX #8: normalize commands for dedup (brain rephrasing no longer bypasses)
_normalize_dedup() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9/]/ /g' | tr -s ' ' | cut -c1-60
}

is_duplicate_dispatch() {
  local pane_idx=$1 cmd=$2
  local norm=$(_normalize_dedup "$cmd")
  local last_norm=$(_normalize_dedup "${LAST_DISPATCH_CMD[$pane_idx]:-}")
  local last_time="${LAST_DISPATCH_TIME[$pane_idx]:-0}"
  local now
  now=$(date +%s)
  if [[ "$norm" == "$last_norm" && $((now - last_time)) -lt $DEDUP_MIN_INTERVAL ]]; then
    return 0
  fi
  return 1
}

record_dispatch() {
  local pane_idx=$1 cmd=$2
  LAST_DISPATCH_CMD[$pane_idx]="$cmd"
  LAST_DISPATCH_TIME[$pane_idx]=$(date +%s)
}

# Persist fallback index across restarts
FALLBACK_STATE_FILE="${MEKONG_DIR:-$HOME/.mekong}/fallback-state"
FALLBACK_IDX_1=0; FALLBACK_IDX_2=0; FALLBACK_IDX_3=0
if [[ -f "$FALLBACK_STATE_FILE" ]]; then
  read -r _f1 _f2 _f3 < "$FALLBACK_STATE_FILE" 2>/dev/null || true
  FALLBACK_IDX_1=${_f1:-0}; FALLBACK_IDX_2=${_f2:-0}; FALLBACK_IDX_3=${_f3:-0}
fi

# Helper: get pane role
get_pane_role() { eval echo "\${PANE_ROLE_${1}:-cong_binh}"; }
# Helper: get fallback command for pane
get_fallback_cmd() {
  local pidx=$1
  local fidx_var="FALLBACK_IDX_${pidx}"
  local fidx=${!fidx_var:-0}
  local cmd_var="ROLE_FB_${pidx}_${fidx}"
  local cmd=${!cmd_var:-"/cook \"RaaS build check\""}
  local count_var="ROLE_FB_${pidx}_COUNT"
  local count=${!count_var:-3}
  eval "${fidx_var}=$(( (fidx + 1) % count ))"
  echo "$FALLBACK_IDX_1 $FALLBACK_IDX_2 $FALLBACK_IDX_3" > "$FALLBACK_STATE_FILE"
  echo "$cmd"
}

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

# ---- OLLAMA HEALTH CHECK + AUTO-RECOVERY ----
# HARDCODED — never depend on env vars for Ollama native API
OLLAMA_URL="http://127.0.0.1:11434"
OLLAMA_MODEL="${OPENCLAW_WORKER_MODEL:-qwen3:32b}"
BRAIN_CONSECUTIVE_FAILS=0
BRAIN_MAX_FAILS=3

# Check if Ollama is alive and model loaded
ollama_health_check() {
  # 1. Check Ollama server responding
  if ! curl -sf "${OLLAMA_URL}/" >/dev/null 2>&1; then
    log "OLLAMA HEALTH: Server DOWN at ${OLLAMA_URL}"
    return 1
  fi

  # 2. Check model is loaded (in ps output)
  local ps_output
  ps_output=$(curl -sf "${OLLAMA_URL}/api/ps" 2>/dev/null || echo "")
  if [[ -z "$ps_output" ]] || ! echo "$ps_output" | python3 -c "import json,sys; d=json.load(sys.stdin); models=[m['name'] for m in d.get('models',[])]; sys.exit(0 if any('${OLLAMA_MODEL}'.split(':')[0] in m for m in models) else 1)" 2>/dev/null; then
    log "OLLAMA HEALTH: Model ${OLLAMA_MODEL} NOT loaded"
    return 2
  fi

  return 0
}

# Auto-recover Ollama: restart serve + pull/warmup model
ollama_auto_recover() {
  log "OLLAMA RECOVERY: Starting auto-recovery sequence..."

  # Step 1: Check if ollama serve is running
  if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
    log "OLLAMA RECOVERY: Launching ollama serve..."
    nohup ollama serve >/dev/null 2>&1 &
    sleep 5
  fi

  # Step 2: Verify server is up
  local attempts=0
  while [[ $attempts -lt 10 ]]; do
    if curl -sf "${OLLAMA_URL}/" >/dev/null 2>&1; then
      log "OLLAMA RECOVERY: Server alive after ${attempts}s"
      break
    fi
    attempts=$((attempts + 1))
    sleep 2
  done

  if [[ $attempts -ge 10 ]]; then
    log "OLLAMA RECOVERY: FAILED — server not responding after 20s"
    save_memory "BRAIN" "CRITICAL: Ollama server failed to start"
    return 1
  fi

  # Step 3: Warmup model (keep_alive ensures it stays loaded)
  log "OLLAMA RECOVERY: Warming up ${OLLAMA_MODEL}..."
  curl -sf "${OLLAMA_URL}/api/generate" -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"ping\",\"stream\":false,\"keep_alive\":\"5m\"}" >/dev/null 2>&1 || true
  sleep 2

  # Step 4: Verify model loaded
  if ollama_health_check; then
    log "OLLAMA RECOVERY: SUCCESS — ${OLLAMA_MODEL} loaded and ready"
    save_memory "BRAIN" "Ollama auto-recovered, model ${OLLAMA_MODEL} loaded"
    return 0
  else
    log "OLLAMA RECOVERY: Model warmup failed — may need manual intervention"
    return 1
  fi
}

# ---- CTO BRAIN: Ollama qwen3:32b via scripts/brain_think.py ----

# Load 135-command catalog for brain dispatch (loaded once at startup)
COMMAND_CATALOG_FILE="${MEKONG_DIR}/commands-catalog.txt"
COMMAND_CATALOG=""
if [[ -f "$COMMAND_CATALOG_FILE" ]]; then
  COMMAND_CATALOG=$(cat "$COMMAND_CATALOG_FILE")
fi

# Call Ollama via standalone Python script with 45s hard timeout
# Uses bash background + wait to prevent daemon hang on brain freeze
BRAIN_TIMEOUT=45

cto_brain_think() {
  local prompt="$1"
  local sd; sd="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local tmpfile="${MEKONG_DIR}/brain-output.tmp"

  # Run brain in background with hard timeout
  (OLLAMA_URL="${OLLAMA_URL}" OLLAMA_MODEL="${OLLAMA_MODEL}" \
    python3 "${sd}/scripts/brain_think.py" <<< "$prompt" \
    > "$tmpfile" 2>>"${MEKONG_DIR}/brain-errors.log") &
  local brain_pid=$!

  # Wait with timeout (portable macOS — no gtimeout needed)
  local elapsed=0
  while kill -0 "$brain_pid" 2>/dev/null && [[ $elapsed -lt $BRAIN_TIMEOUT ]]; do
    sleep 1
    elapsed=$((elapsed + 1))
  done

  # Kill if still running (timed out)
  if kill -0 "$brain_pid" 2>/dev/null; then
    kill "$brain_pid" 2>/dev/null
    wait "$brain_pid" 2>/dev/null
    echo "[$(date '+%H:%M:%S')] BRAIN: TIMEOUT after ${BRAIN_TIMEOUT}s" >> "$LOG_FILE"
    BRAIN_CONSECUTIVE_FAILS=$((BRAIN_CONSECUTIVE_FAILS + 1))
    rm -f "$tmpfile"
    echo ""
    return
  fi

  wait "$brain_pid" 2>/dev/null
  local result
  result=$(cat "$tmpfile" 2>/dev/null)
  rm -f "$tmpfile"

  if [[ -z "$result" ]]; then
    BRAIN_CONSECUTIVE_FAILS=$((BRAIN_CONSECUTIVE_FAILS + 1))
    if [[ $BRAIN_CONSECUTIVE_FAILS -ge $BRAIN_MAX_FAILS ]]; then
      echo "[$(date '+%H:%M:%S')] BRAIN CRITICAL: ${BRAIN_CONSECUTIVE_FAILS} fails — auto-recovering" >> "$LOG_FILE"
      ollama_auto_recover
      BRAIN_CONSECUTIVE_FAILS=0
    fi
    echo ""
    return
  fi

  BRAIN_CONSECUTIVE_FAILS=0
  echo "$result"
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

  # Codebase context for brain (cached per cycle via _codebase_ctx)
  if [[ -z "${_codebase_ctx:-}" ]]; then
    local file_count recent_commits
    file_count=$(find "${dir}" -name "*.ts" -o -name "*.tsx" -o -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
    recent_commits=$(cd "${dir}" && git log --oneline -3 2>/dev/null | tr '\n' ' ' | cut -c1-200)
    _codebase_ctx="FILES: ${file_count} source files. RECENT: ${recent_commits}"
  fi

  # Build catalog section
  local catalog_section
  if [[ -n "$COMMAND_CATALOG" ]]; then
    catalog_section="AVAILABLE COMMANDS:
${COMMAND_CATALOG}
Pick the MOST SPECIFIC command."
  else
    catalog_section="Commands: /cook \"task\" /debug \"issue\" /fix \"bug\" /test \"scope\" /plan hard \"feature\" /review"
  fi

  # Role context for this pane
  local role=$(get_pane_role "$pane_idx")
  local role_desc
  case "$role" in
    tien_phong) role_desc="TIÊN PHONG (complex): /plan hard, /debug hard bugs, /cook complex features" ;;
    cong_binh)  role_desc="CÔNG BINH (build): /cook build, /fix, /backend-api-build, /frontend-ui-build" ;;
    hien_binh)  role_desc="HIẾN BINH (review): /review, /test, /check-and-commit, /code-review" ;;
  esac

  local prompt="GOAL: ${RAAS_GOAL}
You are CTO Brain (QUÂN SƯ). Dispatching PANE ${pane_idx} role: ${role_desc}

PROJECT: ${name} | DIR: ${dir} | DEPLOY: ${deploy}
CONSTRAINT: ONLY modify files inside ${dir}/. Do NOT touch other projects.
${_codebase_ctx}
PANE OUTPUT: ${pane_tail}
${error_lines:+ERRORS: ${error_lines}}

${catalog_section}

THINK: What is the SINGLE most impactful action for ${name} to make RaaS sellable?
Priority: fix errors → fix tests → polish UI → harden API → add features.
Give ONE slash command. Include \"${dir}/\" in the task description.
CRITICAL: ONLY use commands from the AVAILABLE COMMANDS list above.
NEVER use colon syntax (e.g. /plan:hard). Use SPACE: /plan hard, /cto-architect, /pm-sprint.
If unsure, default to /cook.
Reply with ONLY the command. No explanation."

  local result
  result=$(cto_brain_think "$prompt")
  [[ -z "$result" ]] && return

  # Strip Qwen thinking prefix: everything before first /command
  local stripped
  stripped=$(echo "$result" | sed 's/^[^\/]*//' | head -1)

  # Extract /command with optional args (quoted or unquoted)
  local cmd
  cmd=$(echo "$stripped" | grep -oE '/[a-z][a-z0-9_:-]*([ ]+(".*"|.+))?' | head -1 | cut -c1-300)
  if [[ -n "$cmd" ]]; then
    # VALIDATE: check command base exists in catalog or core commands
    local cmd_base
    cmd_base=$(echo "$cmd" | awk '{print $1}')
    local valid_cores="/cook /fix /debug /test /review /plan hard /plan fast /check-and-commit /clear /compact /docs /docs update"
    if ! echo " $valid_cores " | grep -q " $cmd_base "; then
      # Check commands-catalog.txt
      if [[ -f "$COMMAND_CATALOG_FILE" ]] && ! grep -q "^${cmd_base}$" "$COMMAND_CATALOG_FILE" 2>/dev/null; then
        # Check .claude/commands/ and .claude/skills/ directories
        local cmd_name="${cmd_base#/}"
        if [[ ! -d "${PROJECT_ROOT}/.claude/skills/${cmd_name}" ]] && [[ ! -f "${PROJECT_ROOT}/.claude/commands/${cmd_name}.md" ]]; then
          echo "[$(date '+%H:%M:%S')] BRAIN: invalid command '${cmd_base}' — falling back to /cook" >> "$LOG_FILE"
          cmd="/cook $(echo "$cmd" | sed "s|^${cmd_base} *||")"
        fi
      fi
    fi
    # If bare command (no args), append project context
    if ! echo "$cmd" | grep -qE '".*"| '; then
      cmd="${cmd} \"Project: ${name}, Dir: ${dir}. Fix errors, improve code quality.\""
    fi
    echo "$cmd"
  else
    # Write directly to log (NOT via log() which uses tee → stdout → captured by $())
    echo "[$(date '+%H:%M:%S')] BRAIN: unparseable response: $(echo "$result" | head -1 | cut -c1-80)" >> "$LOG_FILE"
  fi
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
for idx in 0 1 2 3; do
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
  # Use config file as source of truth — NEVER auto-remap from pane path
  # CC CLI always runs from monorepo root, so pane_current_path is unreliable
  for idx in 0 1 2 3; do
    # Only load from config if not already set (first run)
    if [[ -z "${WORKER_NAME[$idx]:-}" ]]; then
      WORKER_NAME[$idx]=$(get_pane_config "$idx" "project")
      WORKER_DIR[$idx]=$(get_pane_config "$idx" "dir")
      WORKER_DEPLOY[$idx]=$(get_pane_config "$idx" "deploy_cmd")
    fi
  done
}

# ---- TMUX HELPERS ----
capture_pane() {
  tmux capture-pane -t "${CTO_SESSION}:0.${1}" -p -S -50 2>/dev/null || echo ""
}

send_to_pane() {
  local pane_idx=$1; shift
  local cmd="$*"
  if [[ "$cmd" != "1" ]]; then
    local fresh_output
    fresh_output=$(capture_pane "$pane_idx" 2>/dev/null || echo "")
    if [[ -n "$fresh_output" ]] && ! is_idle "$fresh_output"; then
      echo "[$(date '+%H:%M:%S')] SAFETY GATE: Blocked send to P${pane_idx} (pane BUSY): ${cmd:0:80}" >> "$LOG_FILE"
      return 1
    fi
    # FIX #1: TOCTOU double-check — re-capture and run full is_idle (same logic, no divergence)
    local recheck_output
    recheck_output=$(capture_pane "$pane_idx" 2>/dev/null || echo "")
    if [[ -n "$recheck_output" ]] && ! is_idle "$recheck_output"; then
      echo "[$(date '+%H:%M:%S')] SAFETY GATE RECHECK: P${pane_idx} no longer idle: ${cmd:0:80}" >> "$LOG_FILE"
      return 1
    fi
  fi
  # Inject project scope: ensure CC CLI works in correct project directory
  local worker_dir="${WORKER_DIR[$pane_idx]:-}"
  if [[ -n "$worker_dir" && "$worker_dir" != "." && "$cmd" == /* ]]; then
    if ! echo "$cmd" | grep -qF "$worker_dir"; then
      # Replace closing quote with scope + closing quote
      if echo "$cmd" | grep -qF '"'; then
        cmd="${cmd%\"} SCOPE: Only work in ${worker_dir}/.\""
      fi
    fi
  fi
  tmux send-keys -t "${CTO_SESSION}:0.${pane_idx}" "$cmd" Enter
}

# Launch/respawn a CLI pane via mekong-wrapper (unified entry point)
launch_pane_cc() {
  local pane_idx=$1
  local tool="${2:-$CTO_TOOL}"
  bash "${PROJECT_ROOT}/scripts/launch-pane-cc.sh" "$pane_idx" "${WORKER_DIR[$pane_idx]}" "$CTO_SESSION" "$tool"
}

# ─── ORPHAN NODE CLEANUP (prevents RAM overflow) ───
# CC CLI spawns node subprocesses. When panes restart/crash, orphans accumulate.
# This kills node processes NOT attached to any active tmux pane.
cleanup_orphan_nodes() {
  local killed=0
  local MAX_NODE_COUNT=30

  # FIX #9: only count/kill CC CLI-related node processes (not system-wide)
  local node_count
  node_count=$(pgrep -f 'node.*claude\|node.*@anthropic' 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$node_count" -gt "$MAX_NODE_COUNT" ]]; then
    log "⚠️  GUARD: $node_count CC CLI node processes (>${MAX_NODE_COUNT}) — killing CC CLI nodes"
    pkill -9 -f 'node.*claude|node.*@anthropic' 2>/dev/null || true
    return 0
  fi

  # Build set of ALL PIDs in tmux pane process trees (recursive)
  local allowed_pids=""
  local tmux_pids
  tmux_pids=$(tmux list-panes -t "${CTO_SESSION}" -F '#{pane_pid}' 2>/dev/null || true)
  [[ -z "$tmux_pids" ]] && return 0

  # Walk tree: collect pid + all descendants via pgrep -P (recursive)
  walk_descendants() {
    local parent=$1
    allowed_pids+=" $parent"
    local children
    children=$(pgrep -P "$parent" 2>/dev/null || true)
    for child in $children; do
      walk_descendants "$child"
    done
  }

  for tpid in $tmux_pids; do
    walk_descendants "$tpid"
  done

  # Find all node processes, kill those NOT in allowed set
  local all_nodes
  all_nodes=$(pgrep -f 'node' 2>/dev/null || true)
  [[ -z "$all_nodes" ]] && return 0

  for pid in $all_nodes; do
    if ! echo " $allowed_pids " | grep -q " $pid "; then
      kill -9 "$pid" 2>/dev/null && killed=$((killed + 1))
    fi
  done

  [[ $killed -gt 0 ]] && log "🧹 CLEANUP: killed $killed orphan node processes"
  return 0
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
  local tail10 tail15
  tail10=$(echo "$output" | tail -10)
  tail15=$(echo "$output" | tail -15)

  # GUARD 1: "queued messages" = task stuffed, NEVER idle
  if echo "$tail10" | grep -qiE "queued messages|Press up to edit"; then
    return 1
  fi

  # PRIORITY CHECK: clean ❯ prompt = IDLE (check BEFORE busy guards)
  if echo "$tail10" | grep -qE "^[[:space:]]*❯[[:space:]]*$"; then
    return 0
  fi

  # CC CLI idle: ⏵⏵ visible + NO busy icons in last 8 lines = truly idle
  # ⏵⏵ is status bar (always visible), so ONLY count as idle if no active work above it
  if echo "$output" | tail -3 | grep -qE "⏵⏵"; then
    if ! echo "$output" | tail -8 | grep -qE "⏺|✽|✳|✢|●|◼|▸|Thinking|Running\.\.\.|Searching\.\.\.|pending"; then
      return 0  # IDLE — status bar visible, no active work
    fi
  fi

  # No clean prompt found — check if genuinely busy
  # GUARD 2: CC CLI ACTIVE icons only (NOT completion icons)
  # ✻ = COMPLETION ("Cooked for 48s") — NOT busy!
  # ✶ = COMPLETION variant — NOT busy!
  # Only match: ⏺ (tool output) ✽ (cooking) ✳ (working) ✢ (phase) ● (active) ◼ (subtask)
  if echo "$tail15" | grep -qE "⏺|✽|✳|✢|●|◼|▸"; then
    return 1
  fi

  # GUARD 3: CC CLI busy verbs (context-aware — require active spinner prefix)
  if echo "$tail15" | grep -qE "^[[:space:]]*[·✽✳✢⏺●].*Thinking|Running\.\.\.|Searching\.\.\.|Bash\(|Update\(|Write\(|Search\("; then
    return 1
  fi

  # IDLE: Completion markers + prompt visible
  if echo "$tail15" | grep -qE "Brewed for|Cooked for|Crunched for|Churned for|Cogitated for|Sautéed for|Baked for"; then
    return 0  # Task finished, at prompt
  fi

  # IDLE: non-CC CLI tool prompts
  if echo "$output" | tail -2 | grep -qE "aider>|codex>|Type your message"; then
    return 0
  fi

  # Default: NOT idle (safe)
  return 1
}

# ---- PANE LOCK (2-way dispatch protection) ----
PANE_LOCK_DIR="${MEKONG_DIR}/pane-lock"
mkdir -p "$PANE_LOCK_DIR"
LOCK_TIMEOUT=600  # 10 minutes

acquire_pane_lock() {
  local session=$1 pane=$2
  local lock_file="${PANE_LOCK_DIR}/${session}-${pane}.lock"
  # Check if lock exists and not expired
  if [[ -f "$lock_file" ]]; then
    # FIX #7: cross-platform stat (macOS: -f %m, Linux: -c %Y)
    local mtime
    mtime=$(stat -f %m "$lock_file" 2>/dev/null || stat -c %Y "$lock_file" 2>/dev/null || echo 0)
    local age=$(( $(date +%s) - mtime ))
    if [[ $age -lt $LOCK_TIMEOUT ]]; then
      return 1  # Lock held, skip dispatch
    fi
    # Lock expired, remove it
    rm -f "$lock_file"
  fi
  touch "$lock_file"
  return 0
}

release_pane_lock() {
  local session=$1 pane=$2
  rm -f "${PANE_LOCK_DIR}/${session}-${pane}.lock"
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
  # FIX #4: strict patterns — exclude code output, error messages, URLs
  local candidate
  candidate=$(echo "$output" | tail -8 | grep -vE '🔋|⏰|📁|🌿|bypass|auto-compact|model|Error:|Cannot|TODO|FIXME|http|\.ts|\.js|\.py')
  echo "$candidate" | grep -qE 'Do you want to|Would you like to|Should I |Shall I |Pick an option|Select.*:|Choose.*:|Y/n|\(y/N\)'
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

  # Build/runtime errors (strict: require real error patterns, not "0 errors" or "error handling")
  if echo "$tail20" | grep -qiE "SyntaxError|TypeError|ReferenceError|Cannot find module|ENOENT|EACCES|Segmentation fault|panic:|fatal:|build failed|exit code [1-9]|npm ERR!|error TS[0-9]"; then
    echo "error"
    return
  fi
  # Fallback: lines starting with "Error:" or "ERROR" (not substring matches)
  if echo "$tail20" | grep -qE "^(Error:|ERROR[: ])|command failed|exited with"; then
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
        # Escalate: switch to /plan hard after 3 failed retries
        echo "/plan hard \"${ctx}. ESCALATION: ${retries} retries failed. Error: ${error_ctx}. Analyze root cause deeply, create plan before fixing.\""
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

  # LOCK 2: Check pane lock before dispatch
  if ! acquire_pane_lock "${CTO_SESSION}" "$pane_idx"; then
    log "P${pane_idx} (${name}): LOCKED — skip dispatch (task in progress)"
    return
  fi

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
    if is_duplicate_dispatch "$pane_idx" "$brain_cmd"; then
      log "P${pane_idx} (${name}): DEDUP — skipping duplicate brain cmd"
      return
    fi
    log "P${pane_idx} (${name}): BRAIN WARM → ${brain_cmd}"
    if send_to_pane "$pane_idx" "$brain_cmd"; then
      record_dispatch "$pane_idx" "$brain_cmd"
      log "DELEGATED P${pane_idx} (${name}) — BRAIN dispatch [$(get_pane_role "$pane_idx")]"
    else
      log "P${pane_idx} (${name}): BRAIN cmd BLOCKED by safety gate"
    fi
    return
  fi
  log "P${pane_idx} (${name}): BRAIN COLD/EMPTY — using role fallback"

  # Priority 3: Role-specific fallback (round-robin per pane role)
  local state="fresh"
  if [[ -n "$pane_output" ]]; then
    state=$(detect_pane_state "$pane_output")
  fi

  if [[ "$state" == "fresh" || "$state" == "complete" ]]; then
    # Pick from role-specific fallback array (bash 3.2 compatible)
    local fallback_cmd=$(get_fallback_cmd "$pane_idx")
    local pane_role=$(get_pane_role "$pane_idx")
    if is_duplicate_dispatch "$pane_idx" "$fallback_cmd"; then
      log "P${pane_idx} (${name}): DEDUP — skipping duplicate fallback [${pane_role}]"
      return
    fi
    log "P${pane_idx} (${name}): FALLBACK[${pane_role}]: ${fallback_cmd}"
    if send_to_pane "$pane_idx" "$fallback_cmd"; then
      record_dispatch "$pane_idx" "$fallback_cmd"
    fi
    return
  fi

  local task
  task=$(build_delegation_task "$pane_idx" "$pane_output")
  local chosen_cmd
  chosen_cmd=$(echo "$task" | awk '{print $1}')
  if is_duplicate_dispatch "$pane_idx" "$chosen_cmd"; then
    log "P${pane_idx} (${name}): DEDUP — skipping duplicate ${chosen_cmd} (wait ${DEDUP_MIN_INTERVAL}s)"
    return
  fi
  log "P${pane_idx} (${name}): FALLBACK STATE=${state} → CMD=${chosen_cmd}"
  if send_to_pane "$pane_idx" "$task"; then
    record_dispatch "$pane_idx" "$chosen_cmd"
    log "DELEGATED P${pane_idx} (${name}) — ${chosen_cmd}"
  fi
}

# ---- PHASE 4: VERIFY ----
verify_worker() {
  local pane_idx=$1 output="$2"
  local name="${WORKER_NAME[$pane_idx]}"

  # CC CLI selection dialogs — auto-select option 1 (Enter)
  if echo "$output" | tail -5 | grep -qE "Enter to select|↑/↓ to navigate|Esc to cancel"; then
    log "VERIFY P${pane_idx}: SELECTION DIALOG → Enter (pick default)"
    tmux send-keys -t "${CTO_SESSION}:0.${pane_idx}" Enter
    return 0
  fi

  # SESSION COMPLETE detection — /clear immediately to recycle pane
  # IMPORTANT: only check tail -5 to avoid matching old scroll history from previous sessions
  if echo "$output" | tail -5 | grep -qiE "Session Complete|Hẹn gặp lại|All Tasks Done|Task hoàn thành|Session kết thúc|goodbye|signing off"; then
    if is_idle "$output"; then
      log "VERIFY P${pane_idx}: SESSION COMPLETE → /clear for new task"
      send_to_pane "$pane_idx" "/clear"
      save_memory "RECYCLE" "P${pane_idx}: session complete, cleared for new dispatch"
      return 0
    fi
  fi

  # CI POLLING STUCK detection — FIX #5: tighten ranges + require idle
  if echo "$output" | tail -8 | grep -qE "gh run list|gh run view|Waiting.*CI|checking.*deploy"; then
    if echo "$output" | tail -10 | grep -qE "git push|pushed to"; then
      if is_idle "$output"; then
        log "VERIFY P${pane_idx}: CI POLLING STUCK (commit done + idle) → Ctrl-C + /clear"
        tmux send-keys -t "${CTO_SESSION}:0.${pane_idx}" C-c "" 2>/dev/null
        sleep 1
        send_to_pane "$pane_idx" "/clear"
        save_memory "UNSTUCK" "P${pane_idx}: broke CI polling loop after commit"
        return 0
      fi
    fi
  fi

  # Context management — ONLY when pane is IDLE (never interrupt active work)
  if is_idle "$output"; then
    # Context 90%+ or 100% → /clear (hard reset)
    # FIX #6: anchor to CC CLI format (has ━ progress bar) — prevents matching code output
    if echo "$output" | tail -5 | grep -qE 'Context:[[:space:]]*100%[[:space:]]*━|Context:[[:space:]]*9[0-9]%[[:space:]]*━|auto-compact|Auto-compacting'; then
      log "VERIFY P${pane_idx}: CONTEXT ≥90% + IDLE → /clear"
      send_to_pane "$pane_idx" "/clear"
      save_memory "CLEAR" "P${pane_idx}: context ≥90%, hard reset"
      return 0
    fi
    # Context 80-89% → /compact (soft compress)
    if echo "$output" | tail -5 | grep -qE 'Context:[[:space:]]*8[0-9]%[[:space:]]*━'; then
      log "VERIFY P${pane_idx}: CONTEXT 80-89% + IDLE → /compact"
      send_to_pane "$pane_idx" "/compact"
      save_memory "COMPACT" "P${pane_idx}: context 80-89%, compacted"
      return 0
    fi
  else
    # Log but don't interrupt working panes
    if echo "$output" | tail -10 | grep -qE "Context:.*[89][0-9]%|Context:.*100%"; then
      log "P${pane_idx} (${name}): CONTEXT HIGH but WORKING — skipping clear/compact"
    fi
  fi

  # Check for questions — CC CLI asking for user input
  # Send "1" (pick first option) to unblock, NOT /compact (which causes loop)
  if has_question "$output"; then
    local question
    question=$(get_question "$output")
    # Skip if we already answered recently (prevent answer loop)
    local last_answer_time="${LAST_ANSWER_TIME[$pane_idx]:-0}"
    local now_ts
    now_ts=$(date +%s)
    if [[ $((now_ts - last_answer_time)) -lt 120 ]]; then
      log "P${pane_idx} (${name}): QUESTION skipped (answered <120s ago)"
      return 0
    fi
    LAST_ANSWER_TIME[$pane_idx]=$now_ts
    # FIX #10: context-aware answer — pick "proceed/yes" not "cancel"
    local answer="1"
    local options_text
    options_text=$(echo "$output" | tail -10 | grep -E '^[[:space:]]*[0-9]+[).:]')
    if echo "$options_text" | grep -qiE '2.*proceed|2.*yes|2.*continue|2.*accept'; then
      answer="2"
    fi
    log "VERIFY P${pane_idx}: QUESTION → answering '${answer}': ${question}"
    send_to_pane "$pane_idx" "$answer"
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
  # Auto-detect default branch (main or master)
  local default_branch
  default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
  unpushed=$(git log "origin/${default_branch}..HEAD" --oneline 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$unpushed" -gt "0" ]]; then
    log "INTEGRATE: Pushing $unpushed commits to ${default_branch}..."
    if git push origin "${default_branch}" 2>&1 | tail -3 >> "$LOG_FILE"; then
      log "INTEGRATE: Push SUCCESS"
      save_memory "SHIP" "Pushed $unpushed commits to ${default_branch}"
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

# ---- SINGLETON GUARD: prevent multiple daemon instances ----
PIDFILE="${MEKONG_DIR}/cto-daemon.pid"

# FIX #14: flock if available (more robust), mkdir fallback
LOCKDIR="${MEKONG_DIR}/cto-daemon.lockdir"
if command -v flock >/dev/null 2>&1; then
  exec 9>"${MEKONG_DIR}/cto-daemon.flock"
  if ! flock -n 9; then
    echo "CTO DAEMON already running (flock). Exiting."
    exit 1
  fi
fi
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  # Lock exists — check if holder is still alive
  if [[ -f "$PIDFILE" ]]; then
    old_pid=$(cat "$PIDFILE" 2>/dev/null)
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
      echo "CTO DAEMON already running (PID $old_pid). Exiting."
      exit 1
    fi
  fi
  # Stale lock — reclaim
  rm -rf "$LOCKDIR"
  mkdir "$LOCKDIR" 2>/dev/null || { echo "Cannot acquire lock"; exit 1; }
fi

echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"; rm -rf "$LOCKDIR"; log "DAEMON SHUTDOWN (PID $$)"' EXIT INT TERM
trap 'log "TRAP: Error at line $LINENO (ignored — daemon continues)"' ERR

log "============================================="
log "CTO DAEMON v3.0 — Universal CLI + P→D→V→S"
log "Session: ${CTO_SESSION} | Poll: ${POLL_INTERVAL}s"
log "Tool: ${CTO_TOOL} | Project: ${PROJECT_ROOT}"
log "Workers: P1=${WORKER_NAME[1]} P2=${WORKER_NAME[2]} P3=${WORKER_NAME[3]}"
log "Config: ${CONFIG_FILE}"
log "============================================="

# Ensure tmux session exists with 3 panes (required for daemon operation)
if ! tmux has-session -t "${CTO_SESSION}" 2>/dev/null; then
  log "BOOTSTRAP: tmux session '${CTO_SESSION}' not found — creating with 3 panes"
  tmux new-session -d -s "${CTO_SESSION}" -x 200 -y 50
  tmux split-window -t "${CTO_SESSION}:0" -h
  tmux split-window -t "${CTO_SESSION}:0" -v
  sleep 1
  log "BOOTSTRAP: tmux session '${CTO_SESSION}' created with 3 panes"
else
  # Verify pane count
  pane_count=$(tmux list-panes -t "${CTO_SESSION}:0" 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$pane_count" -lt 4 ]]; then
    log "BOOTSTRAP: Only ${pane_count} panes in '${CTO_SESSION}' — adding missing panes"
    while [[ "$pane_count" -lt 4 ]]; do
      tmux split-window -t "${CTO_SESSION}:0" 2>/dev/null || break
      pane_count=$((pane_count + 1))
    done
  fi
  log "BOOTSTRAP: tmux session '${CTO_SESSION}' OK (${pane_count} panes)"
fi

# Warmup Ollama brain model before first cycle
# Inline warmup — non-blocking (10s max), uses hardcoded OLLAMA_URL
{
  curl -sf --max-time 10 "${OLLAMA_URL}/api/generate" \
    -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":\"5m\",\"options\":{\"num_predict\":1}}" >/dev/null 2>&1 \
    && log "OLLAMA: ${OLLAMA_MODEL} warm" \
    || log "OLLAMA: warmup skipped (will retry on first dispatch)"
} &

# Reset any panes stuck at 100% context
bash "${PROJECT_ROOT}/scripts/reset-full-panes.sh" "${CTO_SESSION}" 2>/dev/null || true

# PHASE 1: Initial SCAN on startup
phase_scan

CYCLE=0
LAST_DISPATCH_1=0
LAST_DISPATCH_2=0
LAST_DISPATCH_3=0
DISPATCH_COOLDOWN=90  # FIX #13: reduced from 180s — less idle waste
CRASH_COUNT=0

while true; do
  # Wrap entire cycle in error trap — never let one bad cycle kill daemon
  {
  CYCLE=$((CYCLE + 1))
  NOW=$(date +%s)
  _catalog_cache=""
  _codebase_ctx=""
  log "--- CYCLE $CYCLE ---"

  # FIX #15: log rotation (every 100 cycles, cap at 5MB)
  if [[ $((CYCLE % 100)) -eq 0 ]] && [[ -f "$LOG_FILE" ]]; then
    log_bytes=$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)
    if [[ $log_bytes -gt 5000000 ]]; then
      tail -2000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
      log "LOG ROTATED (was ${log_bytes} bytes)"
    fi
  fi

  # Re-detect which project is in which pane (handles index shifts from respawns)
  refresh_worker_mapping

  # PHASE 3+4: For each worker, DELEGATE if idle or VERIFY if active
  # FIX: max 1 dispatch per cycle (brain call takes 30s → prevents serial stuffing)
  dispatched_this_cycle=false
  for pane_idx in 0 1 2 3; do
    # Guard: any failure in per-pane logic must not kill the loop
    {
      output=$(capture_pane "$pane_idx") || output=""
      name="${WORKER_NAME[$pane_idx]:-Worker-${pane_idx}}"

      if [[ -z "$output" ]]; then
        # Guard: limit respawns to prevent infinite restart loop
        local respawn_count="${PANE_RESPAWN_COUNT[$pane_idx]:-0}"
        if [[ $respawn_count -ge 3 ]]; then
          log "P${pane_idx} (${name}): NO OUTPUT — respawn limit reached (${respawn_count}/3), skipping until next health cycle"
          continue
        fi
        log "P${pane_idx} (${name}): NO OUTPUT (pane dead?) — respawning via mekong-wrapper ($CTO_TOOL) [${respawn_count}/3]"
        launch_pane_cc "$pane_idx" "$CTO_TOOL" || true
        PANE_RESPAWN_COUNT[$pane_idx]=$((respawn_count + 1))
        continue
      fi
      # Reset respawn counter on successful output
      PANE_RESPAWN_COUNT[$pane_idx]=0

      # PHASE 4: VERIFY — check questions, errors, jidoka
      if verify_worker "$pane_idx" "$output"; then
        continue  # verify handled the worker
      fi

      # If idle → release lock + check missions/dispatch
      if is_idle "$output"; then
        release_pane_lock "${CTO_SESSION}" "$pane_idx"

        # FIX: skip dispatch if already dispatched another pane this cycle
        if [[ "$dispatched_this_cycle" == true ]]; then
          log "P${pane_idx} (${name}): IDLE (1-dispatch-per-cycle limit)"
          continue
        fi

        # FIX: double-sample idle check (1s apart) to close race window
        sleep 1
        recheck_output=$(capture_pane "$pane_idx" 2>/dev/null || echo "")
        if [[ -n "$recheck_output" ]] && ! is_idle "$recheck_output"; then
          log "P${pane_idx} (${name}): IDLE→BUSY detected (double-sample), skipping"
          continue
        fi

        # Priority 0: mission files bypass cooldown entirely
        mission_dir="${MEKONG_DIR}/missions"
        has_mission=false
        if [[ -d "$mission_dir" ]]; then
          for mf in "$mission_dir"/*.json; do
            [[ -f "$mf" ]] && has_mission=true && break
          done
        fi
        if [[ "$has_mission" == true ]]; then
          log "P${pane_idx} (${name}): IDLE + MISSION FILE → DISPATCHING (bypass cooldown)"
          WORKER_RETRIES[$pane_idx]=0
          dispatch_worker "$pane_idx" "$output"
          eval "LAST_DISPATCH_${pane_idx}=$NOW"
          dispatched_this_cycle=true
          sleep 2  # Let pane accept command before checking next pane
        else
          ld_var="LAST_DISPATCH_${pane_idx}"
          last_dispatch="${!ld_var:-0}"
          elapsed=$((NOW - last_dispatch))
          if [[ $elapsed -ge $DISPATCH_COOLDOWN ]]; then
            log "P${pane_idx} (${name}): IDLE → DELEGATING"
            WORKER_RETRIES[$pane_idx]=0
            dispatch_worker "$pane_idx" "$output"
            eval "LAST_DISPATCH_${pane_idx}=$NOW"
            dispatched_this_cycle=true
            sleep 2  # Let pane accept command before checking next pane
          else
            log "P${pane_idx} (${name}): IDLE (cooldown ${elapsed}/${DISPATCH_COOLDOWN}s)"
          fi
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

  # Health check every 5 cycles (system + Ollama brain)
  if [[ $((CYCLE % 5)) -eq 0 ]]; then
    health_check || true
    # Ollama brain health — auto-recover if down
    # DISABLED: CC CLI workers use DashScope API (cloud), not local Ollama
    # Ollama auto-recover was loading 31GB Qwen model on every health check cycle
    # causing OOM kills on task-watcher. Local Ollama only used by CTO brain_think.py
    # which handles its own model loading with keep_alive=5m
    # if ! ollama_health_check; then
    #   log "HEALTH: Ollama brain unhealthy — triggering auto-recovery"
    #   ollama_auto_recover || true
    # fi
    # Reset pane respawn counters every 5 cycles (allow retry)
    PANE_RESPAWN_COUNT[1]=0; PANE_RESPAWN_COUNT[2]=0; PANE_RESPAWN_COUNT[3]=0
  fi

  # Orphan node cleanup every 3 cycles (prevents RAM overflow)
  if [[ $((CYCLE % 3)) -eq 0 ]]; then
    cleanup_orphan_nodes || true
  fi

  # Re-scan every 20 cycles to update context
  if [[ $((CYCLE % 20)) -eq 0 ]]; then
    phase_scan || true
  fi

  CRASH_COUNT=0  # Reset on successful cycle
  } || {
    CRASH_COUNT=$((CRASH_COUNT + 1))
    log "CYCLE $CYCLE CRASHED (attempt ${CRASH_COUNT}) — recovering"
    if [[ $CRASH_COUNT -ge 10 ]]; then
      log "FATAL: 10 consecutive crashes — daemon giving up"
      exit 1
    fi
  }

  sleep "$POLL_INTERVAL"
done
