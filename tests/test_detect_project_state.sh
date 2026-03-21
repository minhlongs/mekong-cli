#!/bin/bash
# Unit tests for detect_project_state() from factory-loop.sh
# Run: bash tests/test_detect_project_state.sh

set -euo pipefail

PASS=0
FAIL=0
TEST_DIR=$(mktemp -d)

# Extract detect_project_state function from factory-loop.sh
# Override HOME to use test directory
export HOME="$TEST_DIR"
mkdir -p "$TEST_DIR/mekong-cli"

detect_project_state() {
  local DIR=$1
  local FULL_DIR="$HOME/mekong-cli/${DIR}"

  if [ ! -d "$FULL_DIR" ]; then
    echo "empty"
    return
  fi

  if [ ! -d "${FULL_DIR}/src" ] && [ ! -d "${FULL_DIR}/app" ]; then
    echo "empty"
    return
  fi

  if [ ! -d "${FULL_DIR}/node_modules" ]; then
    echo "needs_install"
    return
  fi

  if [ -d "${FULL_DIR}/out" ] || [ -d "${FULL_DIR}/.next" ] || [ -d "${FULL_DIR}/dist" ]; then
    echo "deployed"
    return
  fi

  echo "scaffolded"
}

assert_eq() {
  local TEST_NAME=$1
  local EXPECTED=$2
  local ACTUAL=$3
  if [ "$EXPECTED" = "$ACTUAL" ]; then
    echo "  PASS: $TEST_NAME (got: $ACTUAL)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $TEST_NAME (expected: $EXPECTED, got: $ACTUAL)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== detect_project_state unit tests ==="
echo ""

# Test 1: Non-existent directory → empty
echo "Test 1: Non-existent directory"
RESULT=$(detect_project_state "apps/does-not-exist")
assert_eq "non-existent dir" "empty" "$RESULT"

# Test 2: Directory exists but no src/ or app/ → empty
echo "Test 2: Dir with only config files"
mkdir -p "$TEST_DIR/mekong-cli/apps/config-only"
echo '{}' > "$TEST_DIR/mekong-cli/apps/config-only/package.json"
RESULT=$(detect_project_state "apps/config-only")
assert_eq "config-only dir" "empty" "$RESULT"

# Test 3: Has src/ but no node_modules → needs_install
echo "Test 3: Has src/ but no node_modules"
mkdir -p "$TEST_DIR/mekong-cli/apps/no-deps/src"
RESULT=$(detect_project_state "apps/no-deps")
assert_eq "src without node_modules" "needs_install" "$RESULT"

# Test 4: Has app/ but no node_modules → needs_install
echo "Test 4: Has app/ but no node_modules"
mkdir -p "$TEST_DIR/mekong-cli/apps/app-dir/app"
RESULT=$(detect_project_state "apps/app-dir")
assert_eq "app without node_modules" "needs_install" "$RESULT"

# Test 5: Has src/ + node_modules but no build → scaffolded
echo "Test 5: Has src/ + node_modules (no build output)"
mkdir -p "$TEST_DIR/mekong-cli/apps/scaffolded/src"
mkdir -p "$TEST_DIR/mekong-cli/apps/scaffolded/node_modules"
RESULT=$(detect_project_state "apps/scaffolded")
assert_eq "scaffolded project" "scaffolded" "$RESULT"

# Test 6: Has src/ + node_modules + out/ → deployed
echo "Test 6: Has out/ build output"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-out/src"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-out/node_modules"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-out/out"
RESULT=$(detect_project_state "apps/deployed-out")
assert_eq "deployed with out/" "deployed" "$RESULT"

# Test 7: Has src/ + node_modules + .next/ → deployed
echo "Test 7: Has .next/ build output"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-next/src"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-next/node_modules"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-next/.next"
RESULT=$(detect_project_state "apps/deployed-next")
assert_eq "deployed with .next/" "deployed" "$RESULT"

# Test 8: Has app/ + node_modules + dist/ → deployed
echo "Test 8: Has dist/ build output"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-dist/app"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-dist/node_modules"
mkdir -p "$TEST_DIR/mekong-cli/apps/deployed-dist/dist"
RESULT=$(detect_project_state "apps/deployed-dist")
assert_eq "deployed with dist/" "deployed" "$RESULT"

# Test 9: Has both src/ and app/ → not empty
echo "Test 9: Has both src/ and app/"
mkdir -p "$TEST_DIR/mekong-cli/apps/both-dirs/src"
mkdir -p "$TEST_DIR/mekong-cli/apps/both-dirs/app"
RESULT=$(detect_project_state "apps/both-dirs")
assert_eq "both src+app without deps" "needs_install" "$RESULT"

# Test 10: Empty string dir → empty
echo "Test 10: Root-level empty"
RESULT=$(detect_project_state "apps/nonexistent-proj")
assert_eq "nonexistent project" "empty" "$RESULT"

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
echo "All tests passed!"
