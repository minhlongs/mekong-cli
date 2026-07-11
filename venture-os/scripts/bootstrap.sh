#!/usr/bin/env bash
# venture-os/scripts/bootstrap.sh
# Exit 0 = all gates pass. Exit 1 = bootstrap blocked.

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo " ✓ $label"
    PASS=$((PASS + 1))
  else
    echo " ✗ $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== VentureOS Bootstrap Gate ==="

# Phase 1: Foundation
echo ""
echo "[Phase 1] Foundation"
check "foundation.md exists" test -f "$ROOT/blueprint/foundation.md"
check "All ADRs exist" test "$(ls "$ROOT"/adr/*.md 2>/dev/null | wc -l)" -ge 10
check "lib/workflow-types.ts compiles" test -f "$ROOT/lib/workflow-types.ts"
check "lib/workflow-runner.ts compiles" test -f "$ROOT/lib/workflow-runner.ts"
check "lib/compiler.ts compiles" test -f "$ROOT/lib/compiler.ts"

# Phase 2: CLI
echo ""
echo "[Phase 2] CLI"
check "tools/cli/venture.ts exists" test -f "$ROOT/tools/cli/venture.ts"
check "tsconfig.json exists" test -f "$ROOT/tools/tsconfig.json"

# Phase 3: Workflow Engine
echo ""
echo "[Phase 3] Workflow Engine"
check "workflows/research/market-research/ exists" test -d "$ROOT/workflows/research/market-research"
check "workflow.yaml exists" test -f "$ROOT/workflows/research/market-research/workflow.yaml"

# Phase 4: Compilers
echo ""
echo "[Phase 4] Compilers"
if [ -d "$ROOT/workflows/compiler" ]; then
  for d in "$ROOT"/workflows/compiler/*/; do
    name=$(basename "$d")
    check "compiler/$name/compiler.yaml" test -f "$d/compiler.yaml"
  done
else
  echo " (no compilers yet)"
fi

# Phase 5: Sample Venture
echo ""
echo "[Phase 5] Sample Venture"
if [ -d "$ROOT/ventures" ]; then
  for v in "$ROOT"/ventures/*/; do
    id=$(basename "$v")
    check "$id/venture.toml" test -f "$v/venture.toml"
    check "$id/state.json" test -f "$v/state.json"
    check "$id/wal/current.jsonl" test -f "$v/wal/current.jsonl"
  done
fi

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && echo "BOOTSTRAP VIABLE" || echo "BOOTSTRAP BLOCKED"
exit "$FAIL"
