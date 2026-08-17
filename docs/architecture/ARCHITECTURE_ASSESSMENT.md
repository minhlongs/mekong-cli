# Architecture Assessment

## Scores

| Dimension | Score /100 | Rationale |
|-----------|-----------|-----------|
| **Architecture** | 68/100 | Solid Protocol layer (9 Protocols + CapabilityBus + PaymentProvider). Major duplication in agent registry, billing (8 modules), memory (5 modules), CLI (2 registries). 10 identified duplications. Core is provider-neutral. Phase 2 fixed the biggest gaps (capability bus, payment abstraction, runtime expansion). |
| **Autonomy** | 42/100 | 10-step loop exists and works. But: no Buzz adapter, no HIGH-risk approval gate, no cost limit enforcement, no retry limit, no memory separation (session vs persistent), no stream/structured_output on LLMRouter, no mission-level observability, no trace correlation IDs. Governance is binary (SAFE/REVIEW/FORBIDDEN) — needs risk levels. settle_payment is a stub. |
| **Production-Readiness** | 71/100 | 6821 tests passing. Ruff clean. MIT licensed. Public repo with CI. BUT: 554 pre-existing test failures (mostly vn/ suite), 138 errors. Billing has 8+ overlapping modules. NOWPayments integration has duplicate file. Some modules are scaffolds (studio, forest). No clear ownership boundaries for billing. |

## Top 10 Architectural Risks

1. **No Buzz Integration Adapter** — Primary external trigger for autonomous mode is missing. Without it, Mekong can't receive goals from Buzz.
2. **No HIGH-Risk Approval Gate** — Autonomous runtime can execute destructive actions (drop table, rm -rf, etc.) without human approval. Safety gap.
3. **Billing Logic Scattered Across 8 Modules** — No single owner. MCU billing and RaaS billing overlap. Maintenance hazard.
4. **Agent Registration Has 5 Parallel Systems** — Registry, dispatcher, DEFAULT_PROMPTS dict, markdown files, ROLE_HUB_MAP. Drift is guaranteed.
5. **No Cost Limit Enforcement** — estimate_cost() exists but is never checked. Autonomous loop could exhaust budget.
6. **No Memory Separation** — Session memory never cleared. Long-running sessions leak memory. No TTL eviction.
7. **No Retry Limit on repair()** — Infinite repair loop possible on persistent failures. Resource exhaustion risk.
8. **Memory Has No Single Owner** — 5 memory modules. No transaction boundary. Partial writes on failure.
9. **NOWPayments Has Duplicate File** — `nowpayments_checkout.py` + `nowpayments-checkout.py`. One is stale. Confusion risk.
10. **settle_payment() Is a Stub** — x402/MPP settlement returns `pending=True` with a note. No real payment settlement.

## Top 10 Highest-ROI Changes

