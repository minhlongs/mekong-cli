#!/usr/bin/env bash
# verify-install.sh — Smoke-test installed mekong binary.
set -euo pipefail

if ! command -v mekong >/dev/null 2>&1; then
  echo "FAIL: mekong not in PATH"
  exit 1
fi

ver=$(mekong --version 2>&1 || true)
echo "mekong --version -> $ver"

if ! echo "$ver" | grep -qE '[0-9]+\.[0-9]+\.[0-9]+'; then
  echo "FAIL: version format invalid"
  exit 1
fi

mekong help >/dev/null 2>&1 || true

echo "PASS: install smoke-test"
