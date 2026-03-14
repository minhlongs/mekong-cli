#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO SADEC v5 — SIMPLE & RELIABLE
# Based on CTO-FNB v4 architecture (proven stable)
# ═══════════════════════════════════════════════════════════

SADEC_APP="/Users/mac/mekong-cli/apps/sadec-marketing-hub"
T="/opt/homebrew/bin/tmux"
S="tom_hum"
W="0"
NP=6
LOG="/Users/mac/mekong-cli/.cto-reports/sadec/cto-sadec.log"

mkdir -p /Users/mac/mekong-cli/.cto-reports/sadec

IDX=0
TASKS=(
    '/cook "Scan broken links meta tags accessibility trong '$SADEC_APP'"'
    '/dev-feature "Them features moi va cai thien UX trong '$SADEC_APP'"'
    '/dev-bug-sprint "Debug fix bugs console errors broken imports trong '$SADEC_APP'"'
    '/dev-pr-review "Review code quality check patterns dead code '$SADEC_APP'"'
    '/frontend-responsive-fix "Fix responsive 375px 768px 1024px '$SADEC_APP'"'
    '/eng-tech-debt "Refactor consolidate duplicate code '$SADEC_APP'"'
    '/cook "Toi uu performance minify CSS JS lazy load cache '$SADEC_APP'"'
    '/frontend-ui-build "Build dashboard widgets charts KPIs '$SADEC_APP'/admin"'
    '/dev-feature "Them dark mode toggle theme switching '$SADEC_APP'"'
    '/cook "Them SEO metadata og tags title description '$SADEC_APP'"'
    '/dev-bug-sprint "Viet them tests tang coverage '$SADEC_APP'"'
    '/release-ship "Git commit push '$SADEC_APP' viet release notes"'
)
TL=${#TASKS[@]}
CYCLE=0
DIS=0

typeset -A LAST_DISPATCH
LAST_DISPATCH=([0]=0 [1]=0 [2]=0 [3]=0 [4]=0 [5]=0)
LOCK_SEC=45

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

is_worker_busy() {
    local p=$1
    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null | tail -5)

    if echo "$raw" | grep -qE "thinking|Unfurling|Precipitating|Stewing|Pondering|Whirlpooling|Crunching|Clauding"; then
        return 0
    fi
    if echo "$raw" | grep -qE "queued messages|Press up to edit"; then
        return 0
    fi
    if echo "$raw" | grep -qE "◻|◼|pending|completed"; then
        return 0
    fi
    if echo "$raw" | grep -qE "Read.*file|Write\(|Bash\(|Searched|Created|Updated|ctrl\+o"; then
        return 0
    fi
    if echo "$raw" | grep -qE "approve edit|confirm|Enter to select|navigate.*Esc"; then
        return 0
    fi
    if echo "$raw" | grep -qE "esc to"; then
        return 0
    fi
    return 1
}

is_worker_alive() {
    local p=$1
    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null | tail -3)
    if echo "$raw" | grep -qE "bypass permissions|shortcuts"; then
        return 0
    fi
    return 1
}

heal_worker() {
    local p=$1
    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null | tail -2)
    if ! echo "$raw" | grep -qE "bypass|shortcuts|thinking|Unfurling|Stewing|Pondering|esc to|◻|◼|Read|Write|Bash|Searched"; then
        log "🔧 S$p DEAD → restarting CC CLI"
        $T send-keys -t "$S:$W.$p" "cd $SADEC_APP && claude --dangerously-skip-permissions" Enter
        LAST_DISPATCH[$p]=$(($(date +%s) + 15))
    fi
}

can_dispatch() {
    local p=$1
    local now=$(date +%s)

    local last=${LAST_DISPATCH[$p]:-0}
    local age=$((now - last))
    if (( age < LOCK_SEC )); then
        return 1
    fi

    if is_worker_busy "$p"; then
        LAST_DISPATCH[$p]=$now
        return 1
    fi

    if is_worker_alive "$p"; then
        return 0
    fi

    heal_worker "$p"
    return 1
}

echo "╔══════════════════════════════════════════╗"
echo "║ 🧠 CTO SADEC v5 — SIMPLE & RELIABLE    ║"
echo "║ Lock: ${LOCK_SEC}s | Workers: $NP        ║"
echo "╚══════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        if can_dispatch "$p"; then
            local task="${TASKS[$((IDX % TL + 1))]}"
            log "✅ S$p → $(echo $task | head -c 60)..."
            $T send-keys -t "$S:$W.$p" "$task" Enter
            LAST_DISPATCH[$p]=$(date +%s)
            ((IDX++))
            ((DIS++))
        fi
    done

    echo "═══ 🧠 SADEC-v5 $(date +%H:%M:%S) cy:$CYCLE dis:$DIS ═══"
    sleep 12
done
