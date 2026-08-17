# Duplication Map

## Critical Duplications

### 1. Agent Registration — 4 Parallel Systems

| System | Location | Purpose |
|--------|----------|---------|
| `AgentRegistry` | `src/core/agent_registry.py` | Type-safe registry of `AgentBase` subclasses |
| `AgentDispatcher` | Protocol in `protocols.py` | Dispatch + message chain + prompt loading |
| `DEFAULT_PROMPTS` | `src/cli/commands_registry.py` | Dict of role → prompt string |
| `.mekong/agents/*.md` | Filesystem | Markdown prompt files |
| `ROLE_HUB_MAP` | `src/core/agent_registry.py` | Role → hub mapping |

**Impact:** Agent discovery has 5 entry points. `AgentRegistry.list()` returns names, `DEFAULT_PROMPTS` has prompts, `.mekong/agents/*.md` has markdown versions. None are automatically synchronized.

**Consolidation target:** `AgentRegistry` + `AgentDispatcher` already merged. `DEFAULT_PROMPTS` should be auto-generated from `.mekong/agents/*.md`. `ROLE_HUB_MAP` should be a field on `AgentMeta`.

### 2. Billing — 8+ Modules

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

**Impact:** Billing logic scattered across `src/core/`, `src/raas/`, `src/api/`. No single owner. MCU billing and RaaS billing are separate systems with overlapping concerns (usage tracking, quota, payment).

**Consolidation target:** `MCUBilling` should be the canonical billing core. `raas/billing_engine.py` should wrap `MCUBilling` + add RaaS-specific logic. Payment routes should delegate to one billing service.

### 3. Memory — 5 Modules

| Module | Purpose |
|--------|---------|
| `src/core/memory.py` | `MemoryEntry` + `MemoryStore` (basic dict store) |
| `src/core/memory_client.py` | `NeuralMemoryClient` (vector-like client) |
| `src/core/memory_bridge.py` | `MemoryBridge` Protocol |
| `src/core/memory_store_adapter.py` | Adapter bridging MemoryBridge → MemoryStore |
| `src/core/memory_scope.py` | `ScopedMemoryStore` (org-scoped entries) |

**Impact:** Memory has 5 layers for what should be one system. `MemoryStore` is a basic dict. `MemoryBridge` is a Protocol. `ScopedMemoryStore` adds org isolation. `MemoryStoreAdapter` bridges them. `NeuralMemoryClient` is separate.

**Consolidation target:** `ScopedMemoryStore` should be the canonical implementation. `MemoryBridge` Protocol should be the interface. `MemoryStoreAdapter` should be the bridge. `MemoryStore` (basic) should be deprecated.

### 4. NOWPayments Integration — 2 Versions

| Module | Purpose |
|--------|---------|
| `src/raas/nowpayments_checkout.py` | NOWPayments checkout |
| `src/raas/nowpayments-checkout.py` | Duplicate with hyphen naming |

**Impact:** Two files with hyphen vs underscore naming. Likely one is stale.

**Consolidation target:** Delete `nowpayments-checkout.py` (hyphen version), keep `nowpayments_checkout.py`.

### 5. LLM Routing — 3 Systems

| Module | Purpose |
|--------|---------|
| `src/core/llm_router.py` | Router with classify/select_model/estimate_cost |
| `src/core/llm_client.py` | Direct LLM API calls |
| `src/core/provider_registry.py` | Provider registry |

**Impact:** Three systems for the same job. `llm_router.py` routes to providers. `llm_client.py` makes direct calls. `provider_registry.py` registers providers.

**Consolidation target:** `LLMRouterAdapter` (Phase 2) should be the canonical entry. `llm_client.py` should become an adapter. `provider_registry.py` should be a backend for the adapter.

### 6. CLI Commands — 2 Registries

| Registry | Location | Count |
|----------|----------|-------|
| `src/cli/commands_registry.py` | 43 commands | Click-based |
| `src/commands/` | deploy + others | Mixed |

**Impact:** Two command systems. `commands_registry.py` uses Click decorators. `src/commands/deploy.py` is standalone.

**Consolidation target:** All commands should go through `commands_registry.py`. `src/commands/` should be migrated.

### 7. Billing Routes — 4 Overlapping

| Module | Purpose |
|--------|---------|
| `src/api/billing_routes.py` | General billing routes |
| `src/api/raas_billing_service.py` | RaaS billing service |
| `src/api/vn_pilot_billing.py` | VN pilot billing |
| `src/api/vn_payments_routes.py` | VN payment routes |

**Impact:** Four API modules for billing. No clear ownership boundary.

**Consolidation target:** `billing_routes.py` should be canonical. Others should delegate or be merged.

## Minor Duplications

### 8. Prompt Storage — Dict + Filesystem + Code

- `DEFAULT_PROMPTS` dict in `commands_registry.py`
- `.mekong/agents/*.md` markdown files
- `AgentMeta.prompt` field in `AgentRegistry`

**Fix:** Single source = `.mekong/agents/*.md`. Auto-generate `DEFAULT_PROMPTS` at build time.

### 9. Tier Config — Multiple Sources

- `src/seed/config/tiers.py` — canonical
- `src/db/tier_config_repository.py` — DB-backed
- `src/api/vn_pricing.py` — VN-specific pricing

**Fix:** `tiers.py` is source of truth. Others should import from it.

### 10. Error Handling Patterns

- `try/except` + `return {"error": ...}` in `runtime_adapter.py`
- `try/except` + `Result(error=...)` in `orchestrator.py`
- `try/except` + `{"status": "error"}` in `llm_router_adapter.py`

**Fix:** Standardize on `Result` Protocol for all error returns.