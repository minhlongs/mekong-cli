#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 👁 CTO SUPERVISOR — Giám sát CTO Brain theo đúng rules
# Rules: slash commands, đúng path, đọc context trước khi exit
# ═══════════════════════════════════════════════════════════

PROJECT_APP="/Users/mac/mekong-cli/apps/sadec-marketing-hub"
SESSION="tom_hum"
BRAIN_WINDOW="brain"
LOG="/tmp/cto-supervisor.log"
DISPATCH_LOG="/Users/mac/mekong-cli/.cto-reports/dispatch_log.txt"
REPORT_DIR="/Users/mac/mekong-cli/.cto-reports"
TMUX_BIN="/opt/homebrew/bin/tmux"
NUM_WORKERS=6

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

# ═══ RULE CHECK ═══
check_dispatch_rules() {
    local line="$1"
    local violations=()

    # Rule 1: Must use slash command (log format: "QUEUE P*: /command")
    if echo "$line" | grep -qE "QUEUE P[0-9]+:"; then
        if ! echo "$line" | grep -qE "QUEUE P[0-9]+:\s*/[a-z]"; then
            violations+=("❌ NO SLASH COMMAND: $(echo "$line" | head -c 100)")
        fi
    fi

    # Rule 2: Must point to correct path when referencing the project
    if echo "$line" | grep -q "sadec-marketing-hub"; then
        if ! echo "$line" | grep -q "$PROJECT_APP"; then
            violations+=("❌ WRONG PATH (not mekong-cli): $(echo "$line" | head -c 100)")
        fi
    fi

    for v in "${violations[@]}"; do
        log "VIOLATION: $v"
    done
    [[ ${#violations[@]} -eq 0 ]]
}

# ═══ CHECK CONTEXT READ ═══
last_brain_check=""
check_context_read() {
    local brain_out
    brain_out=$($TMUX_BIN capture-pane -t "$SESSION:$BRAIN_WINDOW" -p -S -20 2>/dev/null)

    # Brain should show "📖 P*: Reading" before "🚀"
    local dispatches=$(echo "$brain_out" | grep "🚀" | tail -3)
    local reads=$(echo "$brain_out" | grep "📖" | tail -3)

    if echo "$brain_out" | grep -q "🚀" && ! echo "$brain_out" | grep -q "📖"; then
        log "⚠️ CTO dispatched without reading context!"
    fi
}

# ═══ WATCHDOG ═══
check_brain_alive() {
    if ! $TMUX_BIN has-session -t "$SESSION:$BRAIN_WINDOW" 2>/dev/null; then
        log "💀 CTO Brain window dead! Restarting..."
        $TMUX_BIN new-window -t "$SESSION" -n "$BRAIN_WINDOW" \
            "zsh /Users/mac/mekong-cli/cto-brain.sh /Users/mac/mekong-cli 2>&1 | tee /tmp/cto-final.log"
        return 1
    fi

    local brain_out=$($TMUX_BIN capture-pane -t "$SESSION:$BRAIN_WINDOW" -p -S -5 2>/dev/null)
    local last_line=$(echo "$brain_out" | grep -v '^$' | tail -1)

    # Detect stuck brain (no cycle update in 60s)
    if ! echo "$brain_out" | grep -qE "cycle:|🚀|📖|📨|═══"; then
        log "⚠️ CTO Brain looks stuck. Last: $last_line"
    fi
}

# ═══ MONITOR DISPATCH LOG ═══
LAST_DISPATCH_CHECK=0
check_dispatch_log() {
    local recent
    recent=$(tail -5 "$DISPATCH_LOG" 2>/dev/null)
    if [ -z "$recent" ]; then return; fi

    while IFS= read -r line; do
        if [[ "$line" != "$last_brain_check" ]]; then
            check_dispatch_rules "$line"
            last_brain_check="$line"
        fi
    done <<< "$recent"
}

# ═══ REPORT ═══
report_status() {
    log "═══ SUPERVISOR REPORT ═══"
    log "CTO Brain: alive=$(tmux has-session -t "$SESSION:$BRAIN_WINDOW" 2>/dev/null && echo YES || echo NO)"
    local active=0
    for p in $(seq 0 $((NUM_WORKERS-1))); do
        STATUS=$($TMUX_BIN capture-pane -t "$SESSION:0.$p" -p 2>/dev/null | grep -c "esc to interrupt")
        [ "$STATUS" -gt 0 ] && ((active++))
    done
    log "Workers active: $active/$NUM_WORKERS"
    log "Last dispatch: $(tail -1 "$DISPATCH_LOG" 2>/dev/null | head -c 100)"
}

log "👁 CTO SUPERVISOR started — watching $NUM_WORKERS workers + CTO Brain"
log "Rules: slash commands ✓ | path=$PROJECT_APP ✓ | read context ✓"

TICK=0
while true; do
    check_brain_alive
    check_dispatch_log
    check_context_read

    # Report every 5 mins
    if (( TICK % 25 == 0 )); then
        report_status
    fi

    ((TICK++))
    sleep 12
done
