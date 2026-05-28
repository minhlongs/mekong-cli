#!/bin/bash
# Re-trigger failed CI checks for a PR
# Usage: ./rerun-ci.sh <pr_number>

PR="${1:?Usage: $0 <pr_number>}"

echo "[babysit] Fetching failed checks for PR #$PR..."
FAILED=$(gh pr checks "$PR" --json name,conclusion \
  | python3 -c "import sys,json; checks=json.load(sys.stdin); [print(c['name']) for c in checks if c.get('conclusion')=='failure']" 2>/dev/null)

if [ -z "$FAILED" ]; then
    echo "[babysit] No failed checks found."
    exit 0
fi

echo "[babysit] Failed checks:"
echo "$FAILED"
echo "[babysit] Re-running CI via empty commit push..."

git commit --allow-empty -m "chore: re-trigger CI for PR #$PR"
git push

echo "[babysit] CI re-triggered. Monitor with: gh pr checks $PR --watch"
