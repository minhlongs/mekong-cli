#!/bin/bash
# Compare main vs master for branch divergence
# Usage: ./compare-branches.sh

echo "[daemon] Branch Divergence Check"
echo "================================="

MAIN_EXISTS=$(git rev-parse --verify main 2>/dev/null && echo "yes" || echo "no")
MASTER_EXISTS=$(git rev-parse --verify master 2>/dev/null && echo "yes" || echo "no")

echo "[daemon] main branch: $MAIN_EXISTS"
echo "[daemon] master branch: $MASTER_EXISTS"

if [ "$MAIN_EXISTS" = "yes" ] && [ "$MASTER_EXISTS" = "yes" ]; then
    AHEAD=$(git log --oneline main..master | wc -l)
    BEHIND=$(git log --oneline master..main | wc -l)
    echo "[daemon] master is $AHEAD commits ahead, $BEHIND commits behind main"

    if [ "$BEHIND" -gt 0 ]; then
        echo "[daemon] WARNING: master is missing $BEHIND commits from main" >&2
        echo "[daemon] Missing commits:"
        git log --oneline master..main | head -10
    fi
else
    echo "[daemon] Only one branch exists — no divergence possible"
fi
