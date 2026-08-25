# Ship Report — Wave 2 Masked Import Fixes

## Summary

Defect 4 (masked broken imports) fixed and shipped via PR #5.

- PR: https://github.com/minhlongs/mekong-cli/pull/5
- Branch: feat/wave2-masked-imports
- Commit on branch: 77b0c77e4
- Squash merge SHA: 0365918f57411f787e02595233f69be3eba064ea
- Result gate: CONDITIONAL PASS Round 1 — all 8 conditions verified independently by suntzu; 1 LOW informational finding (comment clarity at agi_bridge.py:52) escrowed as W2-E2
- Deploy: none (CLI/library repo)

## Code shipped

1. `src/command_fabric/router.py` — imports TUI router via real module path `src.cli.tui.router`; module now importable.
2. `src/cli/commands/implement/__init__.py` — `SQLiteGoalStore` imported from canonical `src.mekongcli.core.goal_engine`.
3. `src/agents/agi_bridge.py` — `start()` raises FileNotFoundError naming the missing `apps/openclaw-worker/task-watcher.js` instead of silent False; OSError wrapped as RuntimeError.
4. `src/commands/agi.py` — consumer exits code 1 on FileNotFoundError/RuntimeError and respects the bool return (immediate-exit case reports failure).
5. `tests/test_wave2_import_fixes.py` — NEW: 7 real-behavior tests (importability, canonical class identity, fail-loud with named script, consumer contract), CWD-independent via `_REPO_ROOT` anchor.

## Verification

- Targeted: tests/test_wave2_import_fixes.py → 7 passed (run independently post-merge on main)
- Full parity: 223 failed / 7576 passed / 75 skipped — normalized fail-set diff vs frozen baseline = 0 new failures, 0 green flips
- ruff: All checks passed
- Acceptance one-liners re-run post-merge: router import OK, implement import OK, AGIBridge fail-loud OK

## Execution notes

- Executor follow-ups during EXECUTE: (1) agi.py error-path fall-through + discarded bool return caught by main-agent verify and fixed; (2) new test file added per plan commitment; (3) CWD-relative path in new test broke in full suite — anchored to `_REPO_ROOT`, verified in chdir-prone combination runs.
- First full run showed 225 failed → investigated both deltas: one was the executor test's relative path (fixed), one was pre-existing order-dependent browser_agent flaky (did not recur in rerun).

## CI status

Post-merge failures are the identical set that failed at the Wave 1 merge commit 9b61cf3d7 (verified side-by-side): CI/pnpm-lock.yaml missing, Test Suite lint step, Command Fabric Release Gate, Factory Integrity, Nhịp Điệu Xanh, AI-Native 5 Gates, Quality Gates. Security Hardening & Attestation was in progress at check time. No new gate red attributable to this PR.

## Escrow / follow-up

1. W2-E2 (LOW): clarify misleading comment at src/agents/agi_bridge.py:52 about FileNotFoundError re-raise scope.
2. Pre-existing repo debt unchanged: pnpm-lock.yaml missing and related workflow drift.

## Verdict

GREEN for Wave 2 scope: PR merged, exact parity preserved, protected flows untouched, real tests added and green, ruff clean.
