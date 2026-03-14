#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO F&B FINAL — LOCK FILE BASED (NO PANE DETECTION)
#
# HOW IT WORKS:
#   1. Before dispatch: check /tmp/cto-lock-fnb-P
#   2. If lock < 3 min old → SKIP (worker definitely busy)
#   3. If lock >= 3 min old → check "queued messages" only
#   4. If queued → SKIP
#   5. Otherwise → DISPATCH + create new lock
#
# WHY: pane content detection ALWAYS fails in narrow panes.
#       Lock files CANNOT be truncated or misread.
# ═══════════════════════════════════════════════════════════

FNB_APP="/Users/mac/mekong-cli/apps/fnb-caffe-container"
T="/opt/homebrew/bin/tmux"; S="tom_hum"; W="fnb"; NP=4
LOG="/Users/mac/mekong-cli/.cto-reports/fnb/cto-fnb.log"
LOCK_DIR="/tmp"
LOCK_TTL=180  # 3 minutes minimum between dispatches

mkdir -p /Users/mac/mekong-cli/.cto-reports/fnb "$FNB_APP"

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
TL=${#TASKS[@]}; CYCLE=0; DIS=0

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

can_dispatch() {
    local p=$1
    local lock="$LOCK_DIR/cto-lock-fnb-$p"
    local now=$(date +%s)

    # Step 1: Check lock file
    if [ -f "$lock" ]; then
        local lock_time=$(cat "$lock" 2>/dev/null)
        local age=$((now - lock_time))
        if (( age < LOCK_TTL )); then
            log "  🔒 F$p: locked ($((LOCK_TTL - age))s left)"
            return 1
        fi
    fi

    # Step 2: Lock expired or doesn't exist — check for queued messages ONLY
    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null)
    if echo "$raw" | grep -qi "queued messages"; then
        # Renew lock — worker still processing queue
        echo "$now" > "$lock"
        log "  ❌ F$p: queued (lock renewed)"
        return 1
    fi

    return 0  # Safe to dispatch
}

# Auto-select checkboxes
do_auto_select() {
    local p=$1
    local raw=$($T capture-pane -t "$S:$W.$p" -p -S -15 2>/dev/null)
    if echo "$raw" | grep -qE "Enter to select|Tab.*navigate" && echo "$raw" | grep -qE "\[ \]"; then
        local n=$(echo "$raw" | grep -c "\[ \]")
        for ((j=0; j<n; j++)); do
            $T send-keys -t "$S:$W.$p" " "; sleep 0.3
            $T send-keys -t "$S:$W.$p" Down; sleep 0.3
        done
        $T send-keys -t "$S:$W.$p" Down; sleep 0.3
        $T send-keys -t "$S:$W.$p" Enter
        log "  🎯 F$p: Auto-select"
    fi
}

echo "╔══════════════════════════════════════════╗"
echo "║ 🧠 CTO F&B FINAL — LOCK FILE BASED     ║"
echo "║ Lock TTL: ${LOCK_TTL}s | Cycle: 15s     ║"
echo "╚══════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        do_auto_select "$p"

        if can_dispatch "$p"; then
            local task="${TASKS[$((IDX % TL + 1))]}"
            log "  ✅ F$p → 🚀 $(echo $task | head -c 55)..."
            $T send-keys -t "$S:$W.$p" "$task" Enter
            echo "$(date +%s)" > "$LOCK_DIR/cto-lock-fnb-$p"
            ((IDX++)); ((DIS++))
        fi
    done

    echo "═══ 🧠 FNB $(date +%H:%M:%S) cy:$CYCLE dis:$DIS ═══"
    sleep 15
done
