---
name: factory-intelligence
description: "Show CTO brain intelligence — command effectiveness, output patterns, learning insights"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
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
      console.log('  Commands learned: ' + entri

[Full documentation at agencyos.network]

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
