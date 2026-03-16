---
description: "Run all CTO factory tests — unit + integration + dry-run as health check"
argument-hint: [--verbose]
allowed-tools: Bash
---

# /cto-selftest — CTO System Health Check

Runs all test suites for the factory system.

## Implementation

```bash
echo "=== CTO SELF-TEST ==="
echo ""
TOTAL_PASS=0 TOTAL_FAIL=0

echo "--- Unit Tests (detect_project_state) ---"
bash tests/test_detect_project_state.sh 2>&1 | tail -3

echo ""
echo "--- Integration Tests ---"
bash tests/test_factory_integration.sh 2>&1 | tail -3

echo ""
echo "--- Syntax Checks ---"
bash -n factory-loop.sh && echo "  factory-loop.sh: OK" || echo "  factory-loop.sh: FAIL"
bash -n factory-watchdog.sh && echo "  factory-watchdog.sh: OK" || echo "  factory-watchdog.sh: FAIL"
for f in factory-roi-calculator factory-throughput-optimizer output-intelligence project-priority-matrix algo-orchestrator cto-telemetry cto-anomaly-detector; do
  node -c apps/openclaw-worker/lib/$f.js 2>/dev/null && echo "  $f.js: OK" || echo "  $f.js: FAIL"
done

echo ""
echo "=== SELF-TEST COMPLETE ==="
```

## Goal context

<goal>$ARGUMENTS</goal>
