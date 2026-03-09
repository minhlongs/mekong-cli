#!/bin/bash
# Infinite loop for M1 cooling + CC CLI ZERO-TO-SHIP pipeline injection
# RULE: Only inject if pane is TRULY idle (no queued commands, no active tasks)
# PIPELINE: SCOUT → FIX → TEST → REVIEW → SHIP (5 phases per project)
echo "🧊 M1 FACTORY LOOP STARTED — $(date)"

# Mapping pane index → project name (khớp với config.js PROJECTS)
PANE1_PROJECT="algo-trader"
PANE2_PROJECT="sophia-ai-factory"
PANE3_PROJECT="well"

# Đường dẫn tới openclaw-worker cho Node.js pipeline calls
OPENCLAW_LIB="/Users/macbookprom1/mekong-cli/apps/openclaw-worker/lib"

# Lấy command phase tiếp theo cho một project
get_next_phase_cmd() {
  local project="$1"
  node -e "
    try {
      const sp = require('${OPENCLAW_LIB}/ship-pipeline');
      const cmd = sp.getNextPhaseCommand('${project}');
      console.log(cmd || 'DONE');
    } catch(e) {
      console.log('DONE');
    }
  " 2>/dev/null
}

# Đánh dấu phase hiện tại hoàn thành (PASS) và advance
advance_phase() {
  local project="$1"
  node -e "
    try {
      const sp = require('${OPENCLAW_LIB}/ship-pipeline');
      sp.advancePhase('${project}', 'PASS');
    } catch(e) {}
  " 2>/dev/null
}

# Kiểm tra pipeline đã hoàn thành chưa
is_ship_complete() {
  local project="$1"
  node -e "
    try {
      const sp = require('${OPENCLAW_LIB}/ship-pipeline');
      console.log(sp.isShipComplete('${project}') ? 'YES' : 'NO');
    } catch(e) {
      console.log('NO');
    }
  " 2>/dev/null
}

# Sinh handover docs khi pipeline hoàn thành
generate_handover() {
  local project="$1"
  local project_dir="$2"
  node -e "
    try {
      const gen = require('${OPENCLAW_LIB}/handover-report-generator');
      gen.generateHandoverDocs('${project_dir}', undefined, []);
      console.log('HANDOVER_DONE');
    } catch(e) {
      console.log('HANDOVER_ERR: ' + e.message);
    }
  " 2>/dev/null
}

