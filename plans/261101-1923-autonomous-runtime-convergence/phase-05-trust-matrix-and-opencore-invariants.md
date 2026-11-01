# Phase 05: Trust Matrix (`T01`–`T20`) & Open-Core Invariants (`G7`–`G9`)

- **Status:** pending
- **Priority:** P1
- **Dependencies:** Phase 04

## Context & Requirements

Implement the full 20-scenario deterministic integration test suite (`T01`–`T20`) in `tests/test_autonomous_runtime_trust_matrix.py`, verify all Open-Core and RaaS boundary invariants (`0`-byte diff on `phase_559_opencore_25_step_catalog.py`, `<= 185 LOC` across `src/core/opencore/` and `src/core/raas_license_verifier.py`), and finalize the forensic audit report in `docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md`.

## Affected Files

- `/Users/macbook/mekong-cli-autonomous-worktree/tests/test_autonomous_runtime_trust_matrix.py` (create) — Deterministic test suite covering all 20 scenarios (`T01`–`T20`).
- `/Users/macbook/mekong-cli-autonomous-worktree/docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md` (modify) — Record final verification evidence, test pass counts, and Open-Core invariant checks.

## Implementation Steps

1. Create `tests/test_autonomous_runtime_trust_matrix.py` with 20 deterministic tests:
   - `T01`: `execute_commands=False` -> `SIMULATED`, never `VERIFIED_SUCCESS`.
   - `T02`: Non-zero exit code -> `EXECUTION_FAILED` (`TaskStatus.FAILED`), never `COMPLETED`.
   - `T03`: Blocked/sanitized command (`exit_code=126`) -> `EXECUTION_FAILED` / `BLOCKED` with `blocked_reason`.
   - `T04`: Parallel worker uncaught exception -> `EXECUTION_FAILED`, goal fails cleanly.
   - `T05`: Upstream task failure -> downstream `depends_on` tasks transition to `BLOCKED` and never execute.
   - `T06`: `verification_profile="none"` -> never reports `VERIFIED_SUCCESS`.
   - `T07`: `MekongCoreRuntimeImpl.commit()` without Git commit -> `commit_kind="runtime_state_commit"`, `git_sha=None`.
   - `T08`: Duplicate `(source_id, event_id)` ticket intake -> deduplicated idempotently in `SQLiteGoalStore`.
   - `T09`: Worker attempt to mutate `ImmutableMandate` (`authorized_scope`, `permitted_capabilities`, `cost_budget`) -> rejected by `SQLiteGoalStore` & `verify_mandate_integrity()`.
   - `T10`: Unknown/malformed risk level in `Governance.classify_risk()` -> `ActionClass.FORBIDDEN` (fail-closed).
   - `T11`: Untrusted content (`untrusted_context=True`, e.g., issue comment prompt injection) requesting capability escalation -> `PolicyDecision.decision == "DENY"`.
   - `T12`: Destructive capability without approval token -> `APPROVAL_REQUIRED`; with tampered or replayed token -> `DENY`; with valid first-use payload-bound token -> `ALLOW`.
   - `T13`: Orphaned `RUNNING` task after expired lease (`is_idempotent=True`, within `retry_budget`) -> recovered to `PENDING` (`RETRY_WAIT`) and re-executed on `resume_goal()`.
   - `T14`: Orphaned `RUNNING` task after expired lease (`is_idempotent=False` or `side_effect_uncertain=True`) -> moved to `BLOCKED` (`WAITING_APPROVAL`), never blindly re-executed.
   - `T15`: Outbound status report via `BuzzAdapter` / `report_outbox` -> persisted transactionally, deduplicated by `idempotency_key`, and transitions to `DEAD_LETTER` after `max_attempts`.
   - `T16`: Autonomous worker concurrency cap -> 3rd concurrent autonomous task queues while 2 autonomous leases are active.
   - `T17`: Reserved `OPERATOR_CONTROL` lane -> executes immediately (`status`/`cancel`/`approve`) while 2 autonomous workers are saturated.
   - `T18`: Concurrent write workers in `WorktreeIsolationManager` -> isolated in separate `.mekong/worktrees/<ticket_id>_<task_id>` directories and deterministically cleaned up on completion/failure.
   - `T19`: Path escape attempt (`../outside`) inside isolated worktree -> rejected by `WorktreeIsolationManager` / `LocalExecutor`.
   - `T20`: Unmeasured provider/local execution cost -> recorded with `actual_cost=None` and `cost_status="UNKNOWN"` (never `0.0`), while budget exhaustion blocks further task execution.
2. Run full verification suites and update `docs/audits/MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01.md`.

## Validation & Gate

```bash
python3 -m pytest tests/test_autonomous_runtime_trust_matrix.py tests/test_core_lifecycle_contract.py tests/test_core_boundary.py tests/test_opencore_saas_25_step_suite.py -q
python3 -m ruff check src/core/opencore/ src/mekongcli/core/goal_engine/ src/core/governance.py tests/test_autonomous_runtime_trust_matrix.py
```
