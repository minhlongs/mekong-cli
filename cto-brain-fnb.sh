#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO F&B v2 — F&B Caffe Container Project Manager
# - Đọc 45 dòng context trước khi dispatch
# - Skip nếu worker đang busy hoặc đã có queued messages
# - Chỉ dispatch khi worker thật sự IDLE
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

# Cooldown per worker (prevent stacking)
typeset -A LAST_DISPATCH
for ((i=0; i<NUM_PANES; i++)); do LAST_DISPATCH[$i]=0; done
COOLDOWN=30  # seconds between dispatches to same worker

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$REPORT_DIR/cto-fnb.log"; }

# ═══ Read 45 lines of context from pane ═══
read_context() {
    local p="$1"
    $TMUX_BIN capture-pane -t "$SESSION:$FNB_WIN.$p" -p -S -45 2>/dev/null
}

# ═══ Check if worker is truly IDLE (not busy, no queued tasks) ═══
is_truly_idle() {
    local p="$1"
    local ctx=$(read_context "$p")
    
    # ❌ BUSY: "esc to interrupt" = actively processing
    if echo "$ctx" | grep -q "esc to interrupt"; then
        return 1
    fi
    
    # ❌ BUSY: thinking/running
    if echo "$ctx" | grep -qE "thinking|Precipitating|Clauding|Crunching|Forging|Running"; then
        return 1
    fi
    
    # ❌ BUSY: has queued messages (Press up to edit queued messages)
    if echo "$ctx" | grep -q "queued messages"; then
        return 1
    fi
    
    # ❌ COOLDOWN: dispatched too recently
    local now=$(date +%s)
    local last=${LAST_DISPATCH[$p]:-0}
    if (( now - last < COOLDOWN )); then
        return 1
    fi
    
    # ✅ IDLE: bypass prompt visible without esc to interrupt
    if echo "$ctx" | grep -qE "bypass permissions on|❯ |shortcuts"; then
        return 0
    fi
    
    return 1  # unknown = assume busy
}

# ═══ Auto-select prompts (checkboxes) ═══
auto_select() {
    local p="$1"
    local ctx=$(read_context "$p")
    
    if echo "$ctx" | grep -qE "Enter to select|Tab.*navigate.*Esc" && echo "$ctx" | grep -qE "\[ \]"; then
        if ! echo "$ctx" | grep -qE "thinking|Precipitating|Clauding"; then
            log "🎯 F$p: Auto-select features"
            local n=$(echo "$ctx" | grep -c "\[ \]")
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
echo "║  🧠 CTO F&B v2 — Context-Aware Dispatch      ║"
echo "║  Workers: 4P (window fnb)                     ║"
echo "║  Project: $FNB_APP                            ║"
echo "║  Cooldown: ${COOLDOWN}s per worker            ║"
echo "╚═══════════════════════════════════════════════╝"

while true; do
    ((CYCLE++))
    
    for ((p=0; p<NUM_PANES; p++)); do
        # Step 1: Handle stuck prompts
        auto_select "$p"
        
        # Step 2: Read context (45 lines)
        log "📖 F$p: Reading 45 lines of context..."
        local ctx=$(read_context "$p")
        local files=$(echo "$ctx" | grep -oE "[a-zA-Z0-9_-]+\.(html|js|css|ts|json)" | sort -u | head -5 | tr '\n' ', ')
        local last_line=$(echo "$ctx" | grep -v '^$' | tail -1 | head -c 80)
        local errors=$(echo "$ctx" | grep -iE "error|fail|❌" | tail -1 | head -c 60)
        log "  📄 Files: $files"
        log "  📝 Last: $last_line"
        [ -n "$errors" ] && log "  ⚠️ Errors: $errors"
        
        # Step 3: Only dispatch if truly idle
        if is_truly_idle "$p"; then
            local task="${TASKS[$((IDX % TOTAL + 1))]}"
            log "🚀 F$p ← $(echo $task | head -c 70)..."
            $TMUX_BIN send-keys -t "$SESSION:$FNB_WIN.$p" "$task" Enter
            LAST_DISPATCH[$p]=$(date +%s)
            ((IDX++))
            ((TOTAL_DISPATCHED++))
        else
            log "⏳ F$p busy — skipping"
        fi
    done
    
    echo "═══ 🧠 CTO-FNB $(date +%H:%M:%S) ═══ cycle:$CYCLE dispatched:$TOTAL_DISPATCHED ═══"
    sleep 12
done
