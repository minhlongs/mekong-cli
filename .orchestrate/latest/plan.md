---
title: "Super Command #4 — Next 10 Tasks (Runtime v0.3)"
description: "Merge CI gates PR, converge verifier, enforce network policy, close MemoryStore/GoalEngine/telemetry contract gaps, remount NOWPayments behind PaymentProvider"
status: pending
priority: P1
effort: 16h
branch: feat/sc4-next-10-tasks
tags: [runtime, contracts, debt-closure, protected-flows]
created: 2026-08-25
---

# Super Command #4 — Plan

## 1. Reframed Problem

Runtime v0.2 (PR #9, 0d08762c7) completed contracts E1–E9 but left 10 known gaps from the §23 STOP report. SC#4 closes them in one branch (`feat/sc4-next-10-tasks`, based on main 9898cee5e): make CI gates actually runnable (PR #7), converge the two diverged RecipeVerifier stacks into one canonical verifier, turn the NetworkPolicy placeholder into real deny-all enforcement, implement the two remaining contract gaps (MemoryStore, GoalEngine conformant adapters), prove the MCP adapter against a real server, close the llm_client transitional exception per DEPRECATION.md, replace deleted E3 tracing stubs with a real mission-correlated telemetry emitter, remount the protected NOWPayments IPN behind PaymentProvider without behavior change, and verify-then-defer E10 Buzz (no credentials exist). Hard constraints: protected flows (NOWPayments IPN, license gate) keep byte-identical endpoint behavior; `.github/workflows/*` untouched in this branch (owned by PR #7); parity gate shows 0 new failures vs the 277-line baseline.

## 2. Work Checklist

### Wave A — independent code lanes (parallel-safe, file ownership disjoint)

#### Task 4 — Verifier convergence (canonical = src/core/verifier.py)
Verified facts: `src/core/verifier.py` (517 lines) ALREADY has both `explain()` (line 336) and `verify_quality_gates()` (line 459), plus a threadpool timeout wrapper for verify commands. `src/harness/pev/verifier.py` (493 lines) lacks `explain()` and uses bare subprocess.run. Only importer of the pev copy: `src/harness/pev/orchestrator.py:22,231`. Re-export at `src/harness/pev/__init__.py:10`.
Steps:
- [ ] Repoint `src/harness/pev/orchestrator.py:22` and `:231` imports to `src.core.verifier`
- [ ] Repoint `src/harness/pev/__init__.py:10` re-export to core verifier
- [ ] Delete `src/harness/pev/verifier.py`
- [ ] Grep-verify zero remaining `pev.verifier` references (src/ + tests/)
- [ ] Run pev tests: `python3 -m pytest tests/test_pev_self_healing.py tests/test_e2e_pev.py tests/test_pev_planner_converged.py -q`
Acceptance: one RecipeVerifier class in repo; `grep -rn "class RecipeVerifier" src/` returns exactly `src/core/verifier.py`; pev tests green; parity 0 new.
Agent: fullstack-developer. Files owned: `src/harness/pev/orchestrator.py`, `src/harness/pev/__init__.py`, `src/harness/pev/verifier.py` (delete).

#### Task 5 — Real network enforcement
Verified facts: `NetworkPolicy` at `src/core/exec_runtime/types.py:33`, `allow_outbound: bool = False`, description "deny-all outbound (placeholder; not enforced)" (line 38). docker.py ALREADY enforces (`--network none` default, bridge when allowed — docker.py:99,119-132). local.py:78 and cloudflare.py:97 construct the struct but enforce nothing.
Steps:
- [ ] local.py: best-effort OS-level enforcement with capability detection — `sandbox-exec` (darwin) / `unshare -n` (linux) when `allow_outbound=False` and the tool is available; if unavailable, fail loud: raise at construction OR set `description` to "UNENFORCED" and log warning (choose raise-behavior via existing constructor arg pattern; do NOT silently claim deny-all)
- [ ] cloudflare.py: enforcement is transport-level (injected transport, "zero implicit network" per cloudflare.py:75) — gate any outbound-capable transport wiring on `allow_outbound`; update `description` to reflect reality
- [ ] Update `types.py:38` description strings; remove "placeholder; not enforced" wording everywhere it is now enforced
- [ ] Tests: deny-all blocks outbound (or raises) on local; allow_outbound=True permits; docker mapping unchanged; cloudflare transport gating
Acceptance: no "placeholder; not enforced" string remains for any runtime that claims enforcement; every runtime either enforces or fails loud; new tests green; parity 0 new.
Agent: fullstack-developer. Files owned: `src/core/exec_runtime/{types,local,cloudflare,docker}.py` + their tests.

#### Task 6 — MemoryStore conformant implementation
Verified facts: Protocol at `src/core/protocols.py:221` (`store/retrieve/delete/search`, runtime_checkable). `docs/core-contract.md:48` lists "none conformant — known gap, deferred". Live store `src/core/memory_canonical.py:49` has a DIFFERENT interface (`record/query/semantic_search`). Existing `src/core/adapters/memory_store_adapter.py` bridges to `MemoryBridge`, not to the protocol.
Steps:
- [ ] Implement conformant adapter (new file `src/core/adapters/memory_store_conformant.py`, ≤200 lines) wrapping `memory_canonical.MemoryStore`: `store(key,value,ttl)`→record, `retrieve(key)`→query hit bytes, `delete(key)`, `search(query,limit)`→semantic_search mapped to `MemoryHit`
- [ ] isinstance test against the runtime_checkable Protocol
- [ ] Update `docs/core-contract.md:48` row: gap → conformant adapter path
Acceptance: `isinstance(adapter, protocols.MemoryStore)` True; round-trip store/retrieve/delete/search tests green; contract table updated; parity 0 new.
Agent: fullstack-developer. Files owned: new adapter + its test + `docs/core-contract.md` (MemoryStore row only).

#### Task 7 — GoalEngine conformant adapter (wrap, do NOT rewrite)
Verified facts: Protocol at `src/core/protocols.py:247` (`decompose/adapt/commit`). Live engine `src/mekongcli/core/goal_engine/service.py:33` (`run_goal`:68, `run_goal_parallel`:138).
Steps:
- [ ] New adapter `src/core/adapters/goal_engine_adapter.py` (≤200 lines) wrapping the live service: `decompose(goal)`→Plan, `adapt(plan, failure)`→replanned Plan, `commit(plan)`→Result, delegating to `run_goal`
- [ ] isinstance test against runtime_checkable Protocol + delegation tests with a stub service
- [ ] Update `docs/core-contract.md` GoalEngine gap row if present
Acceptance: isinstance True; adapter delegates without duplicating engine logic; parity 0 new.
Agent: fullstack-developer. Files owned: new adapter + its test. `src/mekongcli/` read-only.

#### Task 9 — Close llm_client transitional exception
Verified facts: DEPRECATION.md resolution target = "MOVE to `src/providers/` (deferred)". `src/providers/` does NOT exist. Client at `src/core/adapters/llm/client.py` (imports `requests` line 40). 70 references to `src.core.adapters.llm`; src importers include `src/core/llm_router_adapter.py:21` + ~10 core modules; test patch strings in ~12 test files incl. `tests/conftest.py:293,311`; allowlist entry `tests/test_core_boundary.py:35`.
Steps:
- [ ] Create `src/providers/llm/client.py` (git mv of `src/core/adapters/llm/client.py` + package `__init__.py`s)
- [ ] Scripted repoint of all `src.core.adapters.llm` imports (src/ + tests/), including patch-target strings (`conftest.py:293,311` and the 12 test files)
- [ ] `tests/test_core_boundary.py`: remove allowlist line 35 (file no longer under src/core); verify boundary test still enforces vendor-SDK ban in core
- [ ] Update `docs/architecture/DEPRECATION.md`: exception → resolved, record move date
- [ ] Full grep: zero `src.core.adapters.llm` / `src/core/llm_client` references remain
Acceptance: `test_core_boundary.py` green with allowlist entry removed; all llm tests green; DEPRECATION.md shows resolved; parity 0 new.
Agent: fullstack-developer. Files owned: `src/providers/**`, `src/core/adapters/llm/**` (delete), all llm importers, `tests/conftest.py`, `tests/test_core_boundary.py`, `docs/architecture/DEPRECATION.md`.

#### Task 10 — Real telemetry emitter with mission_id (invariant 5)
Verified facts: E3 deleted `src/harness/observability/tracing.py` + `metrics.py` (byte-identical dead stubs). Invariant 5 (`docs/core-contract.md:62`): all telemetry carries mission_id; run() and run_from_payload() both produce complete start/step/finish traces. Existing pieces: `TelemetryCollector` (`src/core/telemetry_collector.py:45`, already has `mission_id` field line 39), `TelemetrySinkAdapter` (`src/core/telemetry_sink_adapter.py`), `MissionTracer` (`src/core/mission_tracer.py`), runtime_adapter already wires `_mission_tracer` log_step/end_mission (runtime_adapter.py:778-801) and `TelemetrySinkAdapter` (line 198).
Steps:
- [ ] New `src/core/telemetry_emitter.py` (≤200 lines): emitter implementing `ObservabilitySink` that emits start/step/finish events, every event carrying `mission_id`; composes TelemetryCollector (do not fork it)
- [ ] Wire into `runtime_adapter.run()` and `run_from_payload()` so BOTH paths emit complete start/step/finish traces with the active mission_id (run_from_payload uses payload pre-assigned id — see runtime_adapter.py:295-332)
- [ ] Tests: both paths produce 3-phase trace; every emitted event has non-empty mission_id; no event without correlation
Acceptance: invariant 5 testable and tested for both entry points; no dead stubs reintroduced; parity 0 new.
Agent: fullstack-developer. Files owned: new `src/core/telemetry_emitter.py` + its test, `src/core/runtime_adapter.py`.

### Wave B — protected flow (sequential, after Wave A merges to branch)

#### Task 3 — NOWPayments IPN remount behind PaymentProvider
Verified facts: endpoint `POST /webhooks/nowpayments` at `src/raas/nowpayments_router.py` (33 lines) → `handle_ipn` (`src/raas/nowpayments_webhook_handler.py:98`, HMAC via NOWPAYMENTS_IPN_SECRET). Mounted at `src/gateway.py:34,109`. `PaymentProvider` protocol at `src/core/protocols.py:256` (legacy + extended economic-bus methods, pure-data dataclasses).
Steps:
- [ ] Snapshot current endpoint behavior first: record exact response shapes (`{"status":"ok","action":...}`, `{"status":"error","detail":...}`) and handler call signature as golden tests
- [ ] New `src/raas/nowpayments_provider.py`: NowPaymentsProvider implementing PaymentProvider, delegating settlement/activation to existing `handle_ipn` internals (no logic rewrite)
- [ ] Router keeps the SAME path, SAME request parsing, SAME response JSON — only internal delegation changes to the provider
- [ ] Golden tests: valid sig → ok+action; bad sig → error; exception → error; response bodies byte-identical to pre-change
- [ ] Keep old direct-mount code path reachable until adapter tests green; then swap; license gate untouched
Acceptance: golden IPN tests pass byte-identical; `isinstance(provider, protocols.PaymentProvider)` True; gateway.py mount lines unchanged in path/behavior; parity 0 new.
Agent: fullstack-developer (dedicated lane, no parallel work). Files owned: `src/raas/nowpayments_provider.py` (new), `src/raas/nowpayments_router.py`, its tests. `src/raas/nowpayments_webhook_handler.py` internals read-mostly (no signature changes).

### Wave C — external/ops (sequential, mostly non-code)

#### Task 1 — PR #7 rebase + merge (CI-runnable gates)
Verified facts: `gh pr view 7` → mergeable CONFLICTING, mergeStateStatus DIRTY, head `fix/ci-runnable-gates` (based on d71e13fa0), state OPEN. PR touches 8 workflow files + pyproject.toml + requirements.txt + .orchestrate/ artifacts.
Steps:
- [ ] Check out PR #7 branch locally; `git rebase main` (main = 9898cee5e)
- [ ] Conflicts: KEEP PR #7's side for `.github/workflows/*`, `pyproject.toml`, `requirements.txt`; take MAIN's side for `.orchestrate/` artifacts
- [ ] Force-push PR branch; verify GitHub shows MERGEABLE
- [ ] Merge PR #7 (squash); then rebase/merge main back into feat/sc4-next-10-tasks
- [ ] Verify CI on merged main: core-dna-gate + Quality Gates green-on-branch (repo CI structurally red on main — green-on-branch is the bar)
Acceptance: PR #7 merged; workflows live; SC4 branch rebased clean on post-#7 main; no workflow edits made from the SC4 branch itself.
Agent: git-manager. Constraint: `.github/workflows/*` edited ONLY on the PR #7 branch, never on feat/sc4-next-10-tasks.

#### Task 2 — E10 Buzz: verify-then-defer
Verified facts: NO Buzz credentials anywhere (env vars, ~/.config). Seam exists: `run_from_payload` (`src/core/runtime_adapter.py:312`), lazy BuzzAdapter import (line 319), `BuzzRuntimeAdapter` facade (`src/core/buzz_runtime_adapter.py`, 234 lines). Sanctioned-seam exception documented in core-contract.md.
Steps:
- [ ] Confirm seam tests green: `python3 -m pytest tests/ -q -k "buzz or run_from_payload"`
- [ ] Re-verify credential absence (env, ~/.config, .env*) — document the check
- [ ] Write blocker note in `.orchestrate/latest/reports/` (what's needed: Buzz workspace + credentials; what's ready: seam + facade + tests)
- [ ] Do NOT fabricate credentials, do NOT stub a fake Buzz "live" path
Acceptance: seam tests green; blocker documented with evidence; zero fabricated credentials; task status = deferred-with-evidence.
Agent: fullstack-developer (verify) + docs-manager (blocker note).

#### Task 8 — MCP adapter ↔ capability bus integration test
Verified facts: `tests/test_mcp_server_integration.py` ALREADY spawns the real MCP server as subprocess (JSON-RPC over stdio, `@pytest.mark.integration`, mcp_proc fixture) but tests the SERVER directly, not the adapter↔bus path. `tests/test_mcp_capability_adapter.py` uses `_FakeBus`. Adapter: `src/core/adapters/mcp_capability_adapter.py` (`sync_from_mcp`, `_TOOL_PREFIX = "cc_"`).
Steps:
- [ ] New integration test reusing the `mcp_proc` subprocess fixture pattern: real server → `MCPCapabilityAdapter.sync_from_mcp()` → capabilities registered on a real (or minimal protocol-conformant) CapabilityBus → invoke one tool end-to-end through the bus
- [ ] If the real server cannot run in the environment: build hermetic in-process MCP server test double speaking real JSON-RPC over stdio pipes, and document the gap in the test module docstring
- [ ] Mark `@pytest.mark.integration` consistent with existing convention
Acceptance: adapter↔bus path proven against a real-protocol server (subprocess or hermetic double); test green locally; gap documented if doubled; parity 0 new.
Agent: fullstack-developer + tester.

## 3. Risks & Gates

### Protected flows (DO NOT BREAK)
| Flow | Location | Risk | Mitigation |
|---|---|---|---|
| NOWPayments IPN | `src/gateway.py:34,109` → `src/raas/nowpayments_router.py` → `nowpayments_webhook_handler.py:98` | HIGH — behavior change breaks payment activation | Golden byte-identical response tests BEFORE swap; dedicated sequential lane (Wave B); old path kept until adapter proven; handler signature frozen |
| License gate | `src/middleware/license_gate` | MEDIUM — T9 import repoint could touch it | T9 grep confirms no license_gate files import adapters.llm (verified: none do); parity gate catches regressions |
| Payment flow generally | checkout/polar routes | LOW — untouched | No lane owns these files |

### Hard gates (every wave, every commit)
1. **Parity gate** — baseline `.orchestrate/latest/failset_baseline.txt` (277 lines, keeps "FAILED " prefix). Command:
   ```
   python3 -m pytest tests/ -q --tb=no --ignore=tests/e2e --ignore=tests/test_world_model.py --continue-on-collection-errors > out.txt 2>&1
   grep -E "^FAILED" out.txt | sed 's/ -.*//' | sort -u > new.txt
   comm -13 .orchestrate/latest/failset_baseline.txt new.txt   # MUST be EMPTY
   ```
2. **Workflow freeze** — `.github/workflows/*` MUST NOT be touched on feat/sc4-next-10-tasks (owned by PR #7). Any diff there = lane violation.
3. **Lint** — `python3 -m ruff check src/ tests/` clean.
4. **Harness eval** — `python3 -m src.main harness-eval --json` → 6/6.
5. **Security** — no private keys/seed phrases/wallet creation/real transactions in tests; no credentials fabricated (T2); no secrets committed.
6. **File size** — new files ≤200 lines (repo ratchet).

### Per-lane risk register
| Lane | Risk | L×I | Mitigation |
|---|---|---|---|
| T4 | pev orchestrator relies on subtle behavioral diff (bare subprocess vs threadpool wrapper) | M×M | core's threadpool wrapper is strictly safer (timeout enforcement); pev test suite is the gate |
| T5 | local sandbox tooling absent on some hosts → tests flaky | M×H | capability detection + fail-loud; tests assert either enforced OR loud refusal, never silent pass |
| T9 | 70-ref repoint misses a patch string → mock silently no-ops | M×H | scripted repoint + full grep for zero residue + boundary allowlist removal as proof |
| T10 | double-emission on run() path (start_mission guard, runtime_adapter.py:293-305) | L×M | emitter idempotent per mission_id; tests assert exactly one start/finish per mission |
| T3 | response shape drift | L×H | golden tests written from CURRENT code before any change |
| T1 | rebase conflict mis-resolution breaks CI gates | M×H | side-per-path rule stated above; CI verify post-merge |
| T8 | real server unavailable in CI | M×L | hermetic double + documented gap; integration mark |

### Rollback
Each wave commits separately. Revert = `git revert <wave-commit>`; no wave depends on another's files (ownership disjoint), so reverts don't cascade. T3 rollback restores direct router→handle_ipn call (old path preserved until swap commit).

## 4. Agent Per Step
| Step | Agent |
|---|---|
| T4, T5, T6, T7, T9, T10 implementation (Wave A, parallel) | fullstack-developer (one per lane) |
| T3 implementation (Wave B, dedicated) | fullstack-developer |
| T2 seam verification | fullstack-developer |
| T8 integration test | fullstack-developer |
| All test runs + parity gate verification | tester |
| DEPRECATION.md / core-contract.md / blocker-note updates | docs-manager |
| PR #7 rebase/force-push/merge, wave commits, PR creation | git-manager |
| Post-implementation review | code-reviewer |

## 5. Ship Plan

### Pre-deploy checklist (per wave, before commit)
- [ ] `python3 -m ruff check src/ tests/` — clean
- [ ] Parity gate — `comm -13` output EMPTY (command in §3)
- [ ] `python3 -m src.main harness-eval --json` — 6/6
- [ ] Lane tests green; no `.github/workflows/*` in diff (`git diff --name-only main... | grep workflows` EMPTY)
- [ ] New files ≤200 lines; no console statements; no secrets

### Commit sequence
1. Wave A: one commit per task (T4, T5, T6, T7, T9, T10) — conventional format, no AI references, no plan/phase IDs in messages
2. Wave B: T3 commit (golden tests first, then swap)
3. Wave C: T8 test commit; T2 blocker-note commit; T1 handled on PR #7's own branch (not this branch)

### PR + merge
- [ ] Push feat/sc4-next-10-tasks; open PR to main
- [ ] CI verify: repo CI is structurally red on main — **green-on-branch checks are the bar**; compare branch CI vs main CI, no new reds
- [ ] Coordinate ordering with PR #7: if #7 not yet merged, rebase SC4 after it lands (T1 first in Wave C)
- [ ] Squash merge SC4

### Post-merge verification
- [ ] Parity baseline re-captured on main if failset changed (expect unchanged)
- [ ] NOWPayments IPN smoke: endpoint responds (staging/prod per existing deploy flow)
- [ ] `harness-eval` 6/6 on main
- [ ] Update memory index + ship report; T2 remains escrowed (Buzz credentials), E10 deferred-with-evidence

## Unresolved Questions
- T5 local enforcement: raise-at-construction vs warn-and-mark-UNENFORCED when sandbox tooling absent — decide during implementation based on existing constructor patterns (default: fail loud).
- T8: whether the real MCP server binary is runnable in CI — determines real-subprocess vs hermetic-double path.
