---
name: cto-dashboard
description: "CTO brain health dashboard — ROI scores, active missions, learning state"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /cto-dashboard — CTO Brain Health Dashboard

Shows factory CTO brain status: ROI per project, learning state, active missions.

## Implementation

```bash
echo "=== CTO BRAIN DASHBOARD ==="
echo "$(date)"
echo ""

# ROI Scores from factory-metrics.log
echo "--- Project ROI Scores ---"
node -e "
  try {
    const r = require('$HOME/mekong-cli/apps/openclaw-worker/lib/factory-roi-calculator');
    const d = r.getDashboardData();
    const roi = d.projectROI;
    console.log('Metrics log: ' + d.metricsLineCount + ' events');
    console.log('Commands learned: ' + d.brainState.commandsLearned);
    console.log('Project states tracked: ' + d.brainState.projectStatesTracked);
    console.log('Last brain update: ' + d.brainState.lastUpdated);
    console.log('');
    console.log('Project              | Dispatches | Success | Timeout | ROI');
    console.log('---------------------|------------|---------|---------|-----');
    for (const [name, s] of Object.entries(roi)) {
      const n = name.padEnd(20);
      console.log(n + ' | ' + String(s.dispatches).padStart(10) + ' | ' + String(s.successes).padStart(7) + ' | ' + String(s.timeouts).padStart(7) + ' | ' + s.roi + '%');
    }
    if (Object.keys(roi).length === 0) console.log('(no metrics yet — run factory-loop.sh first)');
  } catch(e) {
    console.log('Factory ROI calculator not available: ' + e.message);
  }
" 2>/dev/null

echo ""
echo "--- Active Panes ---"
for P in 0 1; do
  LAST5=$(tmux capture-pane -t tom_hum:0.$P -p 2>/dev/null | tail -5)
  if echo "$LAST5" | grep -qE "❯|bypass"; then
    echo "P$P: IDLE"
  elif echo "$LAST5" | grep -qE "thinking|Cooking|Brewing|Running"; then
    echo "P$P: WORKING"
  else
    echo "P$P: $(echo "$LAST5" | tail -1 | head -c 60)"
  fi
done

echo ""
echo "--- Brain Learning State ---"
BRAIN_STATE="$HOME/mek

[Full documentation at agencyos.network]

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
