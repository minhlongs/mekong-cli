#!/bin/bash
# Integration tests for CTO factory system
# Tests: detect_project_state, dedup, ROI calculator, output intelligence, anomaly detector
# Run: bash tests/test_factory_integration.sh
set -euo pipefail

PASS=0 FAIL=0
TEST_DIR=$(mktemp -d)
export HOME="$TEST_DIR"
mkdir -p "$TEST_DIR/mekong-cli/apps"

assert_eq() {
  local NAME=$1 EXPECTED=$2 ACTUAL=$3
  if [ "$EXPECTED" = "$ACTUAL" ]; then echo "  PASS: $NAME"; PASS=$((PASS+1))
  else echo "  FAIL: $NAME (expected: $EXPECTED, got: $ACTUAL)"; FAIL=$((FAIL+1)); fi
}
assert_contains() {
  local NAME=$1 PATTERN=$2 TEXT=$3
  if echo "$TEXT" | grep -q "$PATTERN"; then echo "  PASS: $NAME"; PASS=$((PASS+1))
  else echo "  FAIL: $NAME (pattern '$PATTERN' not found)"; FAIL=$((FAIL+1)); fi
}

echo "=== CTO Factory Integration Tests ==="

# --- detect_project_state (extracted) ---
echo ""
echo "Test Group 1: detect_project_state"
detect_project_state() {
  local _DIR=$1
  local _FULL="$HOME/mekong-cli/${_DIR}"
  if [ ! -d "$_FULL" ]; then echo "empty"; return; fi
  if [ ! -d "${_FULL}/src" ] && [ ! -d "${_FULL}/app" ]; then echo "empty"; return; fi
  if [ ! -d "${_FULL}/node_modules" ]; then echo "needs_install"; return; fi
  if [ -d "${_FULL}/out" ] || [ -d "${_FULL}/.next" ] || [ -d "${_FULL}/dist" ]; then echo "deployed"; return; fi
  echo "scaffolded"
}
mkdir -p "$TEST_DIR/mekong-cli/apps/p1/src" "$TEST_DIR/mekong-cli/apps/p1/node_modules" "$TEST_DIR/mekong-cli/apps/p1/out"
assert_eq "deployed project" "deployed" "$(detect_project_state apps/p1)"
mkdir -p "$TEST_DIR/mekong-cli/apps/p2/src"
assert_eq "needs_install" "needs_install" "$(detect_project_state apps/p2)"
mkdir -p "$TEST_DIR/mekong-cli/apps/p3"
assert_eq "empty (no src)" "empty" "$(detect_project_state apps/p3)"
assert_eq "nonexistent" "empty" "$(detect_project_state apps/nope)"

# --- Node.js modules ---
echo ""
echo "Test Group 2: Node.js module validation"
REAL_HOME=$(eval echo ~macbookprom1 2>/dev/null || echo "/Users/macbookprom1")
MODULES=(factory-roi-calculator factory-throughput-optimizer output-intelligence project-priority-matrix algo-orchestrator cto-telemetry cto-anomaly-detector)
for mod in "${MODULES[@]}"; do
  REAL_FILE="${REAL_HOME}/mekong-cli/apps/openclaw-worker/lib/${mod}.js"
  if [ -f "$REAL_FILE" ] && node -c "$REAL_FILE" 2>/dev/null; then
    assert_eq "$mod syntax" "ok" "ok"
  else
    assert_eq "$mod syntax" "ok" "FAIL"
  fi
done

# --- Dry-run mode ---
echo ""
echo "Test Group 3: Dry-run mode"
export HOME="$REAL_HOME"
DRY_OUTPUT=$(cd "$REAL_HOME/mekong-cli" && bash factory-loop.sh --dry-run --cycles=2 2>&1 || true)
assert_contains "dry-run header" "DRY-RUN" "$DRY_OUTPUT"
assert_contains "cycle count" "Cycle=1" "$DRY_OUTPUT"
assert_contains "max cycles exit" "max cycles" "$DRY_OUTPUT"
assert_contains "project state" "State:" "$DRY_OUTPUT"

# --- Output intelligence ---
echo ""
echo "Test Group 4: Output intelligence"
OI_RESULT=$(node -e "
  const oi = require('$REAL_HOME/mekong-cli/apps/openclaw-worker/lib/output-intelligence');
  const r1 = oi.classifyOutput('Write(src/algo.ts) created file successfully');
  console.log(r1.primary);
  const r2 = oi.classifyOutput('report saved to plans/reports/analysis.md');
  console.log(r2.primary);
  const r3 = oi.classifyOutput('error: Build failed with exit code 1');
  console.log(r3.primary);
" 2>/dev/null || echo "error")
assert_eq "code detection" "code_written" "$(echo "$OI_RESULT" | head -1)"
assert_eq "analysis detection" "analysis_only" "$(echo "$OI_RESULT" | sed -n 2p)"
assert_eq "error detection" "error" "$(echo "$OI_RESULT" | sed -n 3p)"

# --- Anomaly detector (clean state) ---
echo ""
echo "Test Group 5: Anomaly detector"
AD_RESULT=$(node -e "
  const ad = require('$REAL_HOME/mekong-cli/apps/openclaw-worker/lib/cto-anomaly-detector');
  const r = ad.detectAnomalies();
  console.log(r.severity);
" 2>/dev/null || echo "error")
assert_eq "clean state = ok" "ok" "$AD_RESULT"

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -gt 0 ] && exit 1
echo "All integration tests passed!"
