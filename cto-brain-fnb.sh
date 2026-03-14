#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO F&B v4 — NARROW PANE SAFE
#
# ROOT CAUSE FIX: panes are 44 chars wide.
# "esc to interrupt" needs 67+ chars → ALWAYS TRUNCATED.
# grep for "esc to interrupt" NEVER works in tiled layout.
#
# NEW APPROACH: detect BUSY from task content signals,
# not from status bar text that gets cut off.
# ═══════════════════════════════════════════════════════════

FNB_APP="/Users/mac/mekong-cli/apps/fnb-caffe-container"
T="/opt/homebrew/bin/tmux"
S="tom_hum"
W="fnb"
NP=4
LOG="/Users/mac/mekong-cli/.cto-reports/fnb/cto-fnb.log"

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
TL=${#TASKS[@]}
CYCLE=0
DIS=0

typeset -A LAST_DISPATCH
LAST_DISPATCH=([0]=0 [1]=0 [2]=0 [3]=0)
LOCK_SEC=45  # 45s — content-based detection handles overlap

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

is_worker_busy() {
    local p=$1
    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null | tail -5)

    # ANY of these patterns = DEFINITELY BUSY
    if echo "$raw" | grep -qE \
        "thinking|Unfurling|Precipitating|Stewing|Pondering|Whirlpooling|Crunching|Clauding"; then
        return 0  # busy
    fi
    if echo "$raw" | grep -qE \
        "queued messages|Press up to edit"; then
        return 0  # busy — tasks already stacked!
    fi
    if echo "$raw" | grep -qE \
        "◻|◼|pending|completed"; then
        return 0  # busy — task checklist visible
    fi
    if echo "$raw" | grep -qE \
        "Read.*file|Write\(|Bash\(|Searched|Created|Updated|ctrl\+o"; then
        return 0  # busy — CC CLI operations in progress
    fi
    if echo "$raw" | grep -qE \
        "approve edit|confirm|Enter to select|navigate.*Esc"; then
        return 0  # busy — prompt waiting
    fi
    if echo "$raw" | grep -qE \
        "esc to"; then
        return 0  # busy — partial match works in narrow panes
    fi

    return 1  # not busy
}

can_dispatch() {
    local p=$1
    local now=$(date +%s)

    # CHECK 1: lock timer
    local last=${LAST_DISPATCH[$p]:-0}
    local age=$((now - last))
    if (( age < LOCK_SEC )); then
        return 1
    fi

    # CHECK 2: worker must NOT be busy
    if is_worker_busy "$p"; then
        # Renew lock — worker still working
        LAST_DISPATCH[$p]=$now
        return 1
    fi

    # CHECK 3: must see bypass or shortcuts = CC CLI idle prompt
    local raw=$($T capture-pane -t "$S:$W.$p" -p -S -3 2>/dev/null)
    if echo "$raw" | grep -qE "bypass permissions|shortcuts"; then
        return 0  # TRULY IDLE
    fi

    return 1  # unknown = skip
}

# Auto-select checkboxes and confirms
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
        log "🎯 F$p: Auto-select"
    fi
    if echo "$raw" | grep -qE "Yes, clear context.*bypass|Yes, and bypass"; then
        $T send-keys -t "$S:$W.$p" "1" Enter
        log "🎯 F$p: Auto-confirm"
    fi
}

echo "╔══════════════════════════════════════════╗"
echo "║ 🧠 CTO F&B v4 — NARROW PANE SAFE       ║"
echo "║ Lock: ${LOCK_SEC}s | Busy: content-based ║"
echo "╚══════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        do_auto_select "$p"

        if can_dispatch "$p"; then
            local task="${TASKS[$((IDX % TL + 1))]}"
            log "✅ F$p → $(echo $task | head -c 55)..."
            $T send-keys -t "$S:$W.$p" "$task" Enter
            LAST_DISPATCH[$p]=$(date +%s)
            ((IDX++))
            ((DIS++))
        fi
    done

    echo "═══ 🧠 FNB-v4 $(date +%H:%M:%S) cy:$CYCLE dis:$DIS ═══"
    sleep 15
done
