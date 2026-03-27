#!/bin/bash
# Verify last git commit matches expectations
# Usage: ./verify-git.sh [expected-message-substring]

set -e

LAST_COMMIT=$(git log --oneline -1)
LAST_FILES=$(git diff --name-only HEAD~1 2>/dev/null || echo "(initial commit)")
REMOTE_HEAD=$(git log --remotes --oneline -1 2>/dev/null || echo "(no remote)")
LOCAL_HEAD=$(git log --oneline -1)

echo "[git] Last commit: $LAST_COMMIT"
echo "[git] Files changed:"
echo "$LAST_FILES" | head -20
echo "[git] Local HEAD:  $LOCAL_HEAD"
echo "[git] Remote HEAD: $REMOTE_HEAD"

if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
    echo "[WARN] Local and remote HEAD differ — push may be pending" >&2
fi

if [ -n "$1" ]; then
    if echo "$LAST_COMMIT" | grep -qi "$1"; then
        echo "[OK] Commit message contains '$1'"
    else
        echo "[FAIL] Commit message does NOT contain '$1'" >&2
        exit 1
    fi
fi
