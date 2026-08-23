# Architecture Assessment

Refreshed: 2026-08-23 · HEAD: 0878f966f

Re-scored from the 13-category re-audit consolidated in `.orchestrate/latest/step4_findings.md`. Prior scores (architecture 68 · autonomy 42 · production-readiness 71) date from the pre-PR#2 baseline. Corrections applied this refresh: `orchestrator.py` references now point to the `src/core/orchestrator/` package (modularized in 8f4a62633); test totals updated to 7525 passed / 223 failed / 83 skipped at HEAD; the Phase 4 billing-consolidation test (test_billing_consolidation.py) was planned but never created and is tracked as an open follow-up.

## Scores

| Dimension | Score /100 | Δ vs prior | Rationale |
|-----------|-----------|------------|-----------|
| **Architecture** | **66** | −2 | Protocol layer intact and growing, PR#2 swept real dead weight — but the audit surfaced 4 critical defects (broken prod run path, dead MCP adapter, unsandboxed scheduler, masked broken imports) and the MemoryStore split is unresolved. |
| **Autonomy** | **55** | +13 | Every gap from the prior rationale now has implemented, tested code (Buzz adapter, governance, cost guard, retry cap, memory separation, tracing) — but prod wiring leaves 5 closures inert or crashing, and plan()/delegate() are stubs. |
| **Production-Readiness** | **72** | +1 | Test health improved sharply (692 failing/erroring → 223) and ruff is clean, but the flagship `mekong run` path raises AttributeError and the funnel CLI surface is gutted (wizard deleted, 16 advertised commands missing). |

### Architecture 68 → 66 (per-point deltas)

- **+3** — PR#2 deleted 142 files / −29k lines of dead code; billing storage converged to a single owner, `src/raas/credits.py` (CreditStore), with `src/billing/` reduced to facade-only (step4 cats 2/5).
- **+1** — Core primitives strengthened: 10 Protocols live in `src/core/protocols.py`; `src/core/runtime_adapter.py` is primitive-ready (constructor accepts every Protocol) (cat 7).
- **−3** — Four critical defects at HEAD: `mekong run` crashes on `_NullTelemetry` lacking `emit()` (`src/commands/run.py:54-57` vs `src/core/runtime_adapter.py:324`); MCP capability adapter imports nonexistent `MCPServer` (`src/core/adapters/mcp_capability_adapter.py:55`) so capability sync discovers zero tools; daemon scheduler executes dropped-in file contents as raw shell (`src/daemon/scheduler.py:100`); three broken imports masked by fallbacks (`src/command_fabric/router.py:25`, `src/cli/commands/implement/__init__.py:188`, `src/agents/agi_bridge.py:34`) (cats 10/12/13).
- **−2** — MemoryStore 3-way split unresolved: `src/core/memory_canonical.py` (~20 consumers) vs `src/core/memory_store.py` JSONL vs the `protocols.MemoryStore` Protocol (`src/core/protocols.py:172`) with zero exact conformers; tenants.db has 6 writer modules (cat 14).
- **−1** — Orchestration fragmentation persists: 4 parallel stacks (`src/core/orchestrator/` RecipeOrchestrator, `src/mekongcli/core/goal_engine/` GoalEngine, `src/harness/pev/` PEV, `src/daemon/`) (cat 1).

### Autonomy 42 → 55 (per-point deltas)

