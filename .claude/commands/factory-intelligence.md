---
description: "Show CTO brain intelligence — command effectiveness, output patterns, learning insights"
argument-hint: [--detailed | --project=name]
allowed-tools: Bash, Read
---

# /factory-intelligence — CTO Brain Intelligence Report

Shows what the CTO has learned about command effectiveness across projects.

## Implementation

```bash
echo "=== CTO Brain Intelligence Report ==="
echo "$(date)"
echo ""

BRAIN_STATE="$HOME/mekong-cli/apps/openclaw-worker/brain-learning-state.json"
METRICS="/tmp/factory-metrics.log"

# 1. Output type distribution
if [ -f "$METRICS" ]; then
  echo "--- Output Intelligence ---"
  echo "What commands actually produce:"
  echo ""
  for TYPE in code_written test_passed build_success deploy_success analysis_only error timeout unknown; do
    COUNT=$(grep -c "$TYPE" "$METRICS" 2>/dev/null || echo "0")
    if [ "$COUNT" -gt 0 ]; then
      BAR=$(printf '%*s' "$COUNT" '' | tr ' ' '#')
      printf "  %-16s %3d %s\n" "$TYPE" "$COUNT" "$BAR"
    fi
  done
  echo ""

  # Code vs analysis ratio
  CODE=$(grep -c "code_written" "$METRICS" 2>/dev/null || echo "0")
  ANALYSIS=$(grep -c "analysis_only" "$METRICS" 2>/dev/null || echo "0")
  TOTAL=$((CODE + ANALYSIS))
  if [ "$TOTAL" -gt 0 ]; then
    RATIO=$((CODE * 100 / TOTAL))
    echo "  Code output ratio: ${RATIO}% (${CODE} code / ${ANALYSIS} analysis)"
  fi
  echo ""
fi

# 2. Command effectiveness from brain learning state
if [ -f "$BRAIN_STATE" ]; then
  echo "--- Command Effectiveness (Learned) ---"
  node -e "
    const s = JSON.parse(require('fs').readFileSync('$BRAIN_STATE','utf-8'));
    const ce = s.commandEffectiveness || {};
    const entries = Object.entries(ce).sort((a,b) => {
      const rateA = a[1].total > 0 ? a[1].success / a[1].total : 0;
      const rateB = b[1].total > 0 ? b[1].success / b[1].total : 0;
      return rateB - rateA;
    });

    if (entries.length === 0) {
      console.log('  (no learning data yet)');
    } else {
      console.log('  Commands learned: ' + entries.length);
      console.log('');
      console.log('  Top performers:');
      entries.slice(0, 5).forEach(([cmd, d]) => {
        const rate = d.total > 0 ? Math.round(d.success/d.total*100) : 0;
        const bar = '#'.repeat(Math.round(rate/10));
        console.log('    ' + String(rate).padStart(3) + '% ' + bar.padEnd(10) + ' ' + cmd);
      });

      const failures = entries.filter(([,d]) => d.total > 2 && d.success/d.total < 0.5);
      if (failures.length > 0) {
        console.log('');
        console.log('  Underperformers (< 50% success, > 2 attempts):');
        failures.forEach(([cmd, d]) => {
          const rate = Math.round(d.success/d.total*100);
          console.log('    ' + String(rate).padStart(3) + '% (' + d.success + '/' + d.total + ') ' + cmd);
        });
      }
    }

    // Project-state insights
    const ps = s.projectStates || {};
    const psEntries = Object.entries(ps);
    if (psEntries.length > 0) {
      console.log('');
      console.log('  --- Project-State Insights ---');
      psEntries.forEach(([key, data]) => {
        const best = (data.bestCommands || []).slice(-2);
        const worst = (data.worstCommands || []).slice(-2);
        console.log('  ' + key + ':');
        if (best.length) console.log('    Best:  ' + best.join(', '));
        if (worst.length) console.log('    Avoid: ' + worst.join(', '));
      });
    }
  " 2>/dev/null
else
  echo "  (no brain-learning-state.json yet — run factory-loop.sh first)"
fi

echo ""
echo "--- Summary ---"
if [ -f "$METRICS" ]; then
  TOTAL_EVENTS=$(wc -l < "$METRICS" 2>/dev/null || echo "0")
  echo "  Total metrics events: $TOTAL_EVENTS"
  echo "  First event: $(head -1 "$METRICS" | cut -d'|' -f1 | xargs)"
  echo "  Last event:  $(tail -1 "$METRICS" | cut -d'|' -f1 | xargs)"
fi
```

## Goal context

<goal>$ARGUMENTS</goal>
