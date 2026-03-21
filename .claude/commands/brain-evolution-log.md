---
description: "Show CTO brain evolution history — what it learned over time, strategy changes"
argument-hint: [--last=10 | --all]
allowed-tools: Bash
---

# /brain-evolution-log — Brain Evolution History

Shows how the CTO brain has evolved over time: which commands got promoted/demoted, learning progression.

## Implementation

```bash
echo "=== BRAIN EVOLUTION LOG ==="
echo "$(date)"
echo ""

BRAIN_STATE="$HOME/mekong-cli/apps/openclaw-worker/brain-learning-state.json"

if [ ! -f "$BRAIN_STATE" ]; then
  echo "No brain-learning-state.json found. Factory loop hasn't run yet."
  exit 0
fi

node -e "
  const s = JSON.parse(require('fs').readFileSync('$BRAIN_STATE','utf-8'));
  const log = s.evolutionLog || [];
  const ce = s.commandEffectiveness || {};

  console.log('--- Brain Stats ---');
  console.log('Commands learned: ' + Object.keys(ce).length);
  console.log('Evolution events: ' + log.length);
  console.log('Last updated: ' + (s.lastUpdated || 'never'));
  console.log('');

  if (log.length === 0) {
    console.log('No evolution events yet. Brain evolves every 10 factory cycles.');
    return;
  }

  console.log('--- Evolution Timeline ---');
  console.log('Date                 | Cmds | Top Command                    | Rate | Worst');
  console.log('---------------------|------|--------------------------------|------|------');
  const shown = log.slice(-20);
  for (const e of shown) {
    console.log([
      (e.ts || '').slice(0,19).padEnd(19),
      String(e.commandsLearned || 0).padStart(4),
      (e.topCommand || 'none').slice(0,30).padEnd(30),
      ((e.topRate || 0) + '%').padStart(4),
      (e.worstCommand || 'none').slice(0,20),
    ].join(' | '));
  }

  // Success rate trend
  if (log.length >= 3) {
    const first3 = log.slice(0,3).reduce((s,e) => s + (e.topRate||0), 0) / 3;
    const last3 = log.slice(-3).reduce((s,e) => s + (e.topRate||0), 0) / 3;
    const trend = last3 > first3 ? 'IMPROVING' : last3 < first3 ? 'DECLINING' : 'STABLE';
    console.log('');
    console.log('Trend: ' + trend + ' (early avg: ' + Math.round(first3) + '% -> recent avg: ' + Math.round(last3) + '%)');
  }
" 2>/dev/null
```

## Goal context

<goal>$ARGUMENTS</goal>
