# AGI Approval Gate — 2026-08-19

## Defect

`AGILoop._execute` spawned CC CLI sessions unconditionally. An unstarted,
unaudited loop could autonomously modify production code with no human
oversight — the #2 priority in `AUTONOMY_GAPS.md`.

## Fix

| File | Change |
|------|--------|
| `src/core/agi_loop.py` | Added `approval_mode` (default `"manual"`) and `_pending_approvals: set[str]` to `__init__`. Added `approve_improvement()`, `deny_improvement()`, `_approval_allowed()`. `_execute` now returns `None` (skip) instead of spawning when the improvement is unapproved; `run_forever` treats `None` as a silent skip that does not consume the consecutive-failure budget. `get_status()` exposes `approval_mode` and `pending_approvals`. |
| `src/core/telegram_agi.py` | Added `/agi approve <id>` and `/agi deny <id>` subcommands (`_agi_approve`, `_agi_deny`). Updated `_agi_config` to show `Approval mode` and `Pending approvals`. Updated usage string. |
| `tests/test_agi_loop.py` | `test_execute_no_prompt` asserts `None` (was `False`). `test_execute_success`/`test_execute_failure` now grant approval before calling `_execute`. Added `TestApprovalGate` — 12 tests: default mode, manual denies unapproved, manual allows approved, auto mode bypasses, approve/deny edge cases, status fields. |

## Verification

- `tests/test_agi_loop.py`: **34 passed** (was 22; +12)
- `ruff check src/core/agi_loop.py src/core/telegram_agi.py tests/test_agi_loop.py`: clean
- CI-gated subset (`tests/core tests/cli tests/seed tests/commands tests/auth tests/unit tests/daemon tests/vn`): running in background — target 2242 passed, 0 failed (baseline)

## Design notes

- Default-safe: a loop that has never been audited can never spawn CC CLI on
  its own. `approval_mode = "auto"` opt-in for unattended runs.
- A refusal is a *skip*, not a failure — the loop keeps assessing instead of
  burning its consecutive-failure budget on work it was never allowed to run.
- Telegram is the zero-friction path: `/agi start` → `/agi approve <id>`.

## Status

Verified, not committed.