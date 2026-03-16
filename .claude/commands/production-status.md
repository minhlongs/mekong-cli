---
description: "Live production board — project states, ROI scores, next planned dispatch, session stats"
argument-hint: [--all | --project=name]
allowed-tools: Bash
---

# /production-status — Live Production Board

Shows real-time production status by combining factory-metrics.log, brain-learning-state.json, and git stats.

## Implementation

```bash
echo "=== PRODUCTION STATUS BOARD ==="
echo "$(date)"
echo ""

# 1. Project states + ROI
echo "--- Project Status ---"
node -e "
  const ft = require('$HOME/mekong-cli/apps/openclaw-worker/lib/factory-throughput-optimizer');
  const roi = require('$HOME/mekong-cli/apps/openclaw-worker/lib/factory-roi-calculator');
  const ws = ft.getWorkforceStatus();
  const roiData = roi.calculateProjectROI();

  console.log('Project              | State        | ROI  | Dispatches | Success | Avg Time');
  console.log('---------------------|--------------|------|------------|---------|--------');
  for (const p of ws.panes) {
    const r = roiData[p.project] || { roi: 0, dispatches: 0, successes: 0, avgDuration: 0 };
    console.log([
      p.project.padEnd(20),
      p.state.padEnd(12),
      (r.roi + '%').padStart(4),
      String(r.dispatches).padStart(10),
      String(r.successes).padStart(7),
      (r.avgDuration + 's').padStart(7),
    ].join(' | '));
  }
" 2>/dev/null

echo ""

# 2. Session stats from git
echo "--- Session Stats (today) ---"
TODAY=$(date +%Y-%m-%d)
COMMITS_TODAY=$(git log --oneline --since="$TODAY" 2>/dev/null | wc -l | xargs)
LINES_TODAY=$(git diff --stat $(git log --oneline --since="$TODAY" --format=%H | tail -1)..HEAD 2>/dev/null | tail -1 || echo "0")
echo "  Commits today: $COMMITS_TODAY"
echo "  Changes: $LINES_TODAY"

echo ""

# 3. Brain learning summary
echo "--- Brain Intelligence ---"
node -e "
  const roi = require('$HOME/mekong-cli/apps/openclaw-worker/lib/factory-roi-calculator');
  const d = roi.getDashboardData();
  console.log('  Commands learned: ' + d.brainState.commandsLearned);
  console.log('  States tracked: ' + d.brainState.projectStatesTracked);
  console.log('  Last update: ' + (d.brainState.lastUpdated || 'never'));
  console.log('  Metrics events: ' + d.metricsLineCount);
" 2>/dev/null

echo ""

# 4. Factory loop status
echo "--- Factory Loop ---"
if [ -f /tmp/factory.pid ]; then
  PID=$(cat /tmp/factory.pid)
  if kill -0 "$PID" 2>/dev/null; then
    echo "  Status: RUNNING (PID $PID)"
  else
    echo "  Status: DEAD (stale PID $PID)"
  fi
else
  echo "  Status: NOT RUNNING"
fi

if [ -f /tmp/factory-metrics.log ]; then
  LAST=$(tail -1 /tmp/factory-metrics.log | cut -d'|' -f1-4 | xargs)
  echo "  Last event: $LAST"
fi
```

## Goal context

<goal>$ARGUMENTS</goal>
