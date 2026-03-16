---
description: "Full CTO observability dashboard — telemetry, anomalies, dispatch health"
argument-hint: [--anomalies | --telemetry | --all]
allowed-tools: Bash
---

# /cto-observability — CTO Observability Dashboard

Full telemetry + anomaly detection in one view.

## Implementation

```bash
echo "=== CTO OBSERVABILITY DASHBOARD ==="
echo "$(date)"
echo ""

# 1. Anomaly detection
echo "--- Anomaly Status ---"
node -e "
  const ad = require('$HOME/mekong-cli/apps/openclaw-worker/lib/cto-anomaly-detector');
  const r = ad.detectAnomalies();
  const icon = r.severity === 'critical' ? '🚨' : r.severity === 'warn' ? '⚠️' : '✅';
  console.log(icon + ' Status: ' + r.severity.toUpperCase());
  if (r.anomalies.length === 0) {
    console.log('  No anomalies detected');
  } else {
    r.anomalies.forEach(a => {
      const sIcon = a.severity === 'critical' ? '🔴' : '🟡';
      console.log('  ' + sIcon + ' ' + a.type + ': ' + a.message);
    });
  }
" 2>/dev/null

echo ""

# 2. Telemetry
echo "--- Telemetry ---"
node -e "
  const t = require('$HOME/mekong-cli/apps/openclaw-worker/lib/cto-telemetry');
  const data = t.generateTelemetry();
  const s = data.summary;
  console.log('  Events: ' + s.totalEvents + ' | Dispatches: ' + s.dispatches + ' | Success: ' + s.successRate + '%');
  console.log('  Avg latency: ' + s.avgLatencySeconds + 's | Timeouts: ' + s.timeouts + ' | Crashes: ' + s.crashes + ' | Dedups: ' + s.dedups);
  console.log('');
  console.log('  Pane utilization:');
  for (const [pane, count] of Object.entries(data.paneUtilization)) {
    const bar = '#'.repeat(Math.min(count, 30));
    console.log('    ' + pane + ': ' + count + ' ' + bar);
  }
  console.log('');
  console.log('  Brain: ' + data.brain.commandsLearned + ' commands learned, ' + data.evolutions + ' evolution events');
  console.log('  Telemetry saved: /tmp/cto-telemetry.json');
" 2>/dev/null

echo ""

# 3. Factory status
echo "--- Factory Loop ---"
if [ -f /tmp/factory.pid ]; then
  PID=$(cat /tmp/factory.pid)
  kill -0 "$PID" 2>/dev/null && echo "  Status: RUNNING (PID $PID)" || echo "  Status: DEAD"
else
  echo "  Status: NOT RUNNING"
fi
if [ -f /tmp/factory-dispatch-history.log ]; then
  echo "  Dispatch history: $(wc -l < /tmp/factory-dispatch-history.log | xargs) entries"
fi
```

## Goal context

<goal>$ARGUMENTS</goal>
