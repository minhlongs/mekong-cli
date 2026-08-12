# Phase 08 — 01.08

**Date:** 260811 · **Status:** pending

## Task
Verify phase: Run full integration test suite. Execute mk auto with 5 real scenarios (deploy, rm, git-push-force, chi-tien, xoa-data). Validate gate blocks, resume works, budget enforced, checkpoints created. Confirm exit codes.

## Files


## Acceptance criteria

All 5 scenarios execute correctly; gates block appropriately; --resume restores state; --decision approves gates; no regressions in existing commands; performance <30s per scenario
