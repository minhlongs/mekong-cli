---
name: adversarial-review
description: Spawn a fresh-eyes subagent to adversarially critique code changes. Trigger when user says "review this", "check my work", "is this good?", or before merging any PR with 500+ lines changed. The review iterates until findings degrade to nitpicks. Based on Anthropic's internal adversarial-review pattern.
---

# Adversarial Review

## Overview
Spawns a SEPARATE subagent with no context from the current session. This fresh-eyes agent looks for issues the original author (human or AI) is blind to.

## Workflow

### Step 1: Collect the diff
```bash
git diff main..HEAD > /tmp/review-diff.txt
echo "Files changed: $(git diff --name-only main..HEAD | wc -l)"
echo "Lines changed: $(git diff --stat main..HEAD | tail -1)"
```

### Step 2: Spawn review subagent
Use Claude Code's subagent capability. The subagent gets ONLY:
- The diff
- The repo's CLAUDE.md
- This skill's review criteria

### Step 3: Review criteria
The subagent evaluates from 6 perspectives (from Mekong's ReviewAgent):
1. **Security** — injection, auth bypass, secret exposure
2. **Performance** — O(n^2) loops, memory leaks, blocking calls
3. **Correctness** — edge cases, off-by-one, null handling
4. **Maintainability** — naming, complexity, dead code
5. **Testing** — untested paths, flaky patterns, missing assertions
6. **Architecture** — coupling, abstraction level, separation of concerns

### Step 4: Iterate
- Implement fixes for CRITICAL and HIGH findings
- Re-run review
- Repeat until only NITPICK findings remain
- Log all findings to `data/review-log.jsonl`

## Scripts
- `scripts/collect-diff.sh` — Generate diff for review
- `scripts/format-review.sh` — Format review output as markdown table

## Gotchas
- The subagent must NOT have access to the current session's conversation. Fresh eyes only.
- Don't review generated code (package-lock.json, build artifacts). Filter with .gitignore.
- Security findings are auto-CRITICAL. Never downgrade to nitpick.
- Review log grows over time — valuable for identifying recurring patterns.
