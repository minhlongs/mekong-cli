---
title: "Supreme Command #01.2: Mekong CLI Adversarial Hardening & Sophia Handoff"
status: completed
created: 2026-11-02
branch: fix/supreme-command-01-2-runtime-hardening
mode: official
route: bugfix
---

# Plan: Supreme Command #01.2 — Adversarial Hardening & Sophia Handoff

## 1. Desired Outcome & Scope Boundary

**Outcome:** Close the 4 verified security/correctness findings (`F01`–`F04`) and 3 latent race/edge-case traps discovered during forensic audit, establish the executable Sophia Integration Contract v1.0 (`mekong.sophia.execution_contract.v1`), and verify all 22 adversarial scenarios (`A01`–`A22`) with zero regressions.

**In Scope:**
1. **Gate G1 — Finding F01 (`False Verified Success` Closure)**:
   - `src/core/adapters/goal_engine_adapter.py`: Remove optimistic `else:` fallback that fabricates `VERIFIED_SUCCESS` when `raw_truth` is missing/`None`/`MagicMock`/unknown under `execute_commands=True`; fail closed to `ExecutionTruthStatus.UNAVAILABLE` (`success=False`). Verify task-level truth states in `self._store.get_tasks(svc_goal_id)` so any `SIMULATED`/`PLANNED`/`UNAVAILABLE` task prevents `VERIFIED_SUCCESS` under `execute_commands=True`. Keep `execute_commands=False` backward-compatible (`simulated=True`, `truth_status="SIMULATED"`).
   - `src/mekongcli/core/goal_engine/service.py`: In `verify_goal()`, never allow `simulated_run=False` to override actual task states when `tasks` is empty, any task is not `COMPLETED`, or any task is `SIMULATED` / has no `command`.
   - `src/cli/cook_command.py` & `src/cli/goal_commands.py`: Expose `--isolate-worktree`, `--ticket-id`, and `--require-verified` on `cook-auto` and `cook-auto-parallel`, enforce non-zero exit when `--require-verified` is not satisfied, and include `truth_status` and `simulated` in `goal list` and `goal cancel` outputs.
2. **Gate G2 — Finding F02 (`Worktree Lifecycle SCRATCH/ARTIFACT/RECOVERY & SHA-256 Handoff`)**:
   - `src/mekongcli/core/goal_engine/worktree_manager.py`:
     - Add `WorktreeMode` (`SCRATCH`, `ARTIFACT`, `RECOVERY`), `ArtifactRecord`, and `WorktreeFinalizationResult`.
     - Manage `.mekong/worktrees/`, `.mekong/artifacts/<ticket_id>/<task_id>/attempt_<n>/`, and `.mekong/recovery_worktrees/<ticket_id>_<task_id>_attempt_<n>/`.
     - Serialize `git worktree` subprocess calls with a re-entrant lock (`_git_lock`) to prevent `.git/config.lock` races during parallel execution.
     - Seed non-git fallback worktrees (`tmp_path` in tests) with top-level workspace files (excluding `.git`, `.mekong`, `__pycache__`, `.venv`, `node_modules`).
     - Implement `harvest_artifacts()` (computes SHA-256, copies modified/new files + git diff patch to `.mekong/artifacts/`, writes `manifest.json`, verifies destination SHA-256 before cleanup), `preserve_recovery_worktree()` (moves/copies dirty or failed worktree to `.mekong/recovery_worktrees/` with `recovery_manifest.json` without overwriting prior attempts), `finalize_worktree()`, and ownership-aware idempotent `cleanup()`.
   - `src/mekongcli/core/goal_engine/service.py`:
     - Replace unconditional `finally: self.worktree_manager.cleanup(wt_path)` in `run_goal()` and `run_goal_parallel()` with `finalize_worktree()` so artifacts are harvested before cleanup and failed/uncertain runs preserve recovery worktrees.
     - Record `worktree_path` on `WorkerLease` and acquire/release worker leases consistently.
3. **Gate G3 — Finding F03 (`Fail-Closed Durable Webhook Admission`)**:
   - `src/core/buzz_runtime_adapter.py`, `src/core/buzz_adapter.py`, `src/mekongcli/core/goal_engine/store.py`:
     - Support `ingress_mode: Literal["trusted_local", "external_webhook"]` (and alias `admission_mode`). Auto-enable durable admission when `ingress_mode == "external_webhook"`, `outbox_store is not None`, or `payload` carries webhook metadata (`event_id`, `source_id`).
     - In `external_webhook` mode (or when `admit_webhook_event` is called): fail closed with `BuzzConfigError` if `outbox_store is None`, fail closed with `ValueError` if explicit `event_id` or `goal` is missing/empty.
     - Catch `sqlite3.IntegrityError` inside `SQLiteGoalStore.admit_ticket()` and `enqueue_outbox()` (`enqueue_outbox_report`) to eliminate TOCTOU race conditions across concurrent SQLite connections.
     - Persist ticket `truth_status` updates (`RUNNING` -> `VERIFIED_SUCCESS` / `SIMULATED` / `CANCELLED` / `EXECUTION_FAILED`) via `SQLiteGoalStore.update_ticket_truth_status()` and refuse re-execution of already-completed or in-flight tickets on duplicate delivery or restart.
