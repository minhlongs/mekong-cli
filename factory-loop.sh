#!/bin/bash
# FACTORY LOOP v12.0 — STATE-AWARE DISPATCH + RAAS SCAFFOLD
# Detects project state (empty/scaffolded/built/deployed) before dispatching.
# Empty projects get /raas-scaffold FIRST, not /marketing-content-engine.
# State machine: empty → scaffold → build features → deploy → operate
# Date: 2026-03-16 | agencyos.network architecture
set -euo pipefail

TMUX_SESSION="tom_hum"
PANES=(0 1)
PANE_PROJECTS=("sophia-proposal" "well")
PANE_DIRS=("apps/sophia-proposal" "apps/well")
PANE_NAMES=("Sophia AI Video Factory" "WellNexus Healthcare B2B")
SLEEP_INTERVAL=120

# CASCADE STATE FILES
PANE_STATE_DIR="/tmp/pane_state"
mkdir -p "$PANE_STATE_DIR"

echo "🏭 FACTORY v12.0 — STATE-AWARE DISPATCH — $(date) — PID: $$"
echo "👑 Detects project state → dispatches correct command for that state"
echo "🏛️ P0=${PANE_PROJECTS[0]}, P1=${PANE_PROJECTS[1]}"

# Save/load previous command output per pane (for A→B chaining)
save_pane_output() {
  local PANE=$1
  local OUTPUT=$2
  # Save last 20 meaningful lines as context for next command
  echo "$OUTPUT" | grep -v "^$" | grep -v "^─" | grep -v "bypass permissions" | grep -v "qwen" | tail -20 > "$PANE_STATE_DIR/pane_${PANE}_output"
}

get_prev_output() {
  local PANE=$1
  cat "$PANE_STATE_DIR/pane_${PANE}_output" 2>/dev/null || echo "(no previous output)"
}

# ═══════════════════════════════════════════════════════════════
# CASCADE LOGIC — Reads output, chains commands
# ═══════════════════════════════════════════════════════════════

# Cascade state per pane: tracks what needs to happen next
# Values: "needs_bootstrap" | "needs_portfolio" | "ready_operate" | "needs_fix"

get_pane_state() {
  local PANE=$1
  local STATE_FILE="$PANE_STATE_DIR/pane_${PANE}_state"
  cat "$STATE_FILE" 2>/dev/null || echo "ready_operate"
}

set_pane_state() {
  local PANE=$1
  local STATE=$2
  echo "$STATE" > "$PANE_STATE_DIR/pane_${PANE}_state"
}

# Analyze last 45 lines for cascade triggers
# Returns: "bootstrap" | "portfolio" | "fix" | "continue" | "error"
analyze_output() {
  local OUTPUT="$1"
  local OUTPUT_LOWER=$(echo "$OUTPUT" | tr '[:upper:]' '[:lower:]')

  # Priority 1: SUCCESS signals → project is ready, continue rotation
  # Check this FIRST so "Bootstrap complete" overrides old "empty" keywords
  if echo "$OUTPUT_LOWER" | grep -qE "✅|bootstrap complete|ready for|initialized|success|completed|saved|created|done|finished|launched|deployed|operational"; then
    echo "continue"
    return
  fi

  # Priority 2: Critical errors → needs fix
  if echo "$OUTPUT_LOWER" | grep -qE "error:|failed:|exception|traceback|crashed|fatal:"; then
    echo "fix"
    return
  fi

  # Priority 3: Not initialized → needs bootstrap (only if no success above)
  if echo "$OUTPUT_LOWER" | grep -qE "not initialized|does not exist|not configured|no studio found|missing portfolio|missing studio"; then
    echo "bootstrap"
    return
  fi

  # Default: continue rotation
  echo "continue"
}

