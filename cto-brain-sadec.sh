#!/bin/zsh
# ═══════════════════════════════════════════════════
# 🧠 CTO SADEC v8 — CONTEXT-DRIVEN FAST DISPATCH
# Same logic as CTO-FNB v8
# ═══════════════════════════════════════════════════

SADEC_APP="/Users/mac/mekong-cli/apps/sadec-marketing-hub"
T="/opt/homebrew/bin/tmux"
S="tom_hum"; W="0"; NP=6
LOG="/Users/mac/mekong-cli/.cto-reports/sadec/cto-sadec.log"
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
TL=${#TASKS[@]}
CYCLE=0; DIS=0

echo "╔═════════════════════════════════════════╗"
echo "║ 🧠 CTO SADEC v8 — CONTEXT-DRIVEN FAST ║"
echo "╚═════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        RAW=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null)

        if echo "$RAW" | grep -qE "Enter to select|Tab.*navigate" && echo "$RAW" | grep -qE "\[ \]"; then
            N=$(echo "$RAW" | grep -c "\[ \]")
            for ((j=0; j<N; j++)); do $T send-keys -t "$S:$W.$p" " "; sleep 0.3; $T send-keys -t "$S:$W.$p" Down; sleep 0.3; done
            $T send-keys -t "$S:$W.$p" Down; sleep 0.3; $T send-keys -t "$S:$W.$p" Enter
            echo "[$(date +%H:%M:%S)] 🎯 S$p: Auto-select" | tee -a "$LOG"
            continue
        fi

        STATUS_LINE=$(echo "$RAW" | grep "bypass permissions on" | tail -1)

        if [ -z "$STATUS_LINE" ]; then
            echo "[$(date +%H:%M:%S)] ⚠️ S$p: no status line" | tee -a "$LOG"
            continue
        fi

        if echo "$RAW" | grep -qi "queued messages"; then
            echo "[$(date +%H:%M:%S)] ❌ S$p: STACKED" | tee -a "$LOG"
            continue
        fi

        if echo "$STATUS_LINE" | grep -q "esc to interrupt"; then
            echo "[$(date +%H:%M:%S)] 🔥 S$p: WORKING" | tee -a "$LOG"
            continue
        fi

        TASK="${TASKS[$((IDX % TL + 1))]}"
        echo "[$(date +%H:%M:%S)] ✅ S$p: DONE → 🚀 $(echo $TASK | head -c 60)..." | tee -a "$LOG"
        $T send-keys -t "$S:$W.$p" "$TASK" Enter
        ((IDX++)); ((DIS++))
    done

    echo "═══ 🧠 CTO-SADEC $(date +%H:%M:%S) ═══ cy:$CYCLE dis:$DIS ═══"
    sleep 15
done
