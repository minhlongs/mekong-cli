# Phase 01: Forensic Audit & P0 Execution Truth (`G0`–`G1`)

- **Status:** pending
- **Priority:** P1
- **Dependencies:** None

## Context & Requirements

Establish the forensic baseline audit report (`docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md`) and eliminate P0 false-positive execution truth defects (`H1`, `H2`, `H4`, `H5`, `H7`) across `GoalEngine`, `TaskGraph`, `VerificationPipeline`, and `MekongCoreRuntimeImpl`.

<!-- Updated: Validation Session 1 - RT-01 & RT-03 applied -->

## Affected Files

- `/Users/macbook/mekong-cli-autonomous-worktree/docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md` (create) — Forensic baseline of H1–H7 and `Governance.classify_risk()`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/models.py` (modify) — Add `ExecutionTruthStatus` (12 states), execution evidence fields on `TaskRecord` and `GoalRecord`, update `TaskGraph.ready_tasks()`, and add `TaskGraph.propagate_failures()`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/goal_engine/service.py` (modify) — Return `ExecutionOutcome` from `_execute_task()`, enforce `SIMULATED` vs `EXECUTION_FAILED` vs `VERIFIED_SUCCESS` in `run_goal()`, `run_goal_parallel()`, and `verify_goal()`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/mekongcli/core/verification/gates.py` (modify) — Expose `is_empty_profile` / gate count metadata so `verify_goal(profile="none")` never reports `ExecutionTruthStatus.VERIFIED_SUCCESS`.
- `/Users/macbook/mekong-cli-autonomous-worktree/src/core/runtime_adapter.py` (modify) — Add `commit_kind: Literal["runtime_state_commit", "git_commit"]` and `git_sha: str | None` to `CommitRecord` and `MekongCoreRuntimeImpl.commit()`.

## Implementation Steps

1. Create `docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md` documenting exact file/line evidence for H1–H7 and `Governance.classify_risk()`.
2. In `src/mekongcli/core/goal_engine/models.py`, define `ExecutionTruthStatus` (`PLANNED`, `SIMULATED`, `QUEUED`, `RUNNING`, `WAITING_APPROVAL`, `RETRY_WAIT`, `VERIFIED_SUCCESS`, `EXECUTION_FAILED`, `VERIFICATION_FAILED`, `BLOCKED`, `CANCELLED`, `UNAVAILABLE`) and add `truth_status`, `exit_code`, `stdout`, `stderr`, `blocked_reason`, `is_idempotent`, `side_effect_uncertain` to `TaskRecord` and `GoalRecord`.
3. Add `TaskGraph.propagate_failures()` in `models.py` so any failed/blocked upstream task transitions dependent `PENDING` tasks to `TaskStatus.BLOCKED` (`ExecutionTruthStatus.BLOCKED`).
4. Update `GoalEngine._execute_task()`, `run_goal()`, `run_goal_parallel()`, and `verify_goal()` in `service.py` to enforce the 5-column Compatibility Mapping.
5. Update `CommitRecord` and `MekongCoreRuntimeImpl.commit()` in `src/core/runtime_adapter.py` (`lines 1023-1034`) with `commit_kind` and `git_sha`.

## Validation & Gate

```bash
python3 -m pytest tests/mekongcli/test_goal_engine.py tests/test_core_lifecycle_contract.py -q
```
