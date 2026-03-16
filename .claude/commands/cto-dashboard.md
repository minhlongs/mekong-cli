---
description: "CTO brain health dashboard — ROI scores, active missions, learning state"
argument-hint: [--roi | --learning | --missions | --all]
allowed-tools: Bash, Read
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
BRAIN_STATE="$HOME/mekong-cli/apps/openclaw-worker/brain-learning-state.json"
if [ -f "$BRAIN_STATE" ]; then
  node -e "
    const s = JSON.parse(require('fs').readFileSync('$BRAIN_STATE','utf-8'));
    const ce = s.commandEffectiveness || {};
    const sorted = Object.entries(ce).sort((a,b) => (b[1].success/b[1].total) - (a[1].success/a[1].total));
    console.log('Top 5 effective commands:');
    sorted.slice(0,5).forEach(([cmd, d]) => {
      const rate = d.total > 0 ? Math.round(d.success/d.total*100) : 0;
      console.log('  ' + rate + '% (' + d.success + '/' + d.total + ') ' + cmd);
    });
    if (sorted.length > 5) {
      console.log('');
      console.log('Bottom 3 (avoid):');
      sorted.slice(-3).forEach(([cmd, d]) => {
        const rate = d.total > 0 ? Math.round(d.success/d.total*100) : 0;
        console.log('  ' + rate + '% (' + d.success + '/' + d.total + ') ' + cmd);
      });
    }
  " 2>/dev/null
else
  echo "(no learning data yet — brain-learning-state.json not created)"
fi

echo ""
echo "--- Factory Loop Status ---"
FACTORY_PID=$(pgrep -f "factory-loop.sh" 2>/dev/null || echo "not running")
echo "Factory PID: $FACTORY_PID"
if [ -f /tmp/factory-metrics.log ]; then
  echo "Metrics size: $(wc -l < /tmp/factory-metrics.log) lines"
  echo "Last event: $(tail -1 /tmp/factory-metrics.log | cut -d'|' -f1-4)"
fi
```

## Goal context

<goal>$ARGUMENTS</goal>
