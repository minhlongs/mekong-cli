---
name: ck:babysit-pr
description: "Monitor a GitHub PR through its lifecycle — retry flaky CI, resolve merge conflicts, enable auto-merge. Trigger when user says 'babysit this PR', 'watch this PR', 'make sure this merges', or when a PR has been open for 2+ hours with failing CI. Based on Anthropic's babysit-pr pattern."
user-invocable: true
when_to_use: "Invoke for PR CI follow-up, merge conflict resolution, or auto-merge setup."
category: dev-tools
keywords: [pr, github, ci, merge, auto-merge, babysit, watch-pr, flaky-ci]
argument-hint: "<PR number or URL>"
metadata:
  author: claudekit
  version: "1.0.0"
---

# Babysit PR

## Overview
Monitors a PR until it merges or needs human intervention. Handles the mechanical work of getting a PR through CI: retrying flaky checks, resolving merge conflicts, and enabling auto-merge.

## Usage

```
/ck:babysit-pr <PR number or URL>
```

If no PR is specified, defaults to the most recent open PR on the current branch.

## Workflow

### Step 1: Assess PR state

```bash
PR_NUMBER=${1:-$(gh pr list --state open --json number -q '.[0].number')}
gh pr view $PR_NUMBER --json state,mergeable,statusCheckRollup,reviews,headRefName,baseRefName
```

Check:
- `mergeable` — `MERGEABLE`, `CONFLICTING`, or `UNKNOWN`
- `statusCheckRollup` — each check's `state` and `conclusion`
- `reviews` — any blocking approvals

### Step 2: Handle CI failures

```bash
# Get failed checks
gh pr checks $PR_NUMBER --json name,state,conclusion \
| jq '[.[] | select(.conclusion == "failure")]'
```

For each failure:

| Type | Detection | Action |
|------|-----------|--------|
| **Flaky** | Seen before in `data/flaky-tests.txt` or passes on re-run without code changes | Re-run CI via `gh pr checks $PR_NUMBER --rerun` |
| **Real** | Consistent failure, error message points to code | Fix → commit → push → wait for CI |
| **Infra** | Timeout, OOM, runner unavailable | Re-run CI; if persists, notify user |

**ClaudeKit gh CLI references:**
```bash
# Re-run all failed checks
gh pr checks <PR> --rerun

# Re-run a specific check
gh pr checks <PR> --rerun "Check Name"

# Watch checks until completion (poll every 30s)
gh pr checks <PR> --watch --interval 30

# Get detailed check runs
gh api repos/{owner}/{repo}/check-runs --paginate -f per_page=100 \
  -f check_run_id=<run_id>
```

### Step 3: Handle merge conflicts

```bash
git fetch origin main
git rebase origin/main
# If conflicts: resolve → force push → wait for CI
```

**ClaudeKit gh CLI references:**
```bash
# Check if PR has conflicts without fetching
gh pr view <PR> --json mergeable,mergeStateStatus

# Get conflicting files
gh api repos/{owner}/{repo}/pulls/<PR>/conflicts --paginate

# After resolving and force-pushing, update the PR
gh pr checks <PR> --watch
```

**Gotcha:** Never force push to someone else's PR branch without explicit permission. If the PR is from a fork, you cannot push directly — ask the PR author to rebase.

### Step 4: Enable auto-merge

```bash
gh pr merge <PR_NUMBER> --auto --squash
```

**ClaudeKit gh CLI references:**
```bash
# Enable auto-merge with specific method
gh pr merge <PR> --auto --squash   # squash merge (default)
gh pr merge <PR> --auto --merge    # regular merge
gh pr merge <PR> --auto --rebase   # rebase merge

# Check branch protection rules (auto-merge requires admin allowance)
gh api repos/{owner}/{repo}/branches/main/protection \
  | jq '.required_status_checks'

# Disable auto-merge if conditions change
gh pr merge <PR> --disable-auto
```

### Step 5: Log result

Append to `data/pr-history.jsonl`:
```json
{"pr": 42, "attempts": 3, "flaky_reruns": 1, "conflict_resolved": true, "merged_at": "2026-06-30T10:00:00Z"}
```

## Sophia-Specific Context

When babysitting PRs for Sophia AI Factory repos:

- **Primary repo:** `billwill/sophia-ai-factory`
- **CI checks to watch:** `build`, `type-check`, `lint`, `test`, `secrets-audit`
- **Deploy verification:** After merge, run `npm run deploy:verify` from `apps/sophia-ai-factory/` to confirm SHA match
- **Protected flows:** Never modify code in Setup Wizard, Telegram Bot, or Payment Flow paths without explicit validation
- **Quality gates:** `npm run build` must pass with 0 TypeScript errors; `npm test` must pass all 844+ tests

```bash
# Sophia-specific: verify deploy after merge
cd apps/sophia-ai-factory
npm run deploy:verify

# Check version SHA match
LOCAL_SHA=$(git rev-parse HEAD | cut -c1-8)
LIVE_SHA=$(curl -s https://sophia.agencyos.network/api/version \
  | grep -o '"shortSha":"[^"]*"' | cut -d'"' -f4)
```

## Scripts

- `scripts/pr-status.sh <pr_number>` — One-line PR health summary
- `scripts/rerun-ci.sh <pr_number>` — Re-trigger failed CI checks
- `scripts/rebase-pr.sh <pr_number>` — Rebase on main and force push

## References

- `references/flaky-tests.md` — Known flaky tests and their patterns
- `references/gh-cli-pr.md` — GitHub CLI PR operations reference

## Gotchas

- Never force push to someone else's PR branch without permission.
- Flaky test detection: if a test passes on re-run without code changes, add it to `data/flaky-tests.txt`.
- Auto-merge needs branch protection rules that allow it. Check with `gh api repos/{owner}/{repo}/branches/main/protection`.
- Rate limit: `gh` CLI respects GitHub API limits. Don't poll faster than every 30 seconds.
- For PRs from forks, you cannot push directly — the fork author must rebase.
- `gh pr checks --watch` exits when all checks complete (success or failure), making it ideal for blocking waits.
