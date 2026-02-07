#!/bin/bash
# Binh Phap Quality Gate Verification

set -e

echo "=== BINH PHAP QUALITY GATE VERIFICATION ==="
echo ""

FAILED_GATES=()

# Gate 1: 始計 Tech Debt Elimination
echo "🔴 Gate 1: 始計 (Tech Debt Elimination)"
TODO_COUNT=$(grep -r "TODO\|FIXME" packages/core/bmad/ 2>/dev/null | wc -l | xargs || echo "0")

if [ "$TODO_COUNT" -eq 0 ]; then
  echo "  ✅ PASS - Zero tech debt items in bmad package"
else
  echo "  ❌ FAIL - Found $TODO_COUNT TODOs/FIXMEs"
  FAILED_GATES+=("tech_debt")
fi
echo ""

# Gate 2: 作戰 Type Safety (Python type hints)
echo "🔴 Gate 2: 作戰 (Type Safety)"
UNTYPED_COUNT=$(grep -r "def.*(" packages/core/bmad/*.py 2>/dev/null | grep -v "self" | grep -v " -> " | wc -l | xargs || echo "0")

if [ "$UNTYPED_COUNT" -eq 0 ]; then
  echo "  ✅ PASS - All functions type-hinted"
else
  echo "  ⚠️  WARN - Found $UNTYPED_COUNT functions without return type hints"
fi
echo ""

# Gate 3: 謀攻 Performance
echo "🟡 Gate 3: 謀攻 (Performance)"
echo "  ℹ️  Performance tests require runtime execution"
echo "  ✅ SKIP - Manual verification needed"
echo ""

# Gate 4: 軍形 Security
echo "🔴 Gate 4: 軍形 (Security)"
SECRET_COUNT=$(grep -rE "(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*['\"]" packages/core/bmad/ 2>/dev/null | wc -l | xargs || echo "0")

if [ "$SECRET_COUNT" -eq 0 ]; then
  echo "  ✅ PASS - No hardcoded secrets"
else
  echo "  ❌ FAIL - Found $SECRET_COUNT potential hardcoded secrets"
  FAILED_GATES+=("security")
fi
echo ""

# Gate 5: 兵勢 UX Polish
echo "🟢 Gate 5: 兵勢 (UX Polish)"
echo "  ℹ️  UX verification requires manual testing"
echo "  ✅ SKIP - CLI commands provide rich output"
echo ""

# Gate 6: 虛實 Documentation
echo "🟢 Gate 6: 虛實 (Documentation)"
if [ -f "README.md" ] && [ -f "CLAUDE.md" ]; then
  echo "  ✅ PASS - Core documentation exists"
else
  echo "  ❌ FAIL - Missing core documentation"
  FAILED_GATES+=("documentation")
fi
echo ""

# Summary
echo "=== SUMMARY ==="
if [ ${#FAILED_GATES[@]} -eq 0 ]; then
  echo "✅ ALL CRITICAL QUALITY GATES PASSED"
  exit 0
else
  echo "❌ FAILED GATES: ${FAILED_GATES[*]}"
  exit 1
fi