# Get cascade command based on state and output analysis
get_cascade_command() {
  local PANE=$1
  local PROJECT=$2
  local DIR=$3
  local NAME=$4
  local OUTPUT="$5"

  local CURRENT_STATE=$(get_pane_state "$PANE")
  local ANALYSIS=$(analyze_output "$OUTPUT")

  # Log analysis to stderr (not captured in command output)
  echo "   📊 State='$CURRENT_STATE' Analysis='$ANALYSIS'" >&2

  # OVERRIDE: If analysis says fix/bootstrap, do it regardless of state
  if [ "$ANALYSIS" = "fix" ]; then
    set_pane_state "$PANE" "needs_fix"
    echo "/cook [CHỈ project: ${PROJECT}] [DIR: ${DIR}] Fix errors in $NAME — KHÔNG đụng project khác"
    return
  fi

  if [ "$ANALYSIS" = "bootstrap" ]; then
    set_pane_state "$PANE" "needs_bootstrap"
    echo "/studio-bootstrap [CHỈ project: ${PROJECT}] [DIR: ${DIR}] $NAME — KHÔNG đụng project khác"
    return
  fi

  # State machine: chain commands logically
  case "$CURRENT_STATE" in
    "needs_bootstrap")
      # Just set bootstrap, next iteration will check output
      set_pane_state "$PANE" "needs_portfolio"
      echo "/studio-bootstrap [CHỈ project: ${PROJECT}] [DIR: ${DIR}] $NAME — KHÔNG đụng project khác"
      ;;
    "needs_portfolio")
      # Check if bootstrap succeeded
      if echo "$OUTPUT" | grep -qE "success|completed|saved"; then
        set_pane_state "$PANE" "ready_operate"
        echo "/portfolio-create [CHỈ project: ${PROJECT}] [DIR: ${DIR}] $NAME — KHÔNG đụng project khác"
      else
        # Bootstrap failed, retry
        echo "/studio-bootstrap [CHỈ project: ${PROJECT}] [DIR: ${DIR}] $NAME — KHÔNG đụng project khác"
      fi
      ;;
    "ready_operate")
      # Normal operation mode — use rotation
      local ROTATION_CMD=$(get_next_command "$PANE" "$PROJECT" "$DIR" "$NAME")
      echo "$ROTATION_CMD"
      ;;
    *)
      # Unknown state → bootstrap first
      set_pane_state "$PANE" "needs_bootstrap"
      echo "/studio-bootstrap $NAME — Thư mục: ${DIR}"
      ;;
  esac
}

# ═══════════════════════════════════════════════════════════════
# PROJECT STATE DETECTION — Checks actual files on disk
# States: empty → scaffolded → built → deployed → operating
# ═══════════════════════════════════════════════════════════════

detect_project_state() {
  local DIR=$1
  local FULL_DIR="$HOME/mekong-cli/${DIR}"

  # Directory doesn't exist at all
  if [ ! -d "$FULL_DIR" ]; then
    echo "empty"
    return
  fi

  # No src/ or app/ = empty project (only config files)
  if [ ! -d "${FULL_DIR}/src" ] && [ ! -d "${FULL_DIR}/app" ]; then
    echo "empty"
    return
  fi

  # Has src but no node_modules = needs install
  if [ ! -d "${FULL_DIR}/node_modules" ]; then
    echo "needs_install"
    return
  fi

  # Has build output = deployed/built
  if [ -d "${FULL_DIR}/out" ] || [ -d "${FULL_DIR}/.next" ] || [ -d "${FULL_DIR}/dist" ]; then
    echo "deployed"
    return
  fi

  # Has src + node_modules but no build = scaffolded, needs features
  echo "scaffolded"
}

# ═══════════════════════════════════════════════════════════════
# OPERATE COMMANDS — Only used when project is deployed/live
# ═══════════════════════════════════════════════════════════════

# Feature build commands for scaffolded projects
FEATURE_CMDS_TEMPLATE=(
  "Build landing page with hero section, features grid, and pricing tiers"
  "Build user dashboard with authentication and stats cards"
  "Build billing integration with Polar.sh webhooks and credit system"
  "Build API routes for core product functionality"
)

# Operate commands for deployed projects (business/studio layer)
OPERATE_CMDS_TEMPLATE=(
  "/studio-operate-daily"
  "/marketing-content-engine"
  "/sales-pipeline-build"
  "/portfolio-status"
)

# Code generation commands for deployed projects wanting new algorithms
ALGO_CMDS=(
  "/cook Implement a scoring algorithm. Write TypeScript to src/algorithms/scoring-engine.ts with: interface, scoring logic, unit tests, and export."
  "/cook Implement a pricing engine. Write TypeScript to src/algorithms/pricing-engine.ts with: tiered pricing, discount calc, bundle pricing."
  "/cook Implement a recommendation algorithm. Write TypeScript to src/algorithms/recommendation-engine.ts with: collaborative filtering, content matching."
  "/cook Build a revenue forecasting model. Write TypeScript to src/algorithms/revenue-forecast.ts with: MRR projection, cohort analysis."
  "/cook Build a unit economics calculator. Write TypeScript to src/algorithms/unit-economics.ts with: LTV, CAC payback, gross margin."
  "/cook Build an A/B test engine. Write TypeScript to src/algorithms/ab-test-engine.ts with: significance calculator, sample size estimator."
  "/cook Build a feature prioritizer (RICE/ICE). Write TypeScript to src/algorithms/feature-prioritizer.ts with: multi-framework scorer."
)

