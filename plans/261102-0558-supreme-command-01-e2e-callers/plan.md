---
title: "Supreme Command #01.1: Mekong CLI Autonomous Runtime Production-Caller & Operator Surface Convergence"
status: completed
created: 2026-11-02
branch: feat/autonomous-runtime-e2e-callers
mode: official
route: feature
---

# Plan: Supreme Command #01.1 — Production-Caller & Operator Surface Convergence

## 1. Desired Outcome & Scope Boundary

**Outcome:** Close the 3 remaining production-caller wiring gaps after Supreme Command #01 (`PR #122` + `PR #123`) so every CLI command (`mekong goal`, `mekong cook-auto`), `GoalEngineAdapter.commit()`, and `BuzzRuntimeAdapter.assign_mission()` surfaces `ExecutionTruthStatus` truthfully and enforces `SQLiteGoalStore` webhook replay deduplication and `report_outbox` durability.

**In Scope:**
1. **Phase 1 — `GoalEngine` & `GoalEngineAdapter` Explicit Dual Mode (`src/mekongcli/core/goal_engine/service.py`, `src/core/adapters/goal_engine_adapter.py`)**:
   - Add `isolate_worktree: bool = False` to `GoalEngine.run_goal()` and `ticket_id: str | None = None, isolate_worktree: bool = False` to `GoalEngine.resume_goal()`, sharing worktree allocation/cleanup with `run_goal_parallel()`.
   - Add `execute_commands: bool = False, isolate_worktree: bool = False` to `GoalEngineAdapter.__init__()` and `make_goal_engine_adapter()`, with overrides via `plan.metadata`.
   - Guard `self._service.run_goal()` invocation with `inspect.signature()` and `isinstance(raw_truth, ExecutionTruthStatus)` so `StubGoalEngineService` in `tests/test_goal_engine_adapter.py` remains 100% compatible.
   - Enforce `truth_status == ExecutionTruthStatus.VERIFIED_SUCCESS` when `execute_commands=True`; always populate `metadata["truth_status"]`, `metadata["simulated"]`, and `output["goal_truth_status"]`.
2. **Phase 2 — `BuzzAdapter` & `BuzzRuntimeAdapter` Replay Dedup + Outbox (`src/core/buzz_adapter.py`, `src/core/buzz_runtime_adapter.py`)**:
   - Add `BuzzAdapter.admit_webhook_event(payload, *, source_id=None) -> tuple[TicketRecord, bool]` backed by `self._outbox_store.admit_ticket()` with deterministic SHA-256 `ticket_id` and fail-closed `ImmutableMandate`.
   - Add `outbox_store: SQLiteGoalStore | None = None` to `BuzzRuntimeAdapter.__init__()`.
   - In `BuzzRuntimeAdapter.assign_mission()`, short-circuit duplicate `(source_id, event_id)` events with `{"status": "duplicate_ignored", "duplicate": True, "ticket_id": ticket.ticket_id, ...}` without calling `run_from_payload()` or `send_update()`; for new events, pass `ticket_id`, `source_id`, `thread_id`, and deterministic `idempotency_key` into `send_update()`.
3. **Phase 3 — CLI Truth Surface & Operator Flags (`src/cli/goal_commands.py`, `src/cli/cook_command.py`)**:
   - Emit `truth_status` and `simulated` in `_goal_result_payload()` and `_cook_auto_payload()` (using `(snapshot.get("goal") or {})`).
   - Add `--isolate-worktree`, `--ticket-id`, `--require-verified` to `goal run`, `goal run-parallel`, `goal resume` (and `--require-verified` to `goal verify`); align default `--workers` from `3` to `2` (`MAX_AUTONOMOUS_WORKERS = 2`).
   - Fix early-return `--json` exit-code bug in `goal_run_parallel` and `goal_verify` via shared `_should_exit_nonzero(goal, require_verified)` helper.
4. **Phase 4 — E2E Verification & Documentation Parity (`tests/test_autonomous_runtime_e2e_callers.py`, `docs/`)**:
   - Add comprehensive E2E test suite `tests/test_autonomous_runtime_e2e_callers.py` covering all 4 caller surfaces.
   - Update `docs/buzz-runtime-adapter.md`, `docs/runtime-adapters.md`, and `docs/core-contract.md`.

**Out of Scope (Non-Goals):**
- Modifying SQLite schema in `src/mekongcli/core/goal_engine/store.py`.
- Modifying any file in `src/core/opencore/`, `src/core/raas_license_verifier.py`, or `src/opc/`.

**Constraints:**
- Byte-for-byte invariant on `src/core/opencore/phase_559_opencore_25_step_catalog.py`.
- `<= 185 LOC` ceiling on all `src/core/opencore/*.py`, `src/core/raas_license_verifier.py`, and `src/opc/*.py` modules.

## 2. Acceptance Criteria

- [x] Plan validated and red-teamed against existing test stubs and boundaries.
- [x] `mekong goal run/status/verify --json` and `mekong cook-auto --json` emit `truth_status` and `simulated`.
- [x] `mekong goal run`, `run-parallel`, and `resume` expose `--isolate-worktree`, `--ticket-id`, `--require-verified` with `--workers` default `2`, and `--json` exits non-zero on failure or unverified `--require-verified`.
- [x] `GoalEngineAdapter.commit()` enforces `VERIFIED_SUCCESS` when `execute_commands=True` and preserves backward compatibility when `execute_commands=False`.
- [x] `BuzzRuntimeAdapter.assign_mission()` skips duplicate `(source_id, event_id)` events (`status="duplicate_ignored"`, `duplicate=True`) and queues failed callbacks into `report_outbox`.
- [x] `tests/test_autonomous_runtime_e2e_callers.py` and all existing unit/conformance/boundary tests pass 100%.

## 3. Validation & Red-Team Gate Summary

- **Validation Gate (`PASS`):** All target files, line anchors, and test suites verified on `HEAD` (`20b9f14b2`).
- **Red-Team Gate (`PASS`):**
  1. `StubGoalEngineService.run_goal` (`tests/test_goal_engine_adapter.py:60`) lacks `**kwargs` and returns `MagicMock()` → mitigated via `inspect.signature()` + `isinstance(raw_truth, ExecutionTruthStatus)`.
  2. `tests/mekongcli/test_goal_cli.py:211` passes `snapshot` without `"goal"` key → mitigated via `snapshot.get("goal") or {}`.
  3. `goal_run_parallel` and `goal_verify` `--json` branches return before exit-code check → mitigated by computing `should_fail = _should_exit_nonzero(goal, require_verified)` before `if json_output:`.