1. **Add Buzz Adapter** (HIGH impact, MEDIUM effort) — Enables the primary use case. Small interface (3 methods).
2. **Add Approval Gate to runtime.execute()** (HIGH impact, LOW effort) — Check Governance.classify() before delegating. 20 lines of code.
3. **Consolidate Billing into MCUBilling** (HIGH impact, MEDIUM effort) — Single owner for all billing logic. Eliminates 7 modules.
4. **Add Cost Limit Check** (MEDIUM impact, LOW effort) — Check estimate_cost() against budget before LLM call.
5. **Add Retry Limit to repair()** (MEDIUM impact, LOW effort) — Add _repair_count field. Abort after N.
6. **Auto-generate DEFAULT_PROMPTS from .mekong/agents/*.md** (MEDIUM impact, LOW effort) — Eliminates prompt drift. Build script only.
7. **Delete Duplicate NOWPayments File** (LOW impact, LOW effort) — Cleanup. No functional change.
8. **Add Memory Separation (SESSION/PERSISTENT)** (MEDIUM impact, MEDIUM effort) — Fixes memory leaks. ScopedMemoryStore already exists.
9. **Add Stream/Structured Output to LLMRouter** (MEDIUM impact, MEDIUM effort) — Needed for plan generation and long tasks.
10. **Add Mission-Level Observability** (MEDIUM impact, MEDIUM effort) — Enables debugging autonomous runs. Correlation IDs.

## File-Level Implementation Order

### Phase 3: Safety + Buzz Integration
1. `src/core/buzz_adapter.py` — Buzz → Goal adapter
2. `src/core/runtime_adapter.py` — Add approval gate, cost check, retry limit
3. `tests/test_buzz_adapter.py`
4. `tests/test_runtime_safety.py`

### Phase 4: Billing Consolidation
5. `src/core/billing_adapter.py` — Unified billing interface
6. `src/raas/billing_engine.py` → wrap `MCUBilling`
7. `src/api/billing_routes.py` → canonical entry point
8. Delete `src/raas/nowpayments-checkout.py`
9. `tests/test_billing_consolidation.py`

### Phase 5: Memory + Observability
10. `src/core/memory_separation.py` — MemoryTier enum + separation logic
11. `src/core/mission_tracer.py` — Mission-level trace correlation
12. `src/core/llm_router_adapter.py` — Add stream()/structured_output()
13. `tests/test_memory_separation.py`
14. `tests/test_mission_tracer.py`

### Phase 6: Polish
15. Build script for prompt generation
16. Deprecation warnings for old APIs
17. CLI migration guide

## File Reuse / Wrap / Deprecate

### Reuse As-Is
| File | Reason |
|------|--------|
| `src/core/protocols.py` | Canonical Protocol definitions — expand only |
| `src/core/capability.py` | Phase 2 — clean, well-tested |
| `src/core/agent_registry.py` | Core registry — expand with dispatch methods |
| `src/core/mcu_billing.py` | Canonical billing — wrap others around it |
| `src/core/memory_scope.py` | Best memory impl — make canonical |
| `src/core/verifier.py` | Verification logic — reuse |
| `src/commands/deploy.py` | Cloudflare deploy — keep as adapter |

### Wrap (Adapter Pattern)
| File | Wrap Into | Reason |
|------|-----------|--------|
| `src/core/llm_client.py` | `LLMRouterAdapter` | Direct API calls → Protocol adapter |
| `src/core/provider_registry.py` | `LLMRouterAdapter` | Backend for provider selection |
| `src/raas/billing_engine.py` | `MCUBilling` | RaaS-specific billing on top of MCU |
| `src/raas/billing_core.py` | `MCUBilling` | Core billing logic → singleton |
| `src/raas/nowpayments_*.py` | `PaymentProvider` adapter | External payment → Protocol |
| `src/core/memory_client.py` | `ScopedMemoryStore` | Neural client → memory adapter |
| `src/core/memory_bridge.py` | `ScopedMemoryStore` | Protocol → implementation |

### Deprecate
| File | Replace With | Reason |
|------|-------------|--------|
| `src/core/memory.py` (basic MemoryStore) | `ScopedMemoryStore` | No isolation, no TTL |
| `src/raas/nowpayments-checkout.py` | `nowpayments_checkout.py` | Duplicate, stale |
| `src/cli/commands_registry.py` DEFAULT_PROMPTS | Generated from `.mekong/agents/*.md` | Prompt drift |
| `src/core/orchestrator.py` | `MekongCoreRuntimeImpl` | No callers found, likely dead |
| `src/api/vn_pilot_billing.py` | `api/billing_routes.py` | Overlapping billing routes |
| `src/api/vn_payments_routes.py` | `api/billing_routes.py` | Overlapping billing routes |

## Smallest v0.1 Path to Buzz + Mekong = Autonomous Runtime

### Scope
Minimum viable autonomous runtime: Buzz sends goal → Mekong plans → executes → reports result.

### Steps (4-6 hours)

1. **Create `src/core/buzz_adapter.py`** (1h)
   - `receive_goal(payload) → Goal` — parse Buzz webhook payload
   - `send_update(status, data)` — POST to Buzz callback URL
   - `receive_feedback(feedback)` — parse feedback, update plan
   - 60 lines. No new dependencies.

2. **Add approval gate to `runtime_adapter.py`** (30min)
   - In `execute()`: call `self._governance.classify(task)` before delegating
   - If FORBIDDEN: return `Result(error="Action forbidden", success=False)`
   - If REVIEW_REQUIRED: emit telemetry, require approval callback
   - 20 lines.

3. **Add retry limit to `runtime_adapter.py`** (15min)
   - Add `_repair_count: int = 0` field
   - In `repair()`: increment, abort if > MAX_REPAIR_RETRIES (3)
   - 10 lines.

4. **Add cost check to `runtime_adapter.py`** (15min)
   - In `execute()`: call `self._llm_router.estimate_cost()` before LLM call
   - If cost > budget: return `Result(error="Budget exceeded", success=False)`
   - 15 lines.

5. **Wire Buzz adapter into runtime** (30min)
   - Add `buzz_adapter` parameter to `MekongCoreRuntimeImpl.__init__()`
   - In `run()`: if buzz_adapter set, call `receive_goal()` instead of parsing string
   - 20 lines.

6. **Write integration test** (1h)
   - Mock Buzz payload → Goal → runtime.run() → Result
   - Verify: goal parsed, plan generated, task executed, result reported
   - `tests/test_buzz_integration.py`

7. **End-to-end smoke test** (30min)
   - Start API server
   - POST Buzz webhook payload
   - Verify goal processed, result returned
   - 30 lines of curl/bash.

### Deliverable
- `src/core/buzz_adapter.py` (60 lines)
- Modified `src/core/runtime_adapter.py` (+80 lines)
- `tests/test_buzz_adapter.py` (1 test)
- `tests/test_buzz_integration.py` (1 integration test)
- `tests/test_runtime_safety.py` (3 tests: approval gate, cost check, retry limit)

### What v0.1 Does NOT Include
- Stream/structured_output on LLMRouter
- Memory separation (SESSION/PERSISTENT)
- Mission-level observability
- Real x402/MPP settlement (stub is fine)
- Cloudflare adapter (deploy stays separate)
- Multi-goal mission planning
- Human-in-the-loop feedback loop (receive_feedback stub only)

### Success Criteria
- `python3 -m pytest tests/test_buzz_adapter.py tests/test_buzz_integration.py tests/test_runtime_safety.py -v` — 100% pass
- `python3 -m ruff check src/core/buzz_adapter.py src/core/runtime_adapter.py` — clean
- End-to-end: curl POST → goal processed → result returned — HTTP 200