4. **Gate G4 — Finding F04 (`Server-Side WebhookAuthorityPolicy & Callback SSRF Defense`)**:
   - `src/core/buzz_adapter.py`:
     - Add `BuzzSecurityError(BuzzConfigError, PermissionError, ValueError)` and `WebhookAuthorityPolicy`.
     - Enforce server-side policy in `admit_webhook_event()`: validate `requester`, reject unauthorized `permitted_capabilities`, reject path-traversal or out-of-scope `resource_boundaries` / `authorized_scope`, prevent risk downgrade or invalid risk levels, reject `cost_budget` / `retry_budget` exceeding server ceilings or `<= 0`, and pin server-owned `mandate_version`, `policy_version`, `accepted_at`, and `verification_requirements`.
     - Implement `validate_callback_destination()` (and alias `validate_callback_url()`): enforce `https` (unless host is explicitly in `allowed_http_hosts`), block credentials in URL, block `localhost`/`.local`/`.internal`, block loopback (`127.0.0.0/8`, `::1`, `::ffff:127.0.0.1`), private RFC1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `fc00::/7`), link-local/cloud metadata (`169.254.0.0/16`, `fe80::/10`), CGNAT (`100.64.0.0/10`), multicast, reserved, and unspecified IPs, and validate all DNS records returned by `socket.getaddrinfo()`.
     - Use `_NoRedirectHandler(urllib.request.HTTPRedirectHandler)` in `_urllib_transport` to block all HTTP `3xx` redirects.
5. **Gate G5 — Sophia Integration Contract v1.0 (`mekong.sophia.execution_contract.v1`)**:
   - Create `src/core/contracts/sophia_integration_v1.py`, `docs/sophia-integration-contract.md`, and `tests/test_sophia_integration_contract.py` implementing all 10 required operations, the 4 independent outcome axes (`execution_outcome`, `verification_outcome`, `delivery_outcome`, `business_outcome`), the fail-closed `verified_success_claim_permitted` invariant, and fixture validator `validate_sophia_handoff_fixture()`.
6. **Gate G6–G9 — Adversarial Matrix (`A01`–`A22`), Regression Verification, Core DNA Sync & PR Delivery**:
   - Create `tests/test_supreme_command_01_2_adversarial.py` covering `F01-T01..T06`, `F02-T01..T10`, `F03-T01..T11`, `F04-T01..T11`, and `A01`–`A22`.
   - Update `dna/core-dna.json` and `docs/` (`docs/buzz-runtime-adapter.md`, `docs/runtime-adapters.md`, `docs/core-contract.md`).

**Out of Scope:**
- Modifying `src/core/opencore/phase_559_opencore_25_step_catalog.py` or exceeding `185 LOC` in any `src/core/opencore/*.py`, `src/core/raas_license_verifier.py`, or `src/opc/*.py` module.
- Modifying the external Sophia AI Factory repository.

## 2. Acceptance Criteria

- [x] `F01-T01..T06` pass: Missing, `None`, `MagicMock`, `PLANNED`, `SIMULATED`, or `UNAVAILABLE` `truth_status` never produces `VERIFIED_SUCCESS` when `execute_commands=True`.
- [x] `F02-T01..T10` pass: Worktrees follow `SCRATCH` / `ARTIFACT` / `RECOVERY` lifecycle; artifacts are harvested to `.mekong/artifacts/` with verified SHA-256 manifests; failed/uncertain worktrees are preserved in `.mekong/recovery_worktrees/`; `cleanup()` is ownership-aware and idempotent.
- [x] `F03-T01..T11` pass: External webhooks fail closed without `outbox_store` or `event_id`; concurrent `admit_ticket()` / `enqueue_outbox()` calls are race-safe; completed or in-flight tickets are never re-executed on replay or restart.
- [x] `F04-T01..T11` pass: `WebhookAuthorityPolicy` blocks capability/scope/budget/risk escalation; `validate_callback_destination()` and `_NoRedirectHandler` block loopback, RFC1918, link-local/metadata (`169.254.169.254`), DNS rebinding to private IPs, and HTTP `3xx` redirects.
- [x] Gate G5 (`src/core/contracts/sophia_integration_v1.py`, `docs/sophia-integration-contract.md`, `tests/test_sophia_integration_contract.py`) passes 100%.
- [x] Gate G6 & G7 (`tests/test_supreme_command_01_2_adversarial.py` `A01`–`A22` + all existing regression and boundary suites) pass 100%.
- [x] `src/core/opencore/phase_559_opencore_25_step_catalog.py` is unchanged byte-for-byte and all Open-Core/OPC modules remain `<= 185 LOC`.

## 3. Validation & Red-Team Gate Summary

- **Validation Gate (`PASS`)**: All target files, line numbers, and symbols verified on `HEAD` (`2c3c8dd13e9e7fadab244f2fb21c84018fffc112`).
- **Red-Team Gate (`PASS`)**:
  1. `tests/test_buzz_adapter.py` and `tests/test_buzz_transport.py` use synthetic domains `https://buzz.test/...` and `https://buzz.example.com/...` with fake transports → `validate_callback_destination()` runs full scheme/IP/DNS checks and allows `socket.gaierror` only on reserved RFC 6761/2606 test domains (`.test`, `.example.com`, `.example.org`, `.example.net`) when `strict_dns=False` (fake transport), while rejecting any resolved private IP and enforcing `strict_dns=True` in `_urllib_transport`.
  2. `StubGoalEngineService` in `tests/test_goal_engine_adapter.py:60` has a fixed 3-arg `run_goal` signature → preserve `inspect.signature` guard in `GoalEngineAdapter.commit()`.
  3. Linked git worktrees have a `.git` file, not a directory → keep `git_dir.exists()` in `WorktreeIsolationManager` and guard `git worktree` calls with `threading.RLock()`.
