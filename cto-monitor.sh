#!/bin/zsh
# ═══════════════════════════════════════════════════════════
# 🔍 CTO MONITOR + M1 COOLER — Continuous Loop
# Auto: monitor workers, accept permissions, re-dispatch idle, cool RAM
# ═══════════════════════════════════════════════════════════

SESSION="tom_hum"
INTERVAL=30
CYCLE=0
LOG="/tmp/cto-monitor.log"

# Task queue for idle workers
TASKS=(
  "/dev-feature Upgrade sadec-marketing-hub login system — thêm OAuth Google, magic link vào portal/login.html. Cyber-Glass 2026 style."
  "/frontend-ui-build ROIaaS Phase Tracker widget — tạo apps/sadec-marketing-hub/admin/components/phase-tracker.html. Hiện 5 phases với progress bars."
  "/backend-api-build ROIaaS Subscription API — tạo apps/sadec-marketing-hub/supabase/functions/roiaas-subscription/index.ts. CRUD subscription tiers."
  "/dev-feature OCOP Product Catalog — tạo apps/sadec-marketing-hub/portal/ocop-catalog.html. Grid view sản phẩm OCOP với filter, search, OCOP rating."
  "/frontend-ui-build ROIaaS Analytics Charts — tạo apps/sadec-marketing-hub/admin/components/roi-charts.html. Line charts ROI, bar charts revenue."
  "/cook Viết comprehensive tests cho tất cả ROIaaS modules trong apps/sadec-marketing-hub/tests/"
  "/dev-feature Client ROI Report — tạo apps/sadec-marketing-hub/portal/roi-report.html. Auto-generate PDF ROI report cho clients."
  "/backend-api-build Notification Engine — tạo apps/sadec-marketing-hub/supabase/functions/notify-engine/index.ts. Email + Zalo + Push notifications."
)
TASK_INDEX=0

eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || true

echo "🔍 CTO MONITOR v1.0 — Started $(date '+%H:%M:%S')" | tee $LOG
echo "⏱  Interval: ${INTERVAL}s" | tee -a $LOG

while true; do
    CYCLE=$((CYCLE + 1))
    TS=$(date '+%H:%M:%S')
    
    # ═══ 1. CHECK WORKERS ═══
    ACTIVE=0
    IDLE=0
    PERMISSION=0
    
    for p in 0 1 2 3; do
        OUT=$(tmux capture-pane -t $SESSION:0.$p -p 2>/dev/null | tail -8)
        
        # Auto-accept permissions
        if echo "$OUT" | grep -q "Yes, allow\|Do you want to proceed\|Esc to cancel"; then
            if echo "$OUT" | grep -q "during this session"; then
                # Select option 2 (session-wide)
                tmux send-keys -t $SESSION:0.$p Down Enter 2>/dev/null
            else
                tmux send-keys -t $SESSION:0.$p "" Enter 2>/dev/null
            fi
            PERMISSION=$((PERMISSION + 1))
            ACTIVE=$((ACTIVE + 1))
            echo "[$TS] 🔓 P$p: Auto-accepted permission" >> $LOG
            
        elif echo "$OUT" | grep -q "esc to interrupt"; then
            ACTIVE=$((ACTIVE + 1))
            
        elif echo "$OUT" | grep -q "for shortcuts\|Worked for\|Try \""; then
            IDLE=$((IDLE + 1))
            
            # Auto-dispatch from task queue
            if [ $TASK_INDEX -lt ${#TASKS[@]} ]; then
                TASK="${TASKS[$((TASK_INDEX + 1))]}"
                if [ -n "$TASK" ]; then
                    tmux send-keys -t $SESSION:0.$p "$TASK" Enter 2>/dev/null
                    echo "[$TS] 🚀 P$p: Dispatched task #$TASK_INDEX" >> $LOG
                    TASK_INDEX=$((TASK_INDEX + 1))
                fi
            fi
        fi
    done
    
    # ═══ 2. COOL M1 ═══
    if [ $((CYCLE % 3)) -eq 0 ]; then
        sync 2>/dev/null
        FREE=$(vm_stat 2>/dev/null | grep "Pages free" | awk '{print $3}' | tr -d '.')
        LOAD=$(uptime | awk -F'load averages:' '{print $2}' | xargs)
        echo "[$TS] ❄️  RAM free: ${FREE} pages | Load: $LOAD" >> $LOG
    fi
    
    # ═══ 3. STATUS LINE ═══
    printf "\r[%s] 🔍 Cycle:%d | Active:%d/4 | Idle:%d | Perms:%d | Tasks:%d/%d     " \
        "$TS" $CYCLE $ACTIVE $IDLE $PERMISSION $TASK_INDEX ${#TASKS[@]}
    
    # ═══ 4. LOG SUMMARY ═══
    if [ $((CYCLE % 6)) -eq 0 ]; then
        echo "" >> $LOG
        echo "[$TS] ═══ CYCLE $CYCLE SUMMARY ═══" >> $LOG
        echo "  Active: $ACTIVE/4 | Idle: $IDLE | Dispatched: $TASK_INDEX/${#TASKS[@]}" >> $LOG
        for p in 0 1 2 3; do
            LAST=$(tmux capture-pane -t $SESSION:0.$p -p 2>/dev/null | grep -v '^$' | tail -1)
            echo "  P$p: $LAST" >> $LOG
        done
    fi
    
    sleep $INTERVAL
done
