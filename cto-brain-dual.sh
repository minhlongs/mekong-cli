#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🧠 CTO BRAIN v2.2 — DUAL PROJECT FACTORY
# Manages 2 projects independently:
#   Window 0: Sadec Marketing Hub (6P)
#   Window fnb: F&B Caffe Container (4P)
# ═══════════════════════════════════════════════════════════

PROJECT="/Users/mac/mekong-cli"
SADEC_APP="/Users/mac/mekong-cli/apps/sadec-marketing-hub"
FNB_APP="/Users/mac/mekong-cli/apps/fnb-caffe-container"
TMUX_BIN="/opt/homebrew/bin/tmux"
DISPATCH="$HOME/mekong-cli/tom-dispatch.sh"
OLLAMA_URL="http://localhost:11434/api/generate"
REPORT_DIR="$PROJECT/.cto-reports"
SESSION="tom_hum"

# Windows
SADEC_WIN="0"
FNB_WIN="fnb"
SADEC_PANES=6
FNB_PANES=4

mkdir -p "$REPORT_DIR"
cd "$PROJECT" 2>/dev/null

# Auto-detect model
detect_model() {
    for m in "cto-brain:32b" "qwen3:32b" "qwen3:14b"; do
        if ollama show "$m" &>/dev/null; then echo "$m"; return; fi
    done
    echo "qwen3:32b"
}
MODEL=$(detect_model)

# ═══ Sadec Tasks ═══
SADEC_IDX=0
SADEC_TASKS=(
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

# ═══ F&B Tasks ═══
FNB_IDX=0
FNB_TASKS=(
    '/cook "Tao project F&B Caffe Container tai '$FNB_APP' voi landing page menu order system"'
    '/dev-feature "Build menu page voi categories drinks food prices images tai '$FNB_APP'"'
    '/dev-feature "Build order system cart checkout payment tai '$FNB_APP'"'
    '/frontend-ui-build "Build admin dashboard quan ly don hang doanh thu tai '$FNB_APP'"'
    '/cook "Tao responsive landing page hero about contact tai '$FNB_APP'"'
    '/dev-feature "Build customer loyalty rewards system tai '$FNB_APP'"'
    '/frontend-ui-build "Build kitchen display order queue real-time tai '$FNB_APP'"'
    '/cook "Them SEO metadata og tags cho '$FNB_APP'"'
)

# ═══ Get pane output ═══
get_pane() {
    local win="$1" pane="$2" lines="${3:-10}"
    $TMUX_BIN capture-pane -t "$SESSION:$win.$pane" -p -S "-$lines" 2>/dev/null
}

# ═══ Check if pane is idle ═══
is_idle() {
    local win="$1" pane="$2"
    local out=$(get_pane "$win" "$pane" 5)
    if echo "$out" | grep -q "esc to interrupt"; then
        return 1  # busy
    fi
    if echo "$out" | grep -qE "shortcuts|bypass permissions on$|❯ $"; then
        return 0  # idle
    fi
    return 1  # assume busy
}

# ═══ Auto-select multi-choice prompts ═══
auto_select_prompts() {
    local win="$1" pane="$2"
    local out=$(get_pane "$win" "$pane" 15)
    
    # Multi-choice checkboxes
    if echo "$out" | grep -qE "Enter to select.*navigate|Tab.*navigate.*Esc" && echo "$out" | grep -qE "\[ \]|\[✔\]"; then
        if ! echo "$out" | grep -qE "thinking|Precipitating|Clauding|Crunching"; then
            echo "🎯 $win:$pane Auto-select features"
            local unchecked=$(echo "$out" | grep -c "\[ \]")
            for ((j=0; j<unchecked; j++)); do
                $TMUX_BIN send-keys -t "$SESSION:$win.$pane" " "
                sleep 0.3
                $TMUX_BIN send-keys -t "$SESSION:$win.$pane" Down
                sleep 0.3
            done
            $TMUX_BIN send-keys -t "$SESSION:$win.$pane" Down
            sleep 0.3
            $TMUX_BIN send-keys -t "$SESSION:$win.$pane" Enter
        fi
    fi
    
    # Yes/accept bypass
    if echo "$out" | grep -qE "1\..*No.*exit" && echo "$out" | grep -qE "2\..*Yes.*accept"; then
        $TMUX_BIN send-keys -t "$SESSION:$win.$pane" "2" Enter
    fi
}

# ═══ Dispatch to project ═══
dispatch_project() {
    local win="$1" num_panes="$2" project_name="$3"
    shift 3
    local -a tasks=("$@")
    local total=${#tasks[@]}
    local dispatched=0
    
    for ((p=0; p<num_panes; p++)); do
        auto_select_prompts "$win" "$p"
        
        if is_idle "$win" "$p"; then
            local idx_var="${project_name}_IDX"
            local idx=${(P)idx_var}
            local task="${tasks[$((idx % total + 1))]}"
            
            echo "🚀 $project_name P$p ← $(echo $task | head -c 60)..."
            $TMUX_BIN send-keys -t "$SESSION:$win.$p" "$task" Enter
            
            eval "${idx_var}=$((idx + 1))"
            ((dispatched++))
            
            echo "[$(date +%H:%M:%S)] $project_name P$p ← $task" >> "$REPORT_DIR/dispatch_log.txt"
        fi
    done
    
    return $dispatched
}

# ═══ MAIN LOOP ═══
CYCLE=0
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🧠 CTO BRAIN v2.2 — DUAL PROJECT FACTORY           ║"
echo "║  Sadec Marketing Hub: 6P (window 0)                  ║"
echo "║  F&B Caffe Container: 4P (window fnb)                ║"
echo "║  Model: $MODEL                                       ║"
echo "╚═══════════════════════════════════════════════════════╝"

while true; do
    ((CYCLE++))
    
    # Dispatch to Sadec (window 0, 6 panes)
    dispatch_project "$SADEC_WIN" "$SADEC_PANES" "SADEC" "${SADEC_TASKS[@]}"
    
    # Dispatch to F&B (window fnb, 4 panes)
    dispatch_project "$FNB_WIN" "$FNB_PANES" "FNB" "${FNB_TASKS[@]}"
    
    # Status line
    echo "═══ 🧠 CTO v2.2 $(date +%H:%M:%S) ═══ cycle:$CYCLE SADEC_IDX:$SADEC_IDX FNB_IDX:$FNB_IDX ═══"
    
    sleep 12
done
