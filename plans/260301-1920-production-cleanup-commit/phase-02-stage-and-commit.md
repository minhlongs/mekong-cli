---
phase: 2
title: "Stage and commit all changes"
status: pending
priority: P1
---

# Phase 02: Stage and Commit

## Context
- [Plan](plan.md)
- [Phase 01](phase-01-verify-gitignore-coverage.md)

## Overview
Stage all changes with `git add -A`, commit with 'chore: cleanup', verify clean tree.

## Files to Stage (37 total)
**Modified (28):** Runtime state (.mekong/, .antigravity/, openclaw-worker/data/), algo-trader refactors (BacktestEngine, BotEngine, CLI commands, plugins), sophia-proposal layout, CI workflow, package.json

**Untracked (9):** New algo-trader modules (backtest metrics/types, CLI commands, bot engine types/factories/executor), openclaw google-intel, security audit plan

## Implementation Steps
1. `git add -A` — stage everything
2. `git status` — verify staged files, no secrets
3. `git commit -m 'chore: cleanup — sync runtime state + add algo-trader modules'`
4. `git status` — confirm clean working tree

## Todo
- [ ] git add -A
- [ ] Verify no secrets staged
- [ ] git commit
- [ ] Confirm clean tree

## Success Criteria
- `git status` shows "nothing to commit, working tree clean"
- No .env or API keys committed
