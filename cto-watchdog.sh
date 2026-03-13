#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🛡️ CTO WATCHDOG — Keeps CTO Brain alive forever
# Restarts CTO Brain if it crashes, ensures tmux session exists
# Usage: bash cto-watchdog.sh [project_path]
# ═══════════════════════════════════════════════════════════

PROJECT="${1:-/Users/mac/.gemini/antigravity/scratch/sadec-marketing-hub}"
FACTORY="$HOME/mekong-cli/tom-hum-factory.sh"
CTO_BRAIN="$HOME/mekong-cli/cto-brain.sh"
SESSION="tom_hum"
CHECK_INTERVAL=30  # seconds between health checks
MAX_RESTARTS=10
RESTART_COUNT=0

eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

echo "🛡️ CTO WATCHDOG — Monitoring CTO Brain + Factory"
echo "📁 $PROJECT"
echo "⏱  Check every ${CHECK_INTERVAL}s"
echo ""

while true; do
    # 1. Check tmux session exists
    if ! /opt/homebrew/bin/tmux has-session -t $SESSION 2>/dev/null; then
        echo "[$(date +%H:%M:%S)] ❌ tmux session '$SESSION' DEAD → restarting factory"
        bash "$FACTORY" "$PROJECT" 4 &
        FACTORY_PID=$!
        sleep 15
        echo "[$(date +%H:%M:%S)] ✅ Factory restarted"
        RESTART_COUNT=$((RESTART_COUNT + 1))
    fi

    # 2. Check CTO Brain process alive
    if ! pgrep -f "cto-brain.sh" >/dev/null 2>&1; then
        if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
            echo "[$(date +%H:%M:%S)] 🚫 Max restarts ($MAX_RESTARTS) reached. Watchdog stopping."
            exit 1
        fi
        
        echo "[$(date +%H:%M:%S)] ❌ CTO Brain DEAD → restarting"
        nohup bash "$CTO_BRAIN" "$PROJECT" > /tmp/cto-brain.log 2>&1 &
        CTO_PID=$!
        RESTART_COUNT=$((RESTART_COUNT + 1))
        echo "[$(date +%H:%M:%S)] ✅ CTO Brain restarted (PID: $CTO_PID, restart #$RESTART_COUNT)"
        sleep 5
    fi

    # 3. Check workers have CCC running
    local dead_workers=0
    for p in 0 1 2 3; do
        out=$(/opt/homebrew/bin/tmux capture-pane -t $SESSION:0.$p -p -S -3 2>/dev/null)
        if [ -z "$(echo "$out" | tr -d '[:space:]')" ]; then
            dead_workers=$((dead_workers + 1))
        fi
    done
    
    if [ $dead_workers -eq 4 ]; then
        echo "[$(date +%H:%M:%S)] ⚠️ All 4 workers DEAD → factory restart"
        /opt/homebrew/bin/tmux kill-session -t $SESSION 2>/dev/null
        sleep 2
        bash "$FACTORY" "$PROJECT" 4 &
        sleep 15
        RESTART_COUNT=$((RESTART_COUNT + 1))
    fi

    # 4. Status
    local alive_workers=0
    for p in 0 1 2 3; do
        out=$(/opt/homebrew/bin/tmux capture-pane -t $SESSION:0.$p -p -S -2 2>/dev/null | tail -2)
        if echo "$out" | grep -q "esc to interrupt\|shortcuts\|thinking\|Perusing"; then
            alive_workers=$((alive_workers + 1))
        fi
    done
    
    printf "\r[%s] 🛡️ Workers: %d/4 alive | CTO: %s | Restarts: %d/%d    " \
        "$(date +%H:%M:%S)" $alive_workers \
        "$(pgrep -f cto-brain.sh >/dev/null && echo '✅' || echo '❌')" \
        $RESTART_COUNT $MAX_RESTARTS

    sleep $CHECK_INTERVAL
done