get_next_command() {
  local PANE=$1
  local PROJECT=$2
  local DIR=$3
  local NAME=$4

  # Detect actual project state from filesystem
  local PROJECT_STATE=$(detect_project_state "$DIR")
  echo "   🔍 Project state: $PROJECT_STATE" >&2

  case "$PROJECT_STATE" in
    "empty")
      # Project has no code — scaffold first!
      echo "/raas-scaffold ${PROJECT} --type saas --stack next+cf [CHỈ project: ${PROJECT}] [DIR: ${DIR}]"
      ;;
    "needs_install")
      # Has code but no deps — install and build
      echo "/cook Install dependencies and build: cd ${DIR} && pnpm install && pnpm build [CHỈ project: ${PROJECT}] [DIR: ${DIR}]"
      ;;
    "scaffolded")
      # Has code + deps but no build — build features one by one
      local FEATURE_IDX_FILE="/tmp/feature_idx_${PROJECT}"
      local FEATURE_IDX=$(cat "$FEATURE_IDX_FILE" 2>/dev/null || echo "0")
      local TOTAL=${#FEATURE_CMDS_TEMPLATE[@]}

      if [ "$FEATURE_IDX" -lt "$TOTAL" ]; then
        local FEATURE="${FEATURE_CMDS_TEMPLATE[$FEATURE_IDX]}"
        echo $((FEATURE_IDX + 1)) > "$FEATURE_IDX_FILE"
        echo "/cook ${FEATURE} for ${NAME} [CHỈ project: ${PROJECT}] [DIR: ${DIR}]"
      else
        # All features built — try to build/deploy
        echo "/cook Run pnpm build and verify no errors [CHỈ project: ${PROJECT}] [DIR: ${DIR}]"
      fi
      ;;
    "deployed")
      # Project is live — NOW use business/studio/algo commands
      local AI_CMD=""
      local STATE_FILE="$PANE_STATE_DIR/pane_${PANE}_output"

      # Try BytePlus brain first
      AI_CMD=$(timeout 10 node ~/mekong-cli/byteplus-cto-brain.js "$PROJECT" "$STATE_FILE" 2>/dev/null || true)

      # Fallback: alternate between operate cmds and algo cmds
      if [ -z "$AI_CMD" ] || [ ${#AI_CMD} -lt 3 ]; then
        local IDX_FILE="/tmp/cto_cmd_idx_P${PANE}"
        local IDX=$(cat "$IDX_FILE" 2>/dev/null || echo "0")

        # Even iterations: operate commands, odd: algo commands
        if [ $((IDX % 2)) -eq 0 ]; then
          local OP_IDX=$(( (IDX / 2) % ${#OPERATE_CMDS_TEMPLATE[@]} ))
          AI_CMD="${OPERATE_CMDS_TEMPLATE[$OP_IDX]} ${NAME}"
        else
          local ALGO_IDX=$(( (IDX / 2) % ${#ALGO_CMDS[@]} ))
          AI_CMD="${ALGO_CMDS[$ALGO_IDX]}"
        fi
        echo $(( (IDX + 1) )) > "$IDX_FILE"
      fi

      echo "${AI_CMD} [CHỈ project: ${PROJECT}] [DIR: ${DIR}] — KHÔNG đụng project khác."
      ;;
  esac
}

while true; do
  LOAD=$(sysctl -n vm.loadavg | awk '{print $2}')
  RAM=$(vm_stat | awk '/free/ {print $3}' | tr -d '.')
  echo "🧊 [$(date +%T)] Load=$LOAD RAM_free=$RAM"

  pkill -f "node.*jest" 2>/dev/null || true
  pkill -f "node.*vitest" 2>/dev/null || true
  pkill -f "tsserver.js" 2>/dev/null || true

  for i in "${!PANES[@]}"; do
    PANE=${PANES[$i]}
    PROJECT=${PANE_PROJECTS[$i]}
    DIR=${PANE_DIRS[$i]}
    NAME=${PANE_NAMES[$i]}

    PANE_OUTPUT=$(tmux capture-pane -t "$TMUX_SESSION:0.$PANE" -p 2>/dev/null || echo "")
    LAST_45=$(echo "$PANE_OUTPUT" | tail -n 45)
    LAST_5=$(echo "$PANE_OUTPUT" | tail -n 5)

    # CRASHED
    if echo "$LAST_5" | grep -qE "bash-5|% $"; then
      echo "☠️ [P$PANE] CRASHED — Restarting CC CLI..."
      tmux send-keys -t "$TMUX_SESSION:0.$PANE" -l "cd ~/mekong-cli && claude --dangerously-skip-permissions"
      sleep 0.5
      tmux send-keys -t "$TMUX_SESSION:0.$PANE" Enter
      continue
    fi

    # QUEUED
    if echo "$LAST_5" | grep -qE "Press up to edit queued"; then
      echo "📬 [P$PANE] QUEUED — Clearing..."
      tmux send-keys -t "$TMUX_SESSION:0.$PANE" Escape
      sleep 1
      continue
    fi

    # WORKING — check LAST 5 lines ONLY (active animation near prompt)
    # Old output in scroll buffer must NOT trigger this
    if echo "$LAST_5" | grep -qE "Bash\(|Read [0-9]|Write\(|Edit\(|Running|thinking|Hashing|Blanching|Creating|Hatching|Puttering|Generating|Tempering|Crunching|Bloviating|Actioning|Manifesting|Stewing|Billowing|Cogitated|Dilly-dallying|Infusing|Churned|Sautéed|Composting|Baked|Warping|Newspapering|Prestidigitating|Channeling|Metamorphosing|Propagating|Scampering|Brewing|Frosting|Moonwalking|Concocting|Sautéing|Orbiting|Compacting|Ebbing|Pondering|Crystallizing|Precipitating|Mulling|Searching for|thought for|Harmonizing"; then
      echo "⚙️ [P$PANE] WORKING on $PROJECT — SKIP"
      continue
    fi

    # JUST FINISHED — check LAST 5 lines only (same as WORKING)
    if echo "$LAST_5" | grep -qE "✅ Done|✔|Sautéed for|Brewed for|Baked for|Cogitated for|Crunched for"; then
      # Only if pane is at prompt (idle after finishing)
      if echo "$LAST_5" | grep -qE "❯"; then
        : # Not truly just-finished, it's idle — fall through to dispatch
      else
        echo "🏁 [P$PANE] JUST FINISHED — cooldown"
        continue
      fi
    fi

    # TRULY IDLE → dispatch VC-level command with cascade logic
    if echo "$LAST_5" | grep -qE "❯|bypass permissions"; then
      COOLDOWN_FILE="/tmp/cto_cooldown_P${PANE}"
      NOW=$(date +%s)
      LAST_DISPATCH=$(cat "$COOLDOWN_FILE" 2>/dev/null || echo "0")
      ELAPSED=$((NOW - LAST_DISPATCH))

      if [ "$ELAPSED" -lt 180 ]; then
        echo "⏳ [P$PANE] COOLDOWN (${ELAPSED}s < 180s) — skip"
        continue
      fi

      # Save current output for chaining (A→B) — CC CLI reads from file
      save_pane_output "$PANE" "$LAST_45"

      # CASCADE LOGIC: analyze + get command
      CASCADE_CMD=$(get_cascade_command "$PANE" "$PROJECT" "$DIR" "$NAME" "$LAST_45" 2>/dev/null)

      # Save context file for CC CLI to reference
      echo "$LAST_45" | grep -v "^$" | grep -v "^─" | grep -v "bypass" | grep -v "qwen" | tail -15 > "/tmp/cto_context_P${PANE}.txt"

      # Determine layer
      LAYER="?"
      case "$CASCADE_CMD" in
        /raas*) LAYER="🏗️ Scaffold" ;;
        /studio*|/portfolio*) LAYER="🏯 Studio" ;;
        /founder*|/venture*) LAYER="👑 Founder" ;;
        /business*|/sales*|/marketing*) LAYER="💼 Business" ;;
        /plan*|/design*) LAYER="🎯 Product" ;;
        /cook*) LAYER="⚙️ Engineering" ;;
        *) LAYER="🏯 Studio" ;;
      esac

      echo "$LAYER [P$PANE] CASCADE DISPATCH for $PROJECT:"
      echo "   📌 $CASCADE_CMD"

      # SEND CLEAN /command — NO inline context (was garbling)
      # CC CLI gets /command as proper slash command
      tmux send-keys -t "$TMUX_SESSION:0.$PANE" -l "$CASCADE_CMD"
      sleep 0.5
      tmux send-keys -t "$TMUX_SESSION:0.$PANE" Enter
      echo "$NOW" > "$COOLDOWN_FILE"
      continue
    fi

    echo "❓ [P$PANE] UNKNOWN STATE"
  done

  echo "💤 [$(date +%T)] Sleeping ${SLEEP_INTERVAL}s..."
  sleep $SLEEP_INTERVAL
done
