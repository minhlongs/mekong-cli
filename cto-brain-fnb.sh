#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO F&B — F&B Caffe Container Project Manager
# Window: fnb (4 panes: F0-F3)
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

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$REPORT_DIR/cto-fnb.log"; }

# ═══ Is pane idle? ═══
is_idle() {
    local p="$1"
    local out=$($TMUX_BIN capture-pane -t "$SESSION:$FNB_WIN.$p" -p -S -5 2>/dev/null)
    # Busy if "esc to interrupt" visible
    if echo "$out" | grep -q "esc to interrupt"; then return 1; fi
    # Idle if prompt visible (bypass with any suffix)
    if echo "$out" | grep -qE "bypass permissions on|❯ |shortcuts"; then return 0; fi
    return 1
}

# ═══ Auto-select prompts ═══
auto_select() {
    local p="$1"
    local out=$($TMUX_BIN capture-pane -t "$SESSION:$FNB_WIN.$p" -p -S -15 2>/dev/null)
    
    if echo "$out" | grep -qE "Enter to select|Tab.*navigate.*Esc" && echo "$out" | grep -qE "\[ \]"; then
        if ! echo "$out" | grep -qE "thinking|Precipitating|Clauding"; then
            log "🎯 F$p: Auto-select features"
            local n=$(echo "$out" | grep -c "\[ \]")
            for ((j=0; j<n; j++)); do
                $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" " "; sleep 0.3
                $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Down; sleep 0.3
            done
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Down; sleep 0.3
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" Enter
        fi
    fi
}

# ═══ MAIN ═══
CYCLE=0
echo "╔═══════════════════════════════════════════════╗"
echo "║  🧠 CTO F&B — Caffe Container Manager        ║"
echo "║  Workers: 4P (window fnb)                     ║"
echo "║  Project: $FNB_APP  ║"
echo "╚═══════════════════════════════════════════════╝"

while true; do
    ((CYCLE++))
    
    for ((p=0; p<NUM_PANES; p++)); do
        auto_select "$p"
        
        if is_idle "$p"; then
            local task="${TASKS[$((IDX % TOTAL + 1))]}"
            log "🚀 F$p ← $(echo $task | head -c 70)..."
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" "$task" Enter
            ((IDX++))
        fi
    done
    
    echo "═══ 🧠 CTO-FNB $(date +%H:%M:%S) ═══ cycle:$CYCLE dispatched:$IDX ═══"
    sleep 12
done
