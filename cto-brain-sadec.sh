#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO SADEC FINAL — LOCK FILE BASED (NO PANE DETECTION)
# Same architecture as CTO-FNB FINAL
# ═══════════════════════════════════════════════════════════

SADEC_APP="/Users/mac/mekong-cli/apps/sadec-marketing-hub"
T="/opt/homebrew/bin/tmux"; S="tom_hum"; W="0"; NP=6
LOG="/Users/mac/mekong-cli/.cto-reports/sadec/cto-sadec.log"
LOCK_DIR="/tmp"
LOCK_TTL=180

mkdir -p /Users/mac/mekong-cli/.cto-reports/sadec

IDX=0
TASKS=(
    '/cook "Quet broken links meta tags accessibility trong '$SADEC_APP'"'
    '/dev-feature "Them features moi va cai thien UX trong '$SADEC_APP'"'
    '/dev-bug-sprint "Viet tests cho '$SADEC_APP' cover untested pages"'
    '/dev-pr-review "Review code quality '$SADEC_APP' check patterns dead code"'
    '/frontend-responsive-fix "Fix responsive 375px 768px 1024px trong '$SADEC_APP'/portal va admin"'
    '/eng-tech-debt "Refactor '$SADEC_APP' consolidate duplicate code"'
    '/cook "Toi uu performance '$SADEC_APP' minify CSS JS lazy load cache"'
    '/frontend-ui-build "Build dashboard widgets charts KPIs '$SADEC_APP'/admin"'
    '/release-ship "Git commit push thay doi trong '$SADEC_APP' viet release notes"'
    '/cook "Them SEO metadata og tags title description vao '$SADEC_APP'"'
    '/dev-bug-sprint "Debug fix bugs '$SADEC_APP' console errors broken imports"'
    '/frontend-ui-build "Nang cap UI '$SADEC_APP' micro-animations loading states"'
)
TL=${#TASKS[@]}; CYCLE=0; DIS=0

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG"; }

can_dispatch() {
    local p=$1
    local lock="$LOCK_DIR/cto-lock-sadec-$p"
    local now=$(date +%s)

    if [ -f "$lock" ]; then
        local lock_time=$(cat "$lock" 2>/dev/null)
        local age=$((now - lock_time))
        if (( age < LOCK_TTL )); then
            log "  🔒 S$p: locked ($((LOCK_TTL - age))s left)"
            return 1
        fi
    fi

    local raw=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null)
    if echo "$raw" | grep -qi "queued messages"; then
        echo "$now" > "$lock"
        log "  ❌ S$p: queued (lock renewed)"
        return 1
    fi

    return 0
}

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
        log "  🎯 S$p: Auto-select"
    fi
}

echo "╔══════════════════════════════════════════╗"
echo "║ 🧠 CTO SADEC FINAL — LOCK FILE BASED   ║"
echo "║ Lock TTL: ${LOCK_TTL}s | Cycle: 15s     ║"
echo "╚══════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        do_auto_select "$p"

        if can_dispatch "$p"; then
            local task="${TASKS[$((IDX % TL + 1))]}"
            log "  ✅ S$p → 🚀 $(echo $task | head -c 55)..."
            $T send-keys -t "$S:$W.$p" "$task" Enter
            echo "$(date +%s)" > "$LOCK_DIR/cto-lock-sadec-$p"
            ((IDX++)); ((DIS++))
        fi
    done

    echo "═══ 🧠 SADEC $(date +%H:%M:%S) cy:$CYCLE dis:$DIS ═══"
    sleep 15
done
