# MEKONG CLI — AUTONOMOUS RUNTIME CONVERGENCE & EXECUTION TRUTH AUDIT (2026-11-01)

- **Document ID:** `MEKONG_AUTONOMOUS_RUNTIME_RESTRUCTURE_2026-11-01`
- **Issue:** [#121](https://github.com/minhlongs/mekong-cli/issues/121) — *Supreme Command #01: Mekong CLI Autonomous Runtime Convergence & Execution Truth (H1–H7)*
- **Pull Request:** [#122](https://github.com/minhlongs/mekong-cli/pull/122) (`MERGED` into `main` at `a954f671e`)
- **Final Release Decision:** `PASS — VERIFIED FEATURE BRANCH`

---

## A. Forensic Baseline

- **Repository URL:** `https://github.com/minhlongs/mekong-cli`
- **Base Branch:** `main`
- **Base HEAD SHA:** `becc344a6` (merged with upstream `3271a8151` prior to PR landing)
- **Working Branch:** `feat/autonomous-runtime-convergence` (isolated git worktree `/Users/macbook/mekong-cli-autonomous-worktree`)
- **Initial Worktree State:** Primary worktree `/Users/macbook/mekong-cli-opc-unification` contained untracked spec `MEKONG CLI — AUTONOMOUS RUNTIME CONVERGENCE.md` (preserved untouched). Dedicated worktree `/Users/macbook/mekong-cli-autonomous-worktree` started clean.
- **Actual Architecture & Command Surface:** Python 3.11+ Typer CLI (`src/cli/app_setup.py`, 39 command groups), `MekongCoreRuntimeImpl` (`src/core/runtime_adapter.py`), `GoalEngine` + `SQLiteGoalStore` (`src/mekongcli/core/goal_engine/`), `LocalExecutor` (`src/mekongcli/core/execution/local_executor.py`), `Governance` (`src/core/governance.py`), `BuzzAdapter` (`src/core/buzz_adapter.py`), and `src/opc/` (`<= 185 LOC` per module).
- **Key Documentation Contradictions Identified & Resolved:**
  1. `docs/autonomy-model.md` previously stated unknown risk levels fell back to `SAFE` (fail-open); updated to reflect fail-closed `ActionClass.FORBIDDEN`.
  2. `docs/core-contract.md` did not document `ExecutionTruthStatus` or `CommitRecord.commit_kind` (`runtime_state_commit` vs `git_commit`); updated to match runtime behavior.

---

## B. Verified Findings (`H1`–`H7`)

| ID | Severity | File & Symbol | Reproduction | Root Cause | Affected Behavior | Fix Status |
| --- | --- | --- | --- | --- | --- | --- |
| **H1** | `CRITICAL` (`P0`) | `src/mekongcli/core/goal_engine/service.py` (`run_goal`, `_execute_task`) | Run `GoalEngine.run_goal(..., execute_commands=False)` or task with `command=None`. | Simulated runs set `TaskStatus.COMPLETED` and `GoalStatus.SATISFIED` without recording simulated state. | Dry-run / simulated execution claimed real completion (`SATISFIED`). | **FIXED & VERIFIED** (`T01`) |
| **H2** | `CRITICAL` (`P0`) | `src/mekongcli/core/goal_engine/service.py` (`_execute_task`) | Execute task command exiting with code `42` or blocked by `CommandSanitizer`. | `_execute_task` ignored `outcome.exit_code != 0` and marked task `COMPLETED`. | Failed subprocesses and sanitizer blocks were reported as succeeded tasks. | **FIXED & VERIFIED** (`T02`, `T03`) |
| **H3** | `HIGH` (`P0`) | `src/mekongcli/core/goal_engine/service.py` (`run_goal_parallel`) | Raise uncaught exception inside parallel task execution worker. | Worker exception was not converted into deterministic `TaskStatus.FAILED` + `GoalStatus.FAILED`. | Parallel DAG runs hid worker crashes or left parent goal non-failed. | **FIXED & VERIFIED** (`T04`) |
| **H4** | `HIGH` (`P0`) | `src/mekongcli/core/goal_engine/dag.py` (`TaskGraph`), `service.py` | Fail upstream task `A` in DAG `A -> B -> C`. | No transitive failure propagation existed on `TaskGraph`. | Downstream dependent tasks remained `PENDING` instead of `BLOCKED`. | **FIXED & VERIFIED** (`T05`) |
| **H5** | `HIGH` (`P0`) | `src/mekongcli/core/goal_engine/service.py` (`verify_goal`) | Call `verify_goal(goal_id, profile="none")`. | `profile="none"` returned `passed=True` and marked goal `SATISFIED` with zero checks. | Unverified goals reported verified completion. | **FIXED & VERIFIED** (`T06`) |
| **H6** | `MEDIUM` (`P0`) | `src/core/runtime_adapter.py` (`MekongCoreRuntimeImpl.commit`) | Call `runtime.commit(result)` without `git_sha`. | Fabricated a 12-char SHA-256 hash when `git_sha` was absent. | Runtime state commits impersonated real Git commit SHAs. | **FIXED & VERIFIED** (`T07`) |
| **H7** | `CRITICAL` (`P0`) | `src/core/governance.py` (`classify_risk`), `local_executor.py` (`LocalExecutor`) | Pass `classify_risk("UNKNOWN_LEVEL")` or relative/symlink escape path to `LocalExecutor`. | `RISK_LEVEL_MAP.get()` defaulted to `ActionClass.SAFE`; `LocalExecutor` defaulted `strict_mode=False` and lacked worktree boundary checks. | Unknown risk strings were auto-approved as `SAFE`; commands could reference paths outside isolated worktree. | **FIXED & VERIFIED** (`T10`, `T19`) |

---

## C. Architecture Convergence

- **Before Architecture:** `GoalEngine` (`SQLiteGoalStore`), `MekongCoreRuntimeImpl`, `BuzzAdapter`, and `src/opc/` operated with disconnected status enums, in-memory webhook state, fail-open risk classification on unknown strings, and unverified `COMPLETED` states.
- **After Architecture:**
  - **Canonical Execution Contract:** 12-state `ExecutionTruthStatus` (`PLANNED`, `SIMULATED`, `QUEUED`, `RUNNING`, `WAITING_APPROVAL`, `RETRY_WAIT`, `VERIFIED_SUCCESS`, `EXECUTION_FAILED`, `VERIFICATION_FAILED`, `BLOCKED`, `CANCELLED`, `UNAVAILABLE`) with backward-compatible `GoalStatus` / `TaskStatus` mapping.
  - **Unified SQLite WAL Persistence (`.mekong/goals.sqlite3`):** Consolidates `goals`, `tasks`, `tickets` (`UNIQUE(source_id, event_id)` + HMAC-SHA256 `ImmutableMandate` + `trg_tickets_immutable_mandate`), `worker_leases` (`2` `AUTONOMOUS` + `1` `OPERATOR_CONTROL`), and `report_outbox` (`UNIQUE(idempotency_key)`).
  - **Reused Components:** `SQLiteGoalStore`, `GoalEngine`, `MekongCoreRuntimeImpl`, `Governance`, `PayloadBoundApprovalEngine` (`src/opc/approval.py`), `CommandSanitizer`, `BuzzAdapter`.
  - **Newly Introduced Modules:** `src/mekongcli/core/goal_engine/worktree_manager.py` (`WorktreeIsolationManager`).

---

## D. Implementation Evidence

| File Modified / Added | Reason | Behavioral Difference | Test Evidence |
| --- | --- | --- | --- |
| `src/mekongcli/core/goal_engine/models.py` | Add canonical truth states & durable ticket/lease/outbox models | Defines `ExecutionTruthStatus`, `ImmutableMandate`, `DurableTicket`, `WorkerLease`, `OutboxMessage` | `T01`–`T20` |
| `src/mekongcli/core/goal_engine/store.py` | Unify SQLite WAL persistence, mandate integrity, leases, crash recovery, outbox, cost accounting | Enables `PRAGMA journal_mode=WAL`, `admit_ticket()`, `verify_mandate_integrity()`, `acquire_worker_lease()`, `reconcile_orphaned_running_tasks()`, `enqueue_outbox()` | `T08`, `T09`, `T13`–`T17`, `T20` |
| `src/mekongcli/core/goal_engine/dag.py` | Deterministic downstream failure propagation | Adds `TaskGraph.propagate_failures()` marking transitive dependents `BLOCKED` | `T05` |
| `src/mekongcli/core/goal_engine/service.py` | Fix `H1`–`H5`, wire lease acquisition & worktree isolation | Records `SIMULATED`/`EXECUTION_FAILED`/`BLOCKED`/`UNAVAILABLE` truthfully; enforces `2+1` worker lanes | `T01`–`T06`, `T16`–`T18` |
| `src/mekongcli/core/goal_engine/worktree_manager.py` | Isolated workspace per concurrent write task | Provisions `.mekong/worktrees/<ticket_id>_<task_id>` (`git worktree` or clean copy fallback) and blocks path escape | `T18`, `T19` |
| `src/mekongcli/core/execution/local_executor.py` | Enforce `strict_mode=True` and worktree path confinement | Rejects `..`, out-of-tree absolute paths, `flag=path` escapes, and symlink escapes with exit code `126` | `T02`, `T03`, `T19` |
| `src/core/governance.py` | Fail-closed risk classification, mandate/boundary checks, untrusted context separation, payload-bound token verification | `classify_risk()` defaults to `ActionClass.FORBIDDEN`; `evaluate_ticket_action()` enforces mandate, `untrusted_context`, and `ApprovalToken` digest | `T10`–`T12` |
| `src/core/runtime_adapter.py` | Fix `H6` commit SHA fabrication and gate `ModelProposal` | `CommitRecord` separates `runtime_state_commit` vs `git_commit`; `validate_model_proposal()` enforces `untrusted_context=True` | `T07`, `test_runtime_adapter.py` |
| `src/core/buzz_adapter.py` | Durable webhook intake & outbox correlation | Deduplicates `(source_id, event_id)` via `SQLiteGoalStore` and queues correlated replies in `report_outbox` | `T08`, `T15` |
| `src/opc/models.py`, `src/opc/usage.py` | Honest cost accounting (`<= 185 LOC` preserved) | Adds `CostAccounting` (`MEASURED | ESTIMATED | UNKNOWN`); unmeasured runs report `actual_cost=None` | `T20`, `test_opc_platform_contract.py` |

---

## E. Trust Matrix (`T01`–`T20`)

Command: `python3 -m pytest tests/test_autonomous_runtime_trust_matrix.py -v` (`20 passed in 1.24s`)

| ID | Scenario | Expected State | Actual State | Result |
| --- | --- | --- | --- | --- |
| `T01` | Simulated mode (`execute_commands=False`) | `truth_status=SIMULATED` (never `VERIFIED_SUCCESS`) | `truth_status=SIMULATED` | **PASS** |
| `T02` | Non-zero command exit code (`exit 42`) | `TaskStatus.FAILED`, `truth_status=EXECUTION_FAILED`, `exit_code=42` | `FAILED` / `EXECUTION_FAILED` / `42` | **PASS** |
| `T03` | Blocked sanitizer command (`rm -rf /`) | `TaskStatus.FAILED`, `exit_code=126`, `blocked_reason` populated | `FAILED` / `126` / `blocked_reason` set | **PASS** |
| `T04` | Parallel worker uncaught exception | Worker task `FAILED`, parent goal `GoalStatus.FAILED` | `FAILED` / `GoalStatus.FAILED` | **PASS** |
| `T05` | Upstream failure in DAG (`t1 -> t2 -> t3`) | `t2`, `t3` marked `TaskStatus.BLOCKED` (`upstream_task_failed:t1`) | `t2`, `t3` `BLOCKED` | **PASS** |
| `T06` | `verify_goal(profile="none")` | `truth_status` in `{SIMULATED, UNAVAILABLE}`, never `VERIFIED_SUCCESS` | `SIMULATED` / `UNAVAILABLE` | **PASS** |
| `T07` | `runtime.commit()` without/with `git_sha` | `runtime_state_commit` (`git_sha=None`) vs `git_commit` (`git_sha` set) | Matched | **PASS** |
| `T08` | Webhook `(source_id, event_id)` replay | First returns `(ticket, True)`, replay returns `(ticket, False)` | Matched | **PASS** |
| `T09` | Worker mandate tampering attempt | SQLite trigger aborts update; `verify_mandate_integrity()` raises `MandateIntegrityError` | Matched | **PASS** |
| `T10` | Unknown/empty risk classification | `Governance.classify_risk()` returns `ActionClass.FORBIDDEN` | `ActionClass.FORBIDDEN` | **PASS** |
| `T11` | Prompt injection (`untrusted_context=True`) | High/medium capability denied (`PolicyDecision.decision == "DENY"`) | `DENY` | **PASS** |
| `T12` | High-risk action payload-bound approval | Replay/tampered/expired token denied; matching single-use token allowed once | Matched | **PASS** |
| `T13` | Crash recovery of idempotent task | Expired lease transitions task to `PENDING` / `RETRY_WAIT` | `PENDING` / `RETRY_WAIT` | **PASS** |
| `T14` | Crash recovery of non-idempotent task | Expired lease transitions task to `BLOCKED` / `WAITING_APPROVAL` | `BLOCKED` / `WAITING_APPROVAL` | **PASS** |
| `T15` | Transactional outbox retry & dead-letter | Deduplicates `idempotency_key`; transitions to `DEAD_LETTER` after `max_attempts` | `DEAD_LETTER` | **PASS** |
| `T16` | Autonomous worker concurrency cap (`2`) | 3rd concurrent `AUTONOMOUS` lease rejected (`None`) | Rejected (`None`) | **PASS** |
| `T17` | Reserved `OPERATOR_CONTROL` lane (`+1`) | Succeeds even when both `AUTONOMOUS` lanes are saturated | Lease acquired | **PASS** |
| `T18` | Worktree isolation for concurrent tasks | Distinct `.mekong/worktrees/<ticket>_<task>` paths; no file bleed | Isolated & cleaned up | **PASS** |
| `T19` | Worktree path / symlink escape | `WorktreeEscapeError` and `LocalExecutor` exit code `126` | Blocked (`126`) | **PASS** |
| `T20` | Honest cost accounting & budget enforcement | Unmeasured run sets `actual_cost=None`, `cost_status="UNKNOWN"`; overrun blocks dispatch | Matched | **PASS** |

---

## F. Security Assessment

- **Privilege Escalation:** Blocked by `ImmutableMandate` HMAC-SHA256 verification and SQLite trigger `trg_tickets_immutable_mandate` (forbidding mutation of mandate fields or `mandate_version`).
- **Prompt Injection:** `untrusted_context=True` in `Governance.evaluate_ticket_action()` and `MekongCoreRuntimeImpl.validate_model_proposal()` prevents untrusted payloads from invoking non-low-risk tools or capabilities outside `AgentMeta.allowed_tools`.
- **Secrets Exposure:** No secrets or tokens logged or committed; `CommandSanitizer(strict_mode=True)` blocks sensitive environment/credential exfiltration patterns.
- **Isolation Boundaries:** `WorktreeIsolationManager` + `LocalExecutor._validate_worktree_escape()` block `..`, out-of-tree absolute paths, `flag=path` options, and symlinked parent directories.
- **Replay & Idempotency:** Enforced at intake (`UNIQUE(source_id, event_id)`), approval (`PayloadBoundApprovalEngine` single-use nonce + payload SHA-256 digest), and outbound reporting (`UNIQUE(idempotency_key)`).
- **Open-Core & RaaS Invariants:** `src/core/opencore/phase_559_opencore_25_step_catalog.py` is 100% untouched; all `src/core/opencore/*.py` and `src/opc/*.py` modules remain `<= 185 LOC`.

---

## G. Performance and Economics

- **SQLite Contention:** Single `.mekong/goals.sqlite3` database under `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, `PRAGMA busy_timeout=5000`, and `threading.RLock` with context-managed connection cleanup (`0` unclosed database warnings).
- **Worker Concurrency:** Bounded at `MAX_AUTONOMOUS_WORKERS = 2` + `OPERATOR_CONTROL_RESERVED = 1` (`2+1`), preventing local CPU/memory exhaustion on macOS.
- **Honest Cost Telemetry:** `CostAccounting` records `actual_cost=None` and `cost_status="UNKNOWN"` when subprocesses do not report token usage, never fabricating `$0.00` spend.

---

## H. Git & CI Evidence

- **Base SHA:** `becc344a6` / `3271a8151`
- **Branch Commits (`feat/autonomous-runtime-convergence`):**
  1. `d926bdf46` — `feat(core): unify autonomous runtime execution truth, durable tickets, and worktree isolation`
  2. `9e4601f89` — `fix(security,ci): harden mandate/worktree gates and pin Python 3.11 in core-dna-gate`
  3. `8bcc86df4` — `test(runtime): align test_commit_and_billing_and_telemetry with H6 commit_kind telemetry`
- **Pull Request:** [#122](https://github.com/minhlongs/mekong-cli/pull/122) — **MERGED** into `main` at commit `a954f671e` (30/30 PR checks passed; 8/8 post-merge `main` workflows passed, including 3,491 unit tests).

---

## I. Residual Risk, Rollback & Follow-Up

- **Fixed & Verified:** All `H1`–`H7` hazards and `T01`–`T20` scenarios.
- **Known Limitations / Deliberately Deferred:** OS-level network namespace isolation (`unshare` / container sandboxing) is not enforced by `LocalExecutor` on macOS; tasks requiring strict network air-gapping must use `DockerExecutionRuntime` (`--network none`).
- **Rollback Procedure:** Revert squash commit `a954f671e` on `main` (`git revert a954f671e`). SQLite schema additions in `.mekong/goals.sqlite3` are additive (`CREATE TABLE IF NOT EXISTS` and nullable/defaulted columns via `_ensure_columns()`), so existing `.mekong/goals.sqlite3` files remain backward-compatible.
