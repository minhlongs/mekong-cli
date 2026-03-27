#!/bin/bash
# Rebase current branch on main and force push
# Usage: ./rebase-pr.sh [base-branch]

BASE="${1:-main}"

echo "[babysit] Fetching latest $BASE..."
git fetch origin "$BASE"

echo "[babysit] Rebasing on origin/$BASE..."
if git rebase "origin/$BASE"; then
    echo "[babysit] Rebase successful. Force pushing..."
    git push --force-with-lease
    echo "[babysit] Done. CI will re-run."
else
    echo "[babysit] Rebase has conflicts. Resolve manually:" >&2
    echo "  git status" >&2
    echo "  # fix conflicts" >&2
    echo "  git add ." >&2
    echo "  git rebase --continue" >&2
    exit 1
fi
