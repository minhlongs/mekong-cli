---
name: commands-status
description: "Show command health — dispatch count, success rate, avg duration from factory-metrics.log"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /commands-status — Command Health Dashboard

Analyze `/tmp/factory-metrics.log` to show command dispatch statistics.

## Usage

```
/commands-status              # Top 10 most-used commands
/commands-status --all        # All commands with stats
/commands-status /cook        # Stats for specific command
```

## Implementation

Read and parse `/tmp/factory-metrics.log`. Each line format:
```
ISO_TIMESTAMP | event | pane | project | status | duration | command
```

Generate a report with:

1. **Summary**: Total dispatches, success rate, avg duration
2. **Per-command breakdown**: Count, success %, avg time, last used
3. **Per-project breakdown**: Which projects get most dispatches
4. **Timeout/crash stats**: Commands that hung or crashed

```bash
METRICS="/tmp/factory-metrics.log"

if [ ! -f "$METRICS" ]; then
  echo "No metrics file found at $METRICS"
  echo "Factory loop v12.1+ creates this file automatically."
  exit 0
fi

echo "=== Factory Command Health ==="
echo "Log: $METRICS"
echo "Lines: $(wc -l < "$METRICS")"
echo ""

echo "--- Dispatch Summary ---"
grep "dispatch" "$METRICS" | wc -l | xargs -I{} echo "Total dispatches: {}"
grep "command_complete.*success" "$METRICS" | wc -l | xargs -I{} echo "Successes: {}"
grep "command_timeout" "$METRICS" | wc -l | xargs -I{} echo "Timeouts: {}"
grep "crash" "$METRICS" | wc -l | xargs -I{} echo "Crashes: {}"
echo ""

echo "--- Per-Project ---"
awk -F'|' '/dispatch/ {gsub(/^ +| +$/,"",$4); print $4}' "$METRICS" | sort | uniq -c | sort -rn
echo ""

echo "--- Recent Commands (last 20) ---"
grep "dispatch.*sent" "$METRICS" | tail -20 | awk -F'|' '{gsub(/^ +| +$/,"",$1); gsub(/^ +| +$/,"",$3); gsub(/^ +| +$/,"",$7); printf "%s %s %s\n", $1, $3, substr($7,1,60)}'
```

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