while true; do
  LOAD=$(sysctl -n vm.loadavg | awk '{print $2}' | tr -d '{')
  LOAD_INT=${LOAD%.*}

  if [ "$LOAD_INT" -gt 30 ]; then
    echo "🔥 [$(date +%T)] OVERHEAT Load=$LOAD — pausing 60s"
    sleep 60
  elif [ "$LOAD_INT" -gt 15 ]; then
    echo "🟡 [$(date +%T)] WARM Load=$LOAD — pausing 30s"
    sleep 30
  else
    echo "🧊 [$(date +%T)] COOL Load=$LOAD — Checking panes..."

    for i in 1 2 3; do
      DEAD=$(tmux display-message -t "tom_hum:0.${i}" -p "#{pane_dead}" 2>/dev/null)
      if [ "$DEAD" = "1" ]; then
        # Respawn dead pane
        case $i in
          1) DIR="/Users/macbookprom1/mekong-cli/apps/algo-trader" ;;
          2) DIR="/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory" ;;
          3) DIR="/Users/macbookprom1/mekong-cli/apps/well" ;;
        esac
        echo "💀 [P${i}] DEAD — respawning..."
        tmux respawn-pane -k -t "tom_hum:0.${i}" "bash -c 'cd $DIR && export CLAUDE_PROJECT_DIR=$DIR && unset CLAUDE_CONFIG_DIR && export NPM_CONFIG_WORKSPACES=false && export npm_config_workspaces=false && /Users/macbookprom1/.local/bin/claude --dangerously-skip-permissions'"
        continue
      fi

      # Capture last 5 lines
      OUT=$(tmux capture-pane -t "tom_hum:0.${i}" -p -S -5)

      # Check if CC CLI EXITED to shell (detect % prompt = crashed/exited)
      if echo "$OUT" | grep -qE "macbookprom1@.*%\s*$"; then
        echo "🔄 [P${i}] CC CLI EXITED — auto-resuming with --continue..."
        case $i in
          1) DIR="/Users/macbookprom1/mekong-cli/apps/algo-trader" ;;
          2) DIR="/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory" ;;
          3) DIR="/Users/macbookprom1/mekong-cli/apps/well" ;;
        esac
        tmux send-keys -t "tom_hum:0.${i}" "cd $DIR && export CLAUDE_PROJECT_DIR=$DIR && /Users/macbookprom1/.local/bin/claude --dangerously-skip-permissions --continue" Enter
        sleep 10
        continue
      fi

      # Check if actively working (has agents, bashes, local agent)
      if echo "$OUT" | grep -qE "bashes|agents|local agent|Bash\(|Read |Write\(|Edit\(|Hashing|Blanching|Creating|Hatching|Puttering|Blanching"; then
        echo "⚙️  [P${i}] WORKING — SKIP"
        continue
      fi

      # Check if truly idle at prompt (bypass + empty prompt ❯)
      if echo "$OUT" | grep -q "bypass permissions on"; then
        LAST_LINE=$(echo "$OUT" | grep "❯" | tail -1)
        if [ -z "$LAST_LINE" ] || echo "$LAST_LINE" | grep -q "^❯ *$"; then
          # Xác định project tương ứng với pane
          case $i in
            1) PROJECT="$PANE1_PROJECT"; DIR="/Users/macbookprom1/mekong-cli/apps/algo-trader" ;;
            2) PROJECT="$PANE2_PROJECT"; DIR="/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory" ;;
            3) PROJECT="$PANE3_PROJECT"; DIR="/Users/macbookprom1/mekong-cli/apps/well" ;;
          esac

          # Kiểm tra pipeline đã hoàn thành chưa
          COMPLETE=$(is_ship_complete "$PROJECT")
          if [ "$COMPLETE" = "YES" ]; then
            echo "🎉 [P${i}] SHIP COMPLETE for $PROJECT — generating handover docs..."
            HANDOVER_RESULT=$(generate_handover "$PROJECT" "$DIR")
            echo "📄 [P${i}] $HANDOVER_RESULT"
            # Reset pipeline để bắt đầu chu kỳ mới
            node -e "require('${OPENCLAW_LIB}/ship-pipeline').resetPipeline('${PROJECT}')" 2>/dev/null
            echo "🔄 [P${i}] Pipeline reset for $PROJECT — starting new cycle"
            continue
          fi

          # Lấy command phase tiếp theo
          NEXT_CMD=$(get_next_phase_cmd "$PROJECT")

          if [ "$NEXT_CMD" = "DONE" ] || [ -z "$NEXT_CMD" ]; then
            echo "✅ [P${i}] $PROJECT pipeline DONE — idle"
            continue
          fi

          # Inject phase command vào pane
          echo "🚀 [P${i}] INJECTING phase for $PROJECT: $NEXT_CMD"
          tmux send-keys -t "tom_hum:0.${i}" "$NEXT_CMD" Enter

          # Advance phase sau khi inject (optimistic — phase sẽ chạy)
          advance_phase "$PROJECT"
          sleep 5
        else
          echo "📝 [P${i}] Has pending input — submitting it..."
          tmux send-keys -t "tom_hum:0.${i}" Enter
          sleep 3
        fi
      fi
    done

    # Long sleep to prevent rapid re-checking
    echo "💤 [$(date +%T)] Sleeping 120s before next check..."
    sleep 120
  fi
done
