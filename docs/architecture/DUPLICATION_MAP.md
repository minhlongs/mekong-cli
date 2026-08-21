# Duplication Map

## Critical Duplications

### 1. Agent Registration — 4 Parallel Systems

**Status:** RESOLVED (2026-08-20)

| System | Location | Purpose | Status |
|--------|----------|---------|--------|
| `AgentRegistry` | `src/core/agent_registry.py` | Type-safe registry of `AgentBase` subclasses | **Canonical** |
| `AgentDispatcher` | Protocol in `protocols.py` | Dispatch + message chain + prompt loading | **REMOVED** — 0 importers |
| `DEFAULT_PROMPTS` | `src/core/agent_dispatcher.py` | Dict of role → prompt string | **Live** — 4 importers |
| `.mekong/agents/*.md` | Filesystem | Markdown prompt files | **Empty** — no files exist |
| `ROLE_HUB_MAP` | `src/core/agent_dispatcher.py` | Role → hub mapping | **Live** — 2 modules |

**Resolution:** AgentDispatcher Protocol removed. AgentRegistry is the single
canonical dispatch surface. DEFAULT_PROMPTS remains the only prompt source
(no markdown files to generate from). ROLE_HUB_MAP is live in agent_dispatcher.

### 2. Billing — 8+ Modules

**Status:** DEFERRED — MEDIUM RISK (2026-08-20)

| Module | Purpose |
|--------|---------|
| `src/core/mcu_billing.py` | MCU billing singleton |
| `src/raas/billing_engine.py` | RaaS billing core |
| `src/raas/billing_core.py` | Core billing logic |
| `src/raas/billing_proration.py` | Proration logic |
| `src/raas/billing_idempotency.py` | Idempotency |
| `src/api/billing_routes.py` | Billing REST routes |
| `src/api/raas_billing_service.py` | RaaS billing service |
| `src/api/vn_pilot_billing.py` | VN pilot billing |
| `src/api/vn_payments_routes.py` | VN payment routes |

**Impact:** Billing logic scattered across `src/core/`, `src/raas/`, `src/api/`. All modules live with distinct importers.

**Consolidation target:** `MCUBilling` should be the canonical billing core. `raas/billing_engine.py` should wrap `MCUBilling` + add RaaS-specific logic. Payment routes should delegate to one billing service.

**Why deferred:** All 8+ modules have live importers. Merging requires dedicated review of each module's specific requirements.

### 3. Memory — 5 Modules

**Status:** PARTIALLY RESOLVED (2026-08-20)

| Module | Purpose | Status |
|--------|---------|--------|
| `src/core/memory.py` | Backward-compat shim (11 lines) | **Shim** — re-exports from memory_canonical |
| `src/core/memory_canonical.py` | Real implementation (396 lines) | **Canonical** |
| `src/core/memory_client.py` | `NeuralMemoryClient` (vector-like client) | **Live** — unique features |
| `src/core/memory_bridge.py` | `MemoryBridge` Protocol | **Live** — 2 importers |
| `src/core/memory_store_adapter.py` | Adapter bridging MemoryBridge → MemoryStore | **Live** — 2 importers |
| `src/core/memory_scope.py` | `ScopedMemoryStore` (org-scoped entries) | **Live** — tested |

**Resolution:** memory.py migrated to shim re-exporting from memory_canonical.py. All 5 modules live with distinct importers. ScopedMemoryStore is the best candidate for canonical, but migration requires updating all callers.

**Why deferred:** All modules have live importers. Migration requires dedicated work.

### 4. NOWPayments Integration — 2 Versions

**Status:** DONE (2026-08-20)

Deleted `nowpayments-checkout.py` and `nowpayments-webhook-handler.py` (hyphen
versions). Verified byte-identical to underscore versions. Updated `test_billing.py`
to reference canonical underscore files.

### 5. LLM Routing — 3 Systems

**Status:** RESOLVED (2026-08-21)

| Module | Purpose |
|--------|---------|
| `src/core/llm_router.py` | Router with classify/select_model/estimate_cost |
| `src/core/llm_client.py` | Direct LLM API calls (32 callers) |
| `src/core/provider_registry.py` | Provider registry |

**Resolution:** `LLMRouterAdapter` now delegates to `LLMClient` (real production
logic — failover, caching, hooks, circuit breaker). Adapter satisfies `LLMRouter`
Protocol and is wired as the default in `runtime_adapter.py`. 3 routing systems
remain (daemon `LLMRouter` in `src/daemon/llm_router.py` is a separate concern
for capability-based mission routing), but the adapter no longer stubs — it
wraps `LLMClient` for Protocol-compatible callers.

### 6. CLI Commands — 2 Registries

**Status:** RESOLVED (2026-08-20)

| Registry | Location | Count | Status |
|----------|----------|-------|--------|
| `src/cli/commands_registry.py` | Aggregator | 43 commands | **Aggregator** — imports from src/commands/ |
| `src/commands/` | Click modules | 20 files | **Canonical** — all commands defined here |

**Resolution:** src/commands/ is the canonical Click command registry.
commands_registry.py is the aggregator that imports and wires them. No
duplication — different layers of the same system.

### 7. Billing Routes — 4 Overlapping

**Status:** DEFERRED — MEDIUM RISK (2026-08-20)

| Module | Purpose |
|--------|---------|
| `src/api/billing_routes.py` | General billing routes |
| `src/api/raas_billing_service.py` | RaaS billing service |
| `src/api/vn_pilot_billing.py` | VN pilot billing |
| `src/api/vn_payments_routes.py` | VN payment routes |

**Impact:** Four API modules for billing. All live with distinct importers.

**Why deferred:** Each module serves a different consumer. Merging requires
dedicated review of each module's specific requirements.

## Minor Duplications

### 8. Prompt Storage — Dict + Filesystem + Code

**Status:** DEFERRED (2026-08-20)

- `DEFAULT_PROMPTS` dict in `agent_dispatcher.py` — **live, 4 importers**
- `.mekong/agents/*.md` markdown files — **empty, no files exist**
- `AgentMeta.prompt` field in `AgentRegistry` — **live**

**Fix:** Create `.mekong/agents/*.md` as single source of truth, then
auto-generate `DEFAULT_PROMPTS` at build time. Deferred — no markdown
source exists yet.

### 9. Tier Config — Multiple Sources

**Status:** FALSE POSITIVE (2026-08-20)

- `src/seed/config/tiers.py` — pricing/credits/features (canonical)
- `src/db/tier_config_repository.py` — rate limiting config (DB-backed)
- `src/api/tier_config_routes.py` — REST API for rate limit management

These serve different concerns despite both having `TierConfig` classes:
- `tiers.py` = business pricing/credits
- `tier_config_repository.py` = rate limiting infrastructure

No consolidation needed.

### 10. Error Handling Patterns

**Status:** LOW PRIORITY (2026-08-20)

- `try/except` + `return {"error": ...}` in `runtime_adapter.py`
- `try/except` + `Result(error=...)` in `orchestrator.py`
- `try/except` + `{"status": "error"}` in `llm_router_adapter.py`

**Fix:** Standardize on `Result` Protocol for all error returns. LOW priority — no
immediate action needed. Patterns are consistent within each module.