- **+12** — Six previously-absent safety/observability subsystems shipped as real code: `src/core/governance.py:28-134` (classify + request_approval), `max_cost_usd` ceiling (`src/core/runtime_adapter.py:417-426`), retry cap `_MAX_REPAIR_ATTEMPTS = 3` (`src/core/runtime_adapter.py:116`), `src/core/memory_separation.py`, `src/core/mission_tracer.py` + `src/core/telemetry_collector.py`.
- **+8** — Integration layer landed: `src/core/buzz_adapter.py:40-65` (receive_goal/send_update/receive_feedback), `run_from_payload` (`src/core/runtime_adapter.py:191`), CapabilityBus + ToolRegistry wired, and loop stages execute/observe/verify/repair/remember/commit all real (cat 9).
- **−5** — Production wiring inert or crashing: `src/commands/run.py:37-45` constructor omits `governance=`, `max_cost_usd=`, tracer → approval gate, cost guard and mission tracing never engage; `_NullTelemetry` (`src/commands/run.py:54-57`) lacks the `emit()` invoked unconditionally at `src/core/runtime_adapter.py:324` → AttributeError kills the first observe().
- **−2** — Loop intelligence stubbed: `plan()` emits a single step (`src/core/runtime_adapter.py:232-234`), `delegate()` assigns all steps to one agent (`src/core/runtime_adapter.py:236-238`), and the prod `_NullDispatcher.dispatch` raises NotImplementedError (`src/commands/run.py:47-51`).
- *(0)* — Closures 4/5/6/10/11 hold at class level (no regression from PR#2 — 11/11 still closed) but are weakened in practice by the two items above; Buzz `send_update` builds a dict and never POSTs (`src/core/buzz_adapter.py:61-63`), already netted into the −5.

### Production-Readiness 71 → 72 (per-point deltas)

- **+5** — Suite health: 692 failing/erroring tests at prior baseline → 223 failed / 83 skipped at HEAD, with 7525 passing; ruff clean.
- **+2** — Rot removal: 142 files / −29k lines deleted in PR#2; billing storage single-writer convergence on CreditStore (`src/raas/credits.py`); license gating intact post-deletion (`src/lib/raas_gate/__init__.py:64-243`, `src/middleware/license_gate.py:52`).
- **−3** — Flagship prod path broken: `mekong run` raises AttributeError at first observe() (`src/commands/run.py:54-57` vs `src/core/runtime_adapter.py:324,389`) — the autonomous entry point is dead-on-arrival.
- **−2** — Funnel surface gutted: the vn-setup wizard was deleted in PR#2; 16 advertised commands are missing from the live binary (vn-setup, billing, trace, license, tier-admin, monitor, usage, auth, raas, sync-raas, activate, deploy-all, test, lint, clean, ci); Zalo OA (`src/commands/zalo_oa.py`), tax libs (`src/commands/thue_dnvn.py`, `src/commands/ke_toan.py`) have no CLI registration in `src/cli/app_setup.py`.
- **−1** — Repo self-description stale: CLAUDE.md cites tree/forest/land source layers (none exist anywhere in the repo) and claims "43 commands" vs 53 live; COMMAND_REGISTRY.md claims 43 wired.

## Top 10 Architectural Risks

1. **Daemon scheduler is unsandboxed arbitrary shell execution** — Any file dropped in the watch dir has its entire text run via `executor.run_shell()` with full user privileges and a 1800s timeout; no CommandSanitizer, no allowlist, no approval. Weakest link in the repo. Evidence: `src/daemon/scheduler.py:100`; contrast the fail-closed path in `src/core/tool_registry.py:274-289`.
2. **`mekong run` production path crashes** — `_NullTelemetry` defines only `record_event()`, but `runtime_adapter` calls `.emit()` unconditionally → AttributeError at first observe(); verified statically. Evidence: `src/commands/run.py:54-57`, `src/core/runtime_adapter.py:324,389`.
3. **Safety gates exist but are not wired in production** — Runtime gates fire only if governance/max_cost/tracer are injected; the prod constructor omits all three, making the approval gate and cost guard INERT. Evidence: gates at `src/core/runtime_adapter.py:254-278`, omission at `src/commands/run.py:37-45`.
4. **GOVERNANCE_AUTO_APPROVE environment bypass** — Any REVIEW-class action is auto-approved when the env var is set; combined with risk 3, a single env var disables human oversight. Evidence: `src/core/governance.py:117,124-134`.
5. **MCP capability adapter silently discovers zero tools** — Imports nonexistent `MCPServer` (real class `MekongMcpServer`, `src/core/mcp_server.py:165`); try/except swallows the failure. Second bug: `_handle_{tool_name}` misses the `cc_` prefix. Tests mask both with MagicMock. Evidence: `src/core/adapters/mcp_capability_adapter.py:55,85`.
6. **Masked broken imports (silent fallbacks)** — `src/command_fabric/router.py:25` imports nonexistent `cli.tui.router` module (ModuleNotFoundError verified); `src/cli/commands/implement/__init__.py:188` imports `SQLiteGoalStore` from the wrong module (real home: `src/mekongcli/core/goal_engine/store.py:31`) → silent subprocess fallback; `src/agents/agi_bridge.py:24,34` spawns nonexistent worker JS → `mekong agi start` dead-on-arrival.
7. **Four parallel orchestration stacks** — Stack A `src/core/orchestrator/` (canonical, 15+ importers), Stack B `src/mekongcli/core/goal_engine/`, Stack C `src/harness/pev/` (its `src/harness/pev/planner.py` is BYTE-IDENTICAL to `src/core/planner.py`, cmp-verified; `src/harness/pev/dag_scheduler.py` is a 19-line stub vs core's 220-line scheduler), Stack D `src/daemon/`. Drift guaranteed (cat 1).
8. **Funnel orphaning** — Zalo OA code intact but unregistered (reachable only via `python -m`); tax/accounting libs have no CLI entry; Sophia has no command surface; the vn-setup wizard is gone. Revenue funnels are invisible to binary users. Evidence: `src/cli/app_setup.py` (no registrations), `src/commands/zalo_oa.py`, `src/commands/thue_dnvn.py`, `src/commands/ke_toan.py`.
9. **Memory ownership split with zero Protocol conformers** — `protocols.MemoryStore` (`src/core/protocols.py:172`) has no exact implementation; YAML+vector (`src/core/memory_canonical.py`) vs JSONL (`src/core/memory_store.py`) split consumers; tenants.db written by 6 modules; mission traces in-memory only (`src/core/mission_tracer.py`). Partial-write risk on failure (cat 14).
10. **Settlement is a stub and NOWPayments bypasses the payment Protocol** — `settle_payment` returns `pending=True` unconditionally; NOWPayments router is mounted directly in the gateway, bypassing `PaymentProvider` (`src/core/protocols.py:207`); `estimate_cost` silently zeroes. Evidence: `src/core/mcu_billing.py:318-340`, `src/gateway.py:34,109`.

## Top 10 Highest-ROI Changes

| # | Change | Effort | Why high ROI | Files touched |
|---|--------|--------|--------------|---------------|
| 1 | Fix run.py wiring: swap `_NullTelemetry` for `TelemetryCollector`, inject `governance`, `max_cost_usd`, tracer | **S** | Unblocks 5 weakened autonomy closures (4/5/6/10/11) in one edit; turns inert gates on; fixes the crash in risk 2 | `src/commands/run.py` (+ reuse `src/core/telemetry_collector.py`, `src/core/governance.py`, `src/core/mission_tracer.py`) |
| 2 | Fix MCP adapter: import `MekongMcpServer`, honor `cc_` prefix in handler lookup | **S** | Restores capability sync from 25 exposed tools; currently the entire MCP→Capability bridge is dead while appearing green in tests | `src/core/adapters/mcp_capability_adapter.py`, its test file |
| 3 | Sandbox the daemon scheduler: route through CommandSanitizer strict mode + allowlist + approval for non-allowlisted content | **M** | Closes the only arbitrary-shell-exec hole (risk 1); the sanitizer already exists and is proven in `tool_registry` | `src/daemon/scheduler.py`, reuse `src/core/command_sanitizer.py` |
| 4 | Converge planner/verifier duplicates: delete byte-identical PEV planner, unify verifiers, replace or grow the 19-line DAG stub | **M** | Removes a whole drift class between Stack A and Stack C with near-zero behavioral risk (files are identical/divergent copies) | `src/harness/pev/planner.py` (delete; import `src/core/planner.py`), `src/harness/pev/verifier.py` → `src/core/verifier.py`, `src/harness/pev/dag_scheduler.py` |
| 5 | Delete confirmed dead-code batch | **S** | Zero-importer deletions verified by the audit; shrinks attack/maintenance surface immediately | See Deprecate/Delete table below |
| 6 | Register or delete the 3 unregistered Typer apps | **S** | billing/pev/usage command code is written and tested but invisible; either ship it or cut it | `src/cli/billing_commands.py`, `src/cli/pev_commands.py`, `src/cli/usage_commands.py`, `src/cli/app_setup.py` |
| 7 | Implement real plan()/delegate() (multi-step plans, multi-agent delegation) | **L** | Converts the loop from single-shot executor to actual autonomous planner; biggest autonomy lever | `src/core/runtime_adapter.py`, conform `src/mekongcli/core/goal_engine/service.py` to `protocols.GoalEngine` (`src/core/protocols.py:198`) |
| 8 | MemoryStore convergence: one conformer over canonical store, migrate JSONL consumers | **M** | Eliminates partial-write/dual-source risk (risk 9); ~20 consumers already on canonical side | `src/core/memory_canonical.py`, `src/core/memory_store.py` consumers, new adapter under `src/core/adapters/` |
| 9 | Concrete x402/MPP PaymentProvider implementation | **L** | Turns the settlement stub into real revenue rail; unblocks HTTP-402 middleware and receipt verification | wrap `src/raas/nowpayments_checkout.py` behind `src/core/protocols.py` PaymentProvider via `src/core/billing_adapter.py`; remount `src/raas/nowpayments_router.py` |
| 10 | Restore funnel command registration | **M** | Reconnects the three business funnels (Zalo, tax, Sophia entry) to the binary; direct revenue visibility | `src/cli/app_setup.py`, `src/commands/zalo_oa.py`, `src/commands/thue_dnvn.py`, `src/commands/ke_toan.py`, new vn-setup module |

## File-Level Implementation Order

### Wave 1 — Wiring fixes (unblock what exists)
1. `src/commands/run.py` — replace `_NullTelemetry` with `src/core/telemetry_collector.py`; inject `governance=` (`src/core/governance.py`), `max_cost_usd=`, `mission_tracer=` (`src/core/mission_tracer.py`) into the `MekongCoreRuntimeImpl` constructor call
2. `src/core/adapters/mcp_capability_adapter.py` — import `MekongMcpServer` from `src/core/mcp_server.py`; fix `cc_` prefix handling in handler resolution
3. `src/command_fabric/router.py` — repair the `cli.tui.router` import (target lives at `src/cli/tui/router.py`)
4. `src/cli/commands/implement/__init__.py` — import `SQLiteGoalStore` from `src/mekongcli/core/goal_engine/store.py`
5. `src/agents/agi_bridge.py` — guard or restore the missing worker entry before spawning node
6. Update the MagicMock-masked tests for items 2–5 to assert real behavior

### Wave 2 — Safety
7. `src/daemon/scheduler.py` — require CommandSanitizer strict mode (`src/core/command_sanitizer.py`), allowlist, and approval for watch-dir content before `run_shell`
8. `src/core/governance.py` — gate or log-alert the `GOVERNANCE_AUTO_APPROVE` bypass
9. `src/core/tool_registry.py` — no change; reference implementation for the strict pattern above

### Wave 3 — Dead code (audit-verified deletions)
10. Delete: `src/api/polar_webhook.py.legacy`, `tests/api/test_polar_webhook.py.legacy`
11. Delete: `src/old/` (a2ui copy, zero importers)
12. Delete: `src/core/founder_vc/__init__.py`, `src/core/founder_ipo/__init__.py` (docstring-only shells)
13. Delete: `src/daemon/llm_router.py`, `src/daemon/llm_config.py` (zero importers post-f7d420c75)
14. Delete: `src/harness/sops-engine/` (empty stub), `src/harness/observability/raas_auth/` (always-False stub; real client is the `src/core/raas_auth/` package, 9 importers)
15. Deprecate→Delete: `src/core/tracing.py` (test-only consumers; overlaps `src/core/telemetry_collector.py`)
16. Remove dead export: `setup_telemetry` in `src/core/telemetry/sdk_setup.py` (gateway uses `src/core/telemetry_init.py`)
17. Delete zero-reference zenos scripts under `workflows/scripts/`
18. Decide-and-execute on KEEP-flagged items: fold root `cli/tui/streaming.py` into `src/cli/tui/`; register or delete `src/cli/billing_commands.py`, `src/cli/pev_commands.py`, `src/cli/usage_commands.py` via `src/cli/app_setup.py`

### Wave 4 — Convergence
19. Delete `src/harness/pev/planner.py` (byte-identical to `src/core/planner.py`); repoint importers
20. Merge `src/harness/pev/verifier.py` into `src/core/verifier.py`
21. Resolve `src/harness/pev/dag_scheduler.py`: adopt `src/core/orchestrator/` scheduling or grow the stub — do not keep both
22. MemoryStore convergence: add a `protocols.MemoryStore` conformer backed by `src/core/memory_canonical.py` under `src/core/adapters/`; migrate `src/core/memory_store.py` consumers (design_intelligence, dispatcher, memory command)
23. Correct stale metadata: CLAUDE.md layer map and command count; COMMAND_REGISTRY.md

### Wave 5 — New capabilities
24. `src/core/runtime_adapter.py` — real multi-step `plan()` and multi-agent `delegate()`
25. Conform `src/mekongcli/core/goal_engine/service.py` to `protocols.GoalEngine` (`src/core/protocols.py:198`)
26. `src/core/buzz_adapter.py` — real async POST in `send_update` + payload schema validation
27. Concrete PaymentProvider: wrap `src/raas/nowpayments_checkout.py` behind `src/core/billing_adapter.py`; remount `src/raas/nowpayments_router.py` through the protocol in `src/gateway.py`
28. Funnel restoration: register `src/commands/zalo_oa.py` in `src/cli/app_setup.py`; add thin CLI entries for `src/commands/thue_dnvn.py` / `src/commands/ke_toan.py`; rebuild the vn-setup wizard as a registered command

## Reuse / Wrap / Deprecate

### Reuse As-Is (build on these)
| File | Reason |
|------|--------|
| `src/core/runtime_adapter.py` | Canonical primitive-ready runtime; constructor already accepts every gate — just inject |
| `src/core/protocols.py` | 10 live Protocols; expand only |
| `src/core/capability.py` | Clean Capability/CapabilityBus model, well-tested |
| `src/core/buzz_adapter.py` | Buzz integration seam exists; needs real transport only |
| `src/core/mcp_server.py` | 25 tools exposed via FastMCP stdio/SSE; server side works |
| `src/core/llm_router_adapter.py` | Provider-neutral LLM access behind Protocol |
| `src/core/mcu_billing.py` | Canonical MCU billing singleton (1 MCU = 1 credit) |
| `src/raas/credits.py` | CreditStore — converged single-writer billing storage target |
| `src/core/governance.py` | Classify/request_approval/audit implemented; wire, don't rewrite |
| `src/core/mission_tracer.py` | Mission trace correlation; add persistence later |
| `src/core/telemetry_collector.py` | Drop-in replacement for `_NullTelemetry` |
| `src/core/tool_registry.py` | Strict fail-closed sanitizer pattern — copy into scheduler |

### Wrap (adapt behind Protocols)
| Source | Wrap Into | Reason |
|--------|-----------|--------|
| `src/raas/nowpayments_checkout.py` | `PaymentProvider` adapter (`src/core/protocols.py:207`) via `src/core/billing_adapter.py` | External payments currently mounted raw, bypassing the Protocol |
| `src/harness/pev/executor.py` PEV loop | Capability adapter over `src/core/capability.py` | Harness execution becomes one capability source among several |
| `src/mekongcli/core/goal_engine/service.py` | `protocols.GoalEngine` conformer (`src/core/protocols.py:198`) | Implemented engine, but not yet a Protocol conformer |

### Deprecate / Delete (audit verdicts)
| Target | Verdict | Evidence |
|--------|---------|----------|
| `src/api/polar_webhook.py.legacy` + `tests/api/test_polar_webhook.py.legacy` | DELETE | 0 importers; superseded by `src/api/webhooks/router.py` revenue_router |
| `src/old/` | DELETE | a2ui duplicate, zero importers |
| `src/core/founder_vc/__init__.py`, `src/core/founder_ipo/__init__.py` | DELETE | Docstring-only shells post-PR#2 |
| `src/daemon/llm_router.py`, `src/daemon/llm_config.py` | DELETE | Zero importers post-f7d420c75 |
| `src/core/tracing.py` | DEPRECATE→DELETE | Test-only consumers; overlaps `src/core/telemetry_collector.py` |
| `src/harness/sops-engine/` | DELETE | Empty stub |
| `src/harness/observability/raas_auth/` | DELETE | Always-False stub; real client `src/core/raas_auth/` has 9 importers |
| `setup_telemetry` in `src/core/telemetry/sdk_setup.py` | DELETE export | Exported, never called; gateway uses `src/core/telemetry_init.py` |
| zenos scripts under `workflows/scripts/` | DELETE | Zero references |
| Root `cli/` package | KEEP-but-flag | `cli/tui/streaming.py` is test-only; fold into `src/cli/tui/`; the `cli.tui.router` import in `src/command_fabric/router.py:25` is broken |
| `src/cli/billing_commands.py`, `src/cli/pev_commands.py`, `src/cli/usage_commands.py` | KEEP-or-REGISTER | Full Typer apps never registered in `src/cli/app_setup.py` |
| `src/harness/pev/planner.py` | DELETE (duplicate) | Byte-identical to `src/core/planner.py` (cmp-verified) |

*(Prior-assessment deprecation rows referencing paths deleted in PR#2 — the old basic memory module, legacy commands aggregator, billing_core, and the duplicate nowpayments-checkout file — are done and removed from this list.)*

## Smallest v0.1 Path: Buzz + Mekong = Autonomous Runtime

Minimal loop: Buzz sends goal → Mekong runs → reports result to Buzz callback. This is v0.1, not the full vision.

### Already exists (verified at HEAD)
- `src/core/buzz_adapter.py` — `receive_goal` (:40) parses payload; `send_update` (:61) builds the update dict; `receive_feedback` (:65)
- `src/core/runtime_adapter.py` — `run_from_payload` (:191) wraps the full stage loop; execute/observe/verify/repair/remember/commit all real
- `src/core/governance.py`, `src/core/mission_tracer.py`, `src/core/telemetry_collector.py` — gates and observability, ready to inject

### Missing (all small)
1. **Prod telemetry crashes the loop** — `_NullTelemetry` lacks `emit()` (`src/commands/run.py:54-57` vs `src/core/runtime_adapter.py:324`). Fix: construct `TelemetryCollector` instead.
2. **Gates not injected** — `src/commands/run.py:37-45` omits governance/max_cost_usd/tracer. Fix: pass them.
3. **Planning is a stub** — `plan()` emits one step (`src/core/runtime_adapter.py:232-234`). v0.1 fix: conform `src/mekongcli/core/goal_engine/service.py` and use it as the planner.
4. **Callback never transmits** — `send_update` returns a dict, never POSTs (`src/core/buzz_adapter.py:61-63`). Fix: async POST to callback URL from the payload.

### Steps (half-day)
1. Fix `src/commands/run.py`: TelemetryCollector + governance + max_cost_usd + mission_tracer injection (S)
2. Wire GoalEngine conformer as the planner in `src/core/runtime_adapter.py` (M)
3. Real POST in `src/core/buzz_adapter.py` `send_update` (S)
4. Smoke test through `run_from_payload` with a Buzz-shaped payload (S)

Explicitly out of scope for v0.1: multi-agent `delegate()`, payload HMAC/auth, capability negotiation, x402 real settlement, MCP client side, mission-trace persistence.

### Success Criteria
- `python3 -m pytest tests/ -k "buzz or runtime"` — green with no MagicMock masking of the adapter
- `python3 -m ruff check src/commands/run.py src/core/buzz_adapter.py src/core/runtime_adapter.py` — clean
- End-to-end: POST Buzz-shaped payload → goal planned (>1 step) → executed → callback received at test endpoint — HTTP 200
