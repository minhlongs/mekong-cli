# Phase 04: Worktree Isolation, 2+1 Worker Lanes & Honest Cost Accounting (`G5` & `G6`)

- **Status:** pending
- **Priority:** P1
- **Dependencies:** Phase 03

## Context & Requirements

Enforce bounded worker concurrency (`max_autonomous_workers=2` plus `1` reserved `OPERATOR_CONTROL` lane), isolate concurrent write tasks using managed Git worktrees under `.mekong/worktrees/<ticket_id>_<task_id>` with deterministic cleanup and `CommandSanitizer(strict_mode=True)`, separate `ModelProposal` from host policy authorization, and enforce honest cost accounting (`cost_status="UNKNOWN"` when unmeasured).

<!-- Updated: Validation Session 1 - RT-01 & RT-04 applied -->

## Affected Files

- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/worktree_manager.py` (create) — Implement `WorktreeIsolationManager` creating and deterministically cleaning up `.mekong/worktrees/<ticket_id>_<task_id>` worktrees and rejecting path escapes outside `worktree_path`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/execution/local_executor.py` (modify) — Default `strict_mode: bool = True` in `LocalExecutor.__init__()` (`line 43`) and validate working directory boundaries.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/service.py` (modify) — Cap autonomous concurrency at `max_autonomous_workers=2`, reserve `1` `OPERATOR_CONTROL` lane (`run_operator_control_action()`), and isolate parallel write tasks via `WorktreeIsolationManager`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/opc/usage.py` (modify) — Add explicit `measured_tokens`, `estimated_tokens`, `actual_cost`, `estimated_cost`, and `cost_status: Literal["MEASURED", "ESTIMATED", "UNKNOWN"]` fields without fabricating `actual_cost = 0.0` on unmeasured runs.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/core/runtime_adapter.py` (modify) — Add `ModelProposal` gating so model-proposed tool/command invocations pass through host `Governance.evaluate_ticket_action()` and budget checks before execution.

## Implementation Steps

1. Create `src/mekongcli/core/goal_engine/worktree_manager.py` with `WorktreeIsolationManager` supporting `allocate(ticket_id, task_id)`, `validate_path_within_worktree(worktree_path, target_path)`, and `cleanup(worktree_path)` (`git worktree remove --force` + fallback directory removal). Note explicitly in module docstring that Git worktrees provide workspace filesystem isolation, not OS/kernel container sandboxing.
2. Update `src/mekongcli/core/execution/local_executor.py:43` so `CommandSanitizer(strict_mode=True)` is active by default and `LocalExecutor` rejects commands attempting path traversal outside an isolated worktree.
3. Update `GoalEngine.run_goal_parallel()` in `src/mekongcli/core/goal_engine/service.py` to enforce `max_autonomous_workers=2` via `SQLiteGoalStore` worker leases, provide `execute_operator_lane()` on the reserved `OPERATOR_CONTROL` lane so operator commands never starve when 2 autonomous workers are busy, and run concurrent write tasks inside isolated worktrees with `try...finally` cleanup.
4. Update `src/opc/usage.py` and `SQLiteGoalStore` cost accounting to record `measured_tokens`, `estimated_tokens`, `actual_cost`, `estimated_cost`, and `cost_status` (`"MEASURED" | "ESTIMATED" | "UNKNOWN"`).

## Validation & Gate

```bash
python3 -m pytest tests/mekongcli/test_goal_engine.py tests/test_opc_platform_contract.py -q
```
