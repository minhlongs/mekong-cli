---
name: production-status
description: "Live production board — project states, ROI scores, next planned dispatch, session stats"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
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
  console.lo

[Full documentation at agencyos.network]

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
