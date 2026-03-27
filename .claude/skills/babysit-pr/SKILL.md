---
name: babysit-pr
description: Monitor a GitHub PR through its lifecycle — retry flaky CI, resolve merge conflicts, enable auto-merge. Trigger when user says "babysit this PR", "watch this PR", "make sure this merges", or when a PR has been open for 2+ hours with failing CI. Based on Anthropic's babysit-pr pattern.
---

# Babysit PR

## Overview
Monitors a PR until it merges or needs human intervention. Handles the mechanical work of getting a PR through CI.

## Workflow

### Step 1: Assess PR state
```bash
PR_NUMBER=${1:-$(gh pr list --state open --json number -q '.[0].number')}
gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup,reviews
```

### Step 2: Handle CI failures
```bash
# Get failed checks
gh pr checks $PR_NUMBER --json name,state,conclusion \
  | jq '[.[] | select(.conclusion == "failure")]'
```

For each failure:
- If FLAKY (seen before in `data/flaky-tests.txt`): re-run CI
- If REAL failure: attempt fix → push → wait for CI
- If INFRA (timeout, OOM): re-run CI

### Step 3: Handle merge conflicts
```bash
git fetch origin main
git rebase origin/main
# If conflicts: resolve → force push → wait for CI
```

### Step 4: Enable auto-merge
```bash
gh pr merge $PR_NUMBER --auto --squash
```

### Step 5: Log result
Append to `data/pr-history.jsonl`:
```json
{"pr": 42, "attempts": 3, "flaky_reruns": 1, "conflict_resolved": true, "merged_at": "..."}
```

## Scripts
- `scripts/pr-status.sh <pr_number>` — One-line PR health summary
- `scripts/rerun-ci.sh <pr_number>` — Re-trigger failed CI checks
- `scripts/rebase-pr.sh <pr_number>` — Rebase on main and force push

## References
- `references/flaky-tests.md` — Known flaky tests and their patterns

## Gotchas
- Never force push to someone else's PR branch without permission.
- Flaky test detection: if a test passes on re-run without code changes, add it to flaky-tests.txt.
- Auto-merge needs branch protection rules that allow it. Check with `gh api repos/{owner}/{repo}/branches/main/protection`.
- Rate limit: `gh` CLI respects GitHub API limits. Don't poll faster than every 30 seconds.
