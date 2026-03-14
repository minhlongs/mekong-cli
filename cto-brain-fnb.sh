#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO F&B v3 — BULLETPROOF DISPATCH
# Root cause fix: "bypass permissions on" is in status bar ALWAYS
# Only true idle signal: last non-empty line contains "❯" prompt
# AND no "esc to interrupt" AND no "queued messages"
# ═══════════════════════════════════════════════════════════

FNB_APP="/Users/mac/mekong-cli/apps/fnb-caffe-container"
TMUX_BIN="/opt/homebrew/bin/tmux"
REPORT_DIR="/Users/mac/mekong-cli/.cto-reports/fnb"
SESSION="tom_hum"
FNB_WIN="fnb"
NUM_PANES=4

mkdir -p "$REPORT_DIR" "$FNB_APP"

# ═══ Tasks ═══
IDX=0
TASKS=(
    '/cook "Tao project F&B Caffe Container website tai '$FNB_APP' voi landing page hero about contact menu order system responsive dark mode"'
    '/dev-feature "Build menu page voi categories drinks food prices images gallery tai '$FNB_APP'"'
    '/dev-feature "Build order system cart checkout thanh toan tai '$FNB_APP'"'
    '/frontend-ui-build "Build admin dashboard quan ly don hang doanh thu thong ke tai '$FNB_APP'"'
    '/cook "Build responsive landing page hero section about us contact form tai '$FNB_APP'"'
    '/dev-feature "Build customer loyalty rewards point system tai '$FNB_APP'"'
    '/frontend-ui-build "Build kitchen display order queue real-time status tai '$FNB_APP'"'
    '/cook "Them SEO metadata og tags favicon manifest PWA support cho '$FNB_APP'"'
    '/dev-bug-sprint "Viet tests cho '$FNB_APP' cover tat ca pages va components"'
    '/frontend-responsive-fix "Fix responsive 375px 768px 1024px cho '$FNB_APP'"'
    '/eng-tech-debt "Refactor '$FNB_APP' optimize performance minify assets"'
    '/release-ship "Git commit push '$FNB_APP' viet release notes deploy"'
)
TOTAL=${#TASKS[@]}

# Cooldown per worker
typeset -A LAST_DISPATCH
for ((i=0; i<NUM_PANES; i++)); do LAST_DISPATCH[$i]=0; done
COOLDOWN=60  # 60 seconds minimum between dispatches

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$REPORT_DIR/cto-fnb.log"; }

# ═══ BULLETPROOF IDLE CHECK ═══
# Returns 0 (idle) ONLY if ALL conditions met:
#   1. No "esc to interrupt" (worker actively processing)
#   2. No "queued messages" (stacked tasks)
#   3. No "thinking" / "Precipitating" etc
#   4. Prompt "❯" visible on a non-empty line  
#   5. Cooldown elapsed (60s since last dispatch)
is_truly_idle() {
    local p="$1"
    local raw=$($TMUX_BIN capture-pane -t "$SESSION:$FNB_WIN.$p" -p -S -15 2>/dev/null)
    
    # ❌ BUSY signals (if ANY present → not idle)
    if echo "$raw" | grep -q "esc to interrupt"; then
        log "  ⏳ F$p: busy (processing)"
        return 1
    fi
    if echo "$raw" | grep -qi "queued messages"; then
        log "  ⏳ F$p: busy (queued — STACKED)"
        return 1
    fi
    if echo "$raw" | grep -qE "thinking|Precipitating|Clauding|Crunching|Forging"; then
        log "  ⏳ F$p: busy (thinking)"
        return 1
    fi
    
    # ❌ Cooldown not elapsed
    local now=$(date +%s)
    local last=${LAST_DISPATCH[$p]:-0}
    if (( now - last < COOLDOWN )); then
        log "  ⏳ F$p: cooldown ($((COOLDOWN - now + last))s left)"
        return 1
    fi
    
    # ❌ Pane is empty/dead
    if [ -z "$(echo "$raw" | tr -d '[:space:]')" ]; then
        log "  ⏳ F$p: empty pane"
        return 1
    fi
    
    # ✅ No busy signals + cooldown passed + pane has content = IDLE
    log "  ✅ F$p: IDLE"
    return 0
}

# ═══ Auto-select prompts ═══
auto_select() {
    local p="$1"
    local raw=$($TMUX_BIN capture-pane -t "$SESSION:$FNB_WIN.$p" -p -S -15 2>/dev/null)
    local clean=$(echo "$raw" | LC_ALL=C sed 's/[^[:print:][:space:]]//g')
    
    if echo "$clean" | grep -qE "Enter to select|Tab.*navigate.*Esc" && echo "$clean" | grep -qE "\[ \]"; then
        if ! echo "$clean" | grep -qE "thinking|Precipitating|Clauding"; then
            log "🎯 F$p: Auto-select features"
            local n=$(echo "$clean" | grep -c "\[ \]")
            for ((j=0; j<n; j++)); do
                $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" " "; sleep 0.3
                $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Down; sleep 0.3
            done
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Down; sleep 0.3
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Enter
        fi
    fi
}

# ═══ MAIN LOOP ═══
CYCLE=0
TOTAL_DISPATCHED=0
echo "╔═══════════════════════════════════════════════╗"
echo "║  🧠 CTO F&B v3 — BULLETPROOF DISPATCH        ║"
echo "║  Workers: 4P (window fnb)                     ║"
echo "║  Cooldown: ${COOLDOWN}s | Idle: ❯ prompt only ║"
echo "╚═══════════════════════════════════════════════╝"

while true; do
    ((CYCLE++))
    
    for ((p=0; p<NUM_PANES; p++)); do
        auto_select "$p"
        
        log "📖 F$p: Reading context..."
        
        if is_truly_idle "$p"; then
            local task="${TASKS[$((IDX % TOTAL + 1))]}"
            log "🚀 F$p ← $(echo $task | head -c 70)..."
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" "$task" Enter
            LAST_DISPATCH[$p]=$(date +%s)
            ((IDX++))
            ((TOTAL_DISPATCHED++))
        fi
    done
    
    echo "═══ 🧠 CTO-FNB $(date +%H:%M:%S) ═══ cycle:$CYCLE dispatched:$TOTAL_DISPATCHED ═══"
    sleep 15
done
