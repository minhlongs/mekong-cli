#!/bin/zsh
# ═══════════════════════════════════════════════════
# 🧠 CTO F&B v8 — CONTEXT-DRIVEN FAST DISPATCH
#
# Reads context to KNOW when worker is done:
#   BUSY: status line has "bypass...esc to interrupt" 
#   IDLE: status line has "bypass" WITHOUT "esc to interrupt"
#   STACKED: "queued messages" visible
# Cycle: 15s. Dispatch immediately when idle detected.
# ═══════════════════════════════════════════════════

FNB_APP="/Users/mac/mekong-cli/apps/fnb-caffe-container"
T="/opt/homebrew/bin/tmux"
S="tom_hum"; W="fnb"; NP=4
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
CYCLE=0; DIS=0

echo "╔═════════════════════════════════════════╗"
echo "║ 🧠 CTO F&B v8 — CONTEXT-DRIVEN FAST   ║"
echo "╚═════════════════════════════════════════╝"

while true; do
    ((CYCLE++))

    for ((p=0; p<NP; p++)); do
        RAW=$($T capture-pane -t "$S:$W.$p" -p 2>/dev/null)

        # Auto-select checkboxes
        if echo "$RAW" | grep -qE "Enter to select|Tab.*navigate" && echo "$RAW" | grep -qE "\[ \]"; then
            N=$(echo "$RAW" | grep -c "\[ \]")
            for ((j=0; j<N; j++)); do $T send-keys -t "$S:$W.$p" " "; sleep 0.3; $T send-keys -t "$S:$W.$p" Down; sleep 0.3; done
            $T send-keys -t "$S:$W.$p" Down; sleep 0.3; $T send-keys -t "$S:$W.$p" Enter
            echo "[$(date +%H:%M:%S)] 🎯 F$p: Auto-select" | tee -a "$LOG"
            continue
        fi

        # Find the STATUS LINE (contains "bypass permissions")
        STATUS_LINE=$(echo "$RAW" | grep "bypass permissions on" | tail -1)

        if [ -z "$STATUS_LINE" ]; then
            echo "[$(date +%H:%M:%S)] ⚠️ F$p: no status line — dead?" | tee -a "$LOG"
            continue
        fi

        # STACKED: queued messages
        if echo "$RAW" | grep -qi "queued messages"; then
            echo "[$(date +%H:%M:%S)] ❌ F$p: STACKED (queued)" | tee -a "$LOG"
            continue
        fi

        # BUSY: status line contains "esc to interrupt"
        if echo "$STATUS_LINE" | grep -q "esc to interrupt"; then
            echo "[$(date +%H:%M:%S)] 🔥 F$p: WORKING" | tee -a "$LOG"
            continue
        fi

        # IDLE: bypass without esc to interrupt → worker finished → DISPATCH
        TASK="${TASKS[$((IDX % TL + 1))]}"
        echo "[$(date +%H:%M:%S)] ✅ F$p: DONE → 🚀 $(echo $TASK | head -c 60)..." | tee -a "$LOG"
        $T send-keys -t "$S:$W.$p" "$TASK" Enter
        ((IDX++)); ((DIS++))
    done

    echo "═══ 🧠 CTO-FNB $(date +%H:%M:%S) ═══ cy:$CYCLE dis:$DIS ═══"
    sleep 15
done
