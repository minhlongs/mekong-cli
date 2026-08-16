# Plan: Architecture v0.2 — Wire Protocols to Existing Code

**Date:** 2026-08-17
**Mode:** auto --parallel
**Scope:** Make Protocol layer real by wiring existing implementations

## Brainstorm Contract

**Outcome:** Protocol layer has zero orphaned code — every Protocol has at least one conforming implementation, every implementation satisfies its Protocol, runtime adapter is callable from CLI.

**Constraints:**
- No production regressions — all 6910 passing tests stay green
- ruff clean — 0 new lint errors
- Preserve working business funnels (Zalo OA, Tax/Accounting, AI Video Factory)
- YAGNI: thin adapters only, no rewrites
- Zero new dependencies

**Non-goals:**
- Don't merge memory systems (5 files serve distinct purposes)
- Don't rewrite existing billing (tier_config.py stays dormant for now)
- Don't add OTel full support
- Don't implement x402/MPP real settlement (speculative)
- Don't change CLI command surface

**Acceptance Criteria:**
1. `protocols.py` — Plan/Step/PlanStatus defined once (canonical), removed from runtime_adapter.py and goal_engine.py
2. `mcu_billing.py` — `check_quota(org_id)` method added (wraps existing `get_balance()`)
3. `runtime_adapter.py` — sync (no async/await), correctly calls sync deps
4. `src/core/memory_store_adapter.py` — NEW thin adapter wrapping memory.py → MemoryStore Protocol
5. `src/core/telemetry_sink_adapter.py` — NEW thin adapter wrapping telemetry_collector.py → ObservabilitySink Protocol
6. `src/core/llm_router_adapter.py` — NEW thin adapter wrapping daemon/llm_router.py → LLMRouter Protocol
7. `src/commands/run.py` — NEW CLI command `mekong run --goal "..."` wired to MekongCoreRuntimeImpl
8. ruff 0 errors, pytest passes for touched modules
9. Protocol conformance test verifies 7/9 implementations satisfy Protocols

## Scout Summary

- `src/core/protocols.py` — 193 lines, 9 Protocols + supporting types
- `src/core/runtime_adapter.py` — 269 lines, MekongCoreRuntimeImpl with async methods
- `src/core/goal_engine.py` — 203 lines, GoalEngineImpl (sync), already has inject defense
- `src/core/mcu_billing.py` — 402 lines, MCUBilling with record_usage (log-only), no check_quota
- `src/core/tool_registry.py` — 586 lines, FULLY CONFORMS 4/4 ToolRegistry Protocol
- `src/core/memory.py` — 394 lines, MemoryStore with record()/query()/semantic_search()
- `src/core/telemetry_collector.py` — 370 lines, TelemetryCollector with collect_event()
- `src/core/verifier.py` — 484 lines, RecipeVerifier missing explain()
- `src/daemon/llm_router.py` — LLMRouter with route() method
- `src/commands/` — 43 existing command modules
- `tests/test_protocol_compliance.py` — 5 smoke tests, passes

## Implementation Steps

### Step 1: Unify Plan/Step/PlanStatus (protocols.py)
Move canonical definitions to protocols.py, delete from runtime_adapter.py and goal_engine.py.

### Step 2: Extend MCUBilling (mcu_billing.py)
Add check_quota() method (wrapper around get_balance()).

### Step 3: Fix runtime_adapter.py
Remove async from MekongCoreRuntimeImpl methods. Fix billing.deduct() → billing.record_usage()/check_quota().

### Step 4: Create 3 adapter files
- src/core/memory_store_adapter.py (~50 lines)
- src/core/telemetry_sink_adapter.py (~50 lines)
- src/core/llm_router_adapter.py (~60 lines)

### Step 5: Create CLI command
- src/commands/run.py (~30 lines)

### Step 6: Test
- Run ruff + pytest on touched modules
- Protocol conformance tests

## File Changes

| File | Action | Lines |
|------|--------|-------|
| `src/core/protocols.py` | MODIFY — add Plan/Step/PlanStatus canonical | +10 |
| `src/core/runtime_adapter.py` | MODIFY — remove duplicate types, fix async/sync | ~50 changes |
| `src/core/goal_engine.py` | MODIFY — remove duplicate Plan/Step types | -10 |
| `src/core/mcu_billing.py` | EXTEND — add check_quota() | +15 |
| `src/core/memory_store_adapter.py` | CREATE | ~50 |
| `src/core/telemetry_sink_adapter.py` | CREATE | ~50 |
| `src/core/llm_router_adapter.py` | CREATE | ~60 |
| `src/commands/run.py` | CREATE | ~30 |
| `tests/test_protocol_conformance.py` | CREATE | ~60 |