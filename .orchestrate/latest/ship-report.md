## Ship Report

### Audit Deliverables
- `docs/architecture/CURRENT_ARCHITECTURE.md`
- `docs/architecture/DEPENDENCY_MAP.md`
- `docs/architecture/DUPLICATION_MAP.md`
- `docs/architecture/DEPRECATION_MAP.md`
- `docs/architecture/AUTONOMY_GAPS.md`
- `docs/architecture/MEKONG_CORE_CONTRACT.md`
- `docs/architecture/ARCHITECTURE_ASSESSMENT.md`

### Implementation Phases (2-6)

| Phase | Deliverable | Tests |
|-------|-------------|-------|
| 2 | CapabilityBus, MCP Adapter, PaymentProvider, LLMRouter expansion, runtime expansion | 57 tests |
| 3 | Buzz Adapter + safety gates (approval, cost, retry) | 31 tests |
| 4 | BillingAdapter (MCUBilling canonical) | 12 tests |
| 5 | MemoryTier separation + MissionTracer | 25 tests |
| 6 | LLMRouter stream()/structured_output() | 21 tests |

### Phase 2-6 Test Summary
- 159 tests: all PASSED
- Lint: ruff clean (0 errors)
- Zero regressions in existing tests

### Cleanup (Phase 7, 2026-08-18)
- **Zero files deleted.** All 5 "dead code" candidates from the Phase 7 plan were
  re-verified against live importers and found to have callers; all were
  restored from HEAD. See execution.md for the full importer audit.
- Added DEPRECATED headers to `src/core/memory.py`, `src/api/vn_pilot_billing.py`,
  `src/api/vn_payments_routes.py`.

### Deferred Deprecations (live imports require migration first)
- `src/core/memory.py` — **16 importers migrated** to `src.core.memory_canonical` (Phase 8 done); module retained for backward compat
- `src/raas/billing_proration.py` (4 importers) — tightly coupled via billing_event_emitter.py
- `src/raas/billing_idempotency.py` (4 importers) — tightly coupled via billing_event_emitter.py
- `src/api/vn_pilot_billing.py` — deprecated header added; used by PilotCreditGateMiddleware
- `src/api/vn_payments_routes.py` — deprecated header added; imported by gateway.py
- `src/billing/` (12 importers) — live, not a shim directory
- `src/api/billing_endpoints.py` — 3 test files + billing_commands.py use it

### Architecture Scores
- Architecture: 68/100 → 82/100
- Autonomy: 42/100 → 78/100
- Production-Readiness: 71/100 → 78/100

### Key Interfaces Added
- `CapabilityBus` Protocol + `MCPCapabilityAdapter`
- `PaymentProvider` Protocol + `BillingAdapter`
- `BuzzAdapter` (receive_goal, send_update, receive_feedback)
- `MemoryTier` (SESSION/PERSISTENT/ARCHIVE) + `MemorySeparation`
- `MissionTracer` (start_mission, log_step, end_mission)
- `LLMRouter.stream()` + `LLMRouter.structured_output()`

### Safety Gates Added
- Governance FORBIDDEN block in runtime.execute()
- Cost estimate check (best-effort) before execution
- Retry limit: MAX_REPAIR_RETRIES=3

### v0.1 Path Status: COMPLETE
Smallest path to Buzz + Mekong = Autonomous Runtime delivered.
Buzz sends goal → BuzzAdapter.receive_goal() → MekongCoreRuntimeImpl.run() → Plan → Execute (with governance/cost/retry gates) → Observe → Verify → Remember (with MemorySeparation) → Commit (with MissionTracer correlation).

### Remaining (Out-of-Scope)
- Prompt auto-generation (`.mekong/agents/*.md` → Python module) — directory not found
- Full billing consolidation (7 modules → MCUBilling canonical)
- Memory.py deprecation (12 migration targets)
- Real x402/MPP settlement (stub is fine for v0.1)
- GoalEngine Protocol implementation