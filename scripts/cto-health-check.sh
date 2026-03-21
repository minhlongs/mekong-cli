#!/bin/bash
# CTO Health Check — Master dashboard for all factory subsystems
# Usage: bash scripts/cto-health-check.sh
set -uo pipefail

G="\033[32m" R="\033[31m" Y="\033[33m" C="\033[36m" B="\033[1m" D="\033[0m"
OK="${G}OK${D}" FAIL="${R}FAIL${D}" WARN="${Y}WARN${D}"

echo -e "${B}${C}╔══════════════════════════════════════════╗${D}"
echo -e "${B}${C}║       CTO HEALTH CHECK DASHBOARD         ║${D}"
echo -e "${B}${C}╚══════════════════════════════════════════╝${D}"
echo -e "  $(date)"
echo ""

# 1. Factory Loop
echo -e "${B}─── Factory Loop ───${D}"
if [ -f /tmp/factory.pid ]; then
  PID=$(cat /tmp/factory.pid)
  if kill -0 "$PID" 2>/dev/null; then
    UPTIME=$(ps -o etime= -p "$PID" 2>/dev/null | xargs)
    echo -e "  Status: ${OK} (PID $PID, uptime: $UPTIME)"
  else
    echo -e "  Status: ${FAIL} (stale PID $PID)"
  fi
else
  echo -e "  Status: ${FAIL} (no PID file)"
fi

# 2. Pane Health
echo -e "\n${B}─── CC CLI Panes ───${D}"
for P in 0 1; do
  PROJ=$([ $P -eq 0 ] && echo "sophia-proposal" || echo "well")
  if tmux capture-pane -t tom_hum:0.$P -p > /dev/null 2>&1; then
    TAIL=$(tmux capture-pane -t tom_hum:0.$P -p 2>/dev/null | tail -3)
    if echo "$TAIL" | grep -qE "❯|bypass"; then
      echo -e "  P$P ($PROJ): ${OK} IDLE"
    elif echo "$TAIL" | grep -qE "thinking|Cooking|Running|Brewing"; then
      echo -e "  P$P ($PROJ): ${G}WORKING${D}"
    else
      echo -e "  P$P ($PROJ): ${Y}ACTIVE${D}"
    fi
  else
    echo -e "  P$P ($PROJ): ${FAIL} DEAD"
  fi
done

# 3. Dispatch History + Dedup
echo -e "\n${B}─── Dedup System ───${D}"
if [ -f /tmp/factory-dispatch-history.log ]; then
  TOTAL=$(wc -l < /tmp/factory-dispatch-history.log | xargs)
  UNIQUE=$(awk -F'|' '{print $3}' /tmp/factory-dispatch-history.log | sort -u | wc -l | xargs)
  DUPES=$((TOTAL - UNIQUE))
  echo -e "  History: ${OK} ($TOTAL entries, $UNIQUE unique)"
  echo -e "  Duplicates prevented: ${C}$DUPES${D}"
  if [ "$TOTAL" -gt 0 ]; then
    DEDUP_RATE=$((DUPES * 100 / TOTAL))
    echo -e "  Dedup rate: ${C}${DEDUP_RATE}%${D}"
  fi
else
  echo -e "  History: ${WARN} (no file yet)"
fi

# 4. Metrics Log
echo -e "\n${B}─── Metrics ───${D}"
if [ -f /tmp/factory-metrics.log ]; then
  LINES=$(wc -l < /tmp/factory-metrics.log | xargs)
  DISPATCHES=$(grep -c "dispatch" /tmp/factory-metrics.log 2>/dev/null || true)
  SUCCESSES=$(grep -c "success\|code_written" /tmp/factory-metrics.log 2>/dev/null || true)
  ERRORS=$(grep -c "timeout\|crash\|error" /tmp/factory-metrics.log 2>/dev/null || true)
  echo -e "  Events: ${OK} ($LINES total)"
  echo -e "  Dispatches: ${C}$DISPATCHES${D} | Success: ${G}$SUCCESSES${D} | Errors: ${R}$ERRORS${D}"
else
  echo -e "  Metrics: ${WARN} (no file)"
fi

# 5. Brain Learning
echo -e "\n${B}─── Brain State ───${D}"
BRAIN="$HOME/mekong-cli/apps/openclaw-worker/brain-learning-state.json"
if [ -f "$BRAIN" ]; then
  if node -e "JSON.parse(require('fs').readFileSync('$BRAIN','utf-8')); console.log('valid')" 2>/dev/null | grep -q valid; then
    CMDS=$(node -e "const s=JSON.parse(require('fs').readFileSync('$BRAIN','utf-8'));console.log(Object.keys(s.commandEffectiveness||{}).length)" 2>/dev/null)
    EVOS=$(node -e "const s=JSON.parse(require('fs').readFileSync('$BRAIN','utf-8'));console.log((s.evolutionLog||[]).length)" 2>/dev/null)
    echo -e "  State: ${OK} ($CMDS commands, $EVOS evolutions)"
  else
    echo -e "  State: ${FAIL} (corrupt JSON)"
  fi
else
  echo -e "  State: ${WARN} (no file — first run)"
fi

# 6. Anomaly Detector
echo -e "\n${B}─── Anomalies ───${D}"
AD=$(node -e "try{const a=require('$HOME/mekong-cli/apps/openclaw-worker/lib/cto-anomaly-detector');const r=a.detectAnomalies();console.log(r.severity+'|'+r.anomalies.length)}catch(e){console.log('error|0')}" 2>/dev/null)
SEV=$(echo "$AD" | cut -d'|' -f1)
CNT=$(echo "$AD" | cut -d'|' -f2)
if [ "$SEV" = "ok" ]; then
  echo -e "  Status: ${OK} (no anomalies)"
elif [ "$SEV" = "warn" ]; then
  echo -e "  Status: ${WARN} ($CNT warning(s))"
else
  echo -e "  Status: ${FAIL} ($CNT anomaly/anomalies)"
fi

echo -e "\n${B}${C}══════════════════════════════════════════${D}"
