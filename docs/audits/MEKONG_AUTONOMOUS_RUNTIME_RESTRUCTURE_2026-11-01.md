# MEKONG CLI — AUTONOMOUS RUNTIME CONVERGENCE & EXECUTION TRUTH AUDIT (2026-11-01)

- **Document ID:** `MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01`
- **Issue:** [#121](https://github.com/longtho638-jpg/mekong-cli/issues/121) — *Supreme Command #01: Mekong CLI Autonomous Runtime Convergence & Execution Truth (H1–H7)*
- **Branch:** `feat/autonomous-runtime-convergence`
- **Status:** `VERIFIED_SUCCESS` (202 passed across Open-Core boundary gate, GoalEngine, Core Lifecycle, Buzz Outbox, Governance, OPC Security, and T01–T20 Trust Matrix; `ruff check` 0 errors)

---

## 1. Executive Summary

This restructuring converges Mekong CLI's autonomous runtime spine (`GoalEngine`, `SQLiteGoalStore`, `MekongCoreRuntimeImpl`, `LocalExecutor`, `Governance`, `BuzzAdapter`, and `UsageLedger`) around **Execution Truth** and **Unified SQLite WAL Persistence** while preserving 100% of Mekong CLI's Python-first, local-first identity and Open-Core/RaaS invariants (`phase_559_opencore_25_step_catalog.py` untouched byte-for-byte; all `src/core/opencore/` and `src/opc/` modules `<= 185 LOC`).

Seven execution-truth hazards (`H1`–`H7`) identified in the baseline audit have been eliminated and locked behind the deterministic 20-scenario **Autonomous Runtime Trust Matrix (`tests/test_autonomous_runtime_trust_matrix.py`, `T01`–`T20`)**.

---

## 2. Elimination of Execution-Truth Hazards (`H1`–`H7`)

| Hazard | Baseline Defect | Converged Remediation | Verification Gate |
| --- | --- | --- | --- |
| **H1** | `execute_commands=False` or `command=None` marked tasks `COMPLETED` and goals `SATISFIED` indistinguishable from real execution. | Introduced 12-state canonical `ExecutionTruthStatus`. Simulated runs record `truth_status=SIMULATED` on tasks and goals and never report `VERIFIED_SUCCESS`. | `T01` (`test_t01_simulated_mode_never_claims_verified_success`) |
| **H2** | `GoalEngine._execute_task()` ignored `ExecutionOutcome.exit_code != 0` and marked failed shell commands as `COMPLETED`. | Non-zero exit codes, timeouts (`124`), and sanitizer blocks (`126`) transition tasks to `TaskStatus.FAILED` / `ExecutionTruthStatus.EXECUTION_FAILED`, persisting `exit_code`, `stdout`, `stderr`, and `blocked_reason`. | `T02`, `T03` (`test_t02_nonzero_exit_code_marks_execution_failed`, `test_t03_blocked_sanitizer_command_marks_execution_failed_with_reason`) |
| **H3** | `run_goal_parallel()` swallowed worker exceptions or left failed tasks without failing the parent goal. | Parallel worker catches exceptions, records `TaskStatus.FAILED` / `ExecutionTruthStatus.EXECUTION_FAILED`, propagates downstream `BLOCKED` state, and marks the parent goal `GoalStatus.FAILED`. | `T04` (`test_t04_parallel_worker_uncaught_exception_marks_goal_failed`) |
| **H4** | Upstream task failure in a DAG left downstream tasks in `PENDING` instead of explicitly blocking them. | `TaskGraph.propagate_failures()` deterministically transitions all transitive dependents of a failed or blocked task to `TaskStatus.BLOCKED` / `ExecutionTruthStatus.BLOCKED` with `blocked_reason="upstream_task_failed:<id>"`. | `T05` (`test_t05_upstream_failure_propagates_blocked_to_downstream_tasks`) |
| **H5** | `verify_goal(profile="none")` marked goals `SATISFIED` with `passed=True` when zero verification checks ran. | `verify_goal(profile="none")` sets `truth_status=SIMULATED` (when simulated) or `UNAVAILABLE` (when commands ran without verification gates), never `VERIFIED_SUCCESS`. | `T06` (`test_t06_verification_profile_none_never_reports_verified_success`) |
| **H6** | `MekongCoreRuntimeImpl.commit()` fabricated a synthetic 12-char SHA-256 hash when `git_sha` was absent, impersonating a git commit. | `CommitRecord` explicitly distinguishes `commit_kind="runtime_state_commit"` (`git_sha=None`) vs `commit_kind="git_commit"` (verified 7–64 hex SHA). | `T07` (`test_t07_runtime_commit_distinguishes_runtime_state_from_git_commit`) |
| **H7** | `Governance.classify_risk()` defaulted unknown risk strings to `ActionClass.SAFE`, and `LocalExecutor` defaulted `strict_mode=False`. | `Governance.classify_risk()` fails closed to `ActionClass.FORBIDDEN` on unknown/empty risk strings. `LocalExecutor` defaults to `CommandSanitizer(strict_mode=True)` and enforces worktree boundary containment. | `T10`, `T19` (`test_t10_governance_classify_risk_fails_closed_on_unknown_risk`, `test_t19_worktree_path_escape_blocked`) |

---

## 3. Unified SQLite WAL Control Plane (`SQLiteGoalStore`)

All durable state is consolidated into `.mekong/goals.sqlite3` under `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA busy_timeout=5000`, and `threading.RLock` serialization:

1. **`goals` & `tasks` (Schema Migration Idempotent):**
   - Added `truth_status`, `exit_code`, `stdout`, `stderr`, `blocked_reason`, `is_idempotent`, `side_effect_uncertain`, and `mutates_workspace`.
2. **`tickets` (Webhook Intake Deduplication & Immutable Mandate):**
   - Enforces `UNIQUE(source_id, event_id)` for idempotent admission (`store.admit_ticket()`).
   - Stores canonical mandate columns (`requester`, `authorized_scope`, `workspace_id`, `mandate_version`, `policy_version`, `accepted_at`, `permitted_capabilities`, `resource_boundaries`, `risk_classification`, `cost_budget`, `retry_budget`, `verification_requirements`) and HMAC-SHA256 `mandate_hash`.
   - Protected by SQLite `BEFORE UPDATE` trigger `trg_tickets_immutable_mandate` and `store.verify_mandate_integrity()`, raising `MandateIntegrityError` on any worker tampering attempt (`T08`, `T09`).
3. **`worker_leases` (Bounded `2+1` Concurrency & Crash Recovery):**
   - Enforces `MAX_AUTONOMOUS_WORKERS = 2` concurrent `AUTONOMOUS` leases while reserving `OPERATOR_CONTROL_RESERVED = 1` slot for `status` / `cancel` / `inspect` (`T16`, `T17`).
   - `reconcile_orphaned_running_tasks()` inspects expired leases on startup/resume: idempotent tasks (`is_idempotent=True`, `side_effect_uncertain=False`) transition to `PENDING` / `RETRY_WAIT` (`T13`), whereas non-idempotent or side-effect-uncertain tasks halt in `BLOCKED` / `WAITING_APPROVAL` (`T14`).
4. **`report_outbox` (Transactional Outbound Delivery):**
   - `BuzzAdapter` persists outbound status updates with `UNIQUE(idempotency_key)` deduplication and deterministic `DEAD_LETTER` transition after `max_attempts` (`T15`).

---

## 4. Fail-Closed Governance, Worktree Isolation & Honest Cost Accounting

- **Policy Decision Contract (`src/core/governance.py`):**
  - `Governance.evaluate_ticket_action()` evaluates `ImmutableMandate` capabilities and resource boundaries, blocks untrusted content (`untrusted_context=True`) from executing non-low-risk capabilities (`T11`), and binds `HIGH`-risk actions to single-use `ApprovalToken` digests via `PayloadBoundApprovalEngine` (`T12`).
- **Worktree Isolation (`src/mekongcli/core/goal_engine/worktree_manager.py`):**
  - `WorktreeIsolationManager` provisions isolated task workspaces under `.mekong/worktrees/<ticket_id>_<task_id>`, blocks `..` and out-of-tree symlinks/paths (`WorktreeEscapeError`), and deterministically cleans up worktrees (`T18`, `T19`).
- **Honest Cost Accounting (`src/opc/models.py`, `src/opc/usage.py`, `SQLiteGoalStore`):**
  - `CostAccounting` separates `measured_tokens`, `estimated_tokens`, `actual_cost`, `estimated_cost`, and `cost_status` (`MEASURED | ESTIMATED | UNKNOWN`). Unmeasured local subprocess executions report `actual_cost=None` and `cost_status="UNKNOWN"` (never fabricating `0.0`), while ticket budget overruns halt execution before task dispatch (`T20`).

---

## 5. Verification Evidence

- **20-Scenario Autonomous Runtime Trust Matrix:**
  `python3 -m pytest tests/test_autonomous_runtime_trust_matrix.py -v` -> **20 passed** (`T01`–`T20`).
- **Combined Regression & Open-Core Boundary Suite:**
  `python3 -m pytest tests/test_opencore_saas_25_step_suite.py tests/test_core_boundary.py tests/test_dual_rail_checkout.py tests/test_raas_license_verifier.py tests/test_durian_grab_honest_diagnosis.py tests/test_idea_run_blueprint_writing.py tests/test_opencore_git_boundary_guard.py tests/test_github_content_25_step_sync.py tests/mekongcli/test_goal_engine.py tests/mekongcli/test_goal_cli.py tests/test_goal_engine_adapter.py tests/ports/test_goal_engine_conformance.py tests/test_core_lifecycle_contract.py tests/test_buzz_adapter.py tests/test_governance.py tests/test_opc_approval_security.py tests/test_opc_platform_contract.py tests/test_autonomous_runtime_trust_matrix.py` -> **202 passed, 0 failed**.
- **Static Analysis & Line-Count Ceilings:**
  `python3 -m ruff check` -> **All checks passed!**
  All `src/core/opencore/*.py` and `src/opc/*.py` files verified `<= 185 LOC`.
