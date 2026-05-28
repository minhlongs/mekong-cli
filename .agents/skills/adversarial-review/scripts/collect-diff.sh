#!/bin/bash
# Collect git diff for adversarial review
# Usage: ./collect-diff.sh [base-branch]
# Output: writes diff to /tmp/review-diff.txt

BASE="${1:-main}"
OUT="/tmp/review-diff.txt"

echo "[review] Collecting diff against $BASE..."

git diff "$BASE"..HEAD > "$OUT"

FILES=$(git diff --name-only "$BASE"..HEAD | wc -l)
STATS=$(git diff --stat "$BASE"..HEAD | tail -1)

echo "[review] Files changed: $FILES"
echo "[review] Stats: $STATS"
echo "[review] Diff saved to: $OUT"
