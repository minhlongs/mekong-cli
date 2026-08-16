# Mekong CLI — Dependency Map

**Date:** 2026-08-17
**Scope:** Complete cross-module import graph for all src/ and engine/ modules
**Author:** docs-manager

---

## Summary

The Mekong CLI codebase has **src/core/** as its gravitational center — 143 files outside core import from it, making it the single highest-risk module to change. Three bidirectional dependency loops exist: **core <-> harness** (via PEV checkpoint and memory adapters), **core <-> raas** (via CreditStore in billing and hybrid_router), and **engine <-> src** (via billing config and license store in 24+ files). Sixteen leaf modules under src/ are never imported by anything else and are safe candidates for deprecation. The engine/ subsystem has a hard boundary violation: engine files import from src.core, src.db, and src.lib, preventing clean separation.

---

## Module-Level Dependency Graph

```
                          ┌─────────────────┐
                          │   src/seed/      │  (foundational: tiers, config, types)
                          │   fan-out: 4     │
                          └───────┬─────────┘
                                  │ imported by core, api, db, cli
                                  ▼
┌──────────┐   ┌─────────┐   ┌──────────┐   ┌──────────┐
│ src/     │   │ src/    │   │ src/     │   │ src/     │
│ daemon/  │──>│ core/   │<──│ harness/ │   │ raas/    │
│ fan: 3   │   │ fan:143 │   │ fan: 5   │   │ fan: 33  │
└──────────┘   └────┬────┘   └──────────┘   └────┬─────┘
                    │                             │
         ┌──────────┼──────────                  │ (credits, billing)
         ▼          ▼          ▼                  ▼
   ┌──────────┐ ┌──────┐ ┌──────────┐    ┌──────────────┐
   │ src/api/ │ │ src/ │ │ src/cli/ │    │  engine/     │
   │ fan: 8   │ │auth/ │ │ fan: 5   │    │ billing +    │
   └──────────┘ │fan:13│ └──────────┘    │ license +    │
                └──────┘                  │ payments     │
                                          └──────────────┘
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ src/db/  │ │src/lib/  │ │src/      │
   │ fan: 29  │ │fan: 14   │ │services/ │
   └──────────┘ └──────────┘ │fan: 15   │
                              └──────────┘

Fan-out = number of files outside the module that import from it.
```

---

### Core -> Harness Dependencies

These are **src/core/ files importing from src/harness/**:

| Core File | Harness Import | Import Type |
|-----------|---------------|-------------|
| `src/core/pev_checkpoint.py:8` | `src.harness.pev.checkpoint.CheckpointStore, PipelineCheckpoint, _utc_now` | Module-level |
| `src/core/adapters/pev_adapter.py:19` | `src.harness.pev.memory.MemoryStore` | Lazy (inside method) |

**Assessment:** The checkpoint import is a hard dependency. The adapter import is lazy/conditional. Core delegates real PEV implementations to harness, creating a circular loop since harness imports 28 core modules.

### Harness -> Core Dependencies

28 files in `src/harness/` import from `src/core/`. The most heavily imported core modules by harness:

| Core Module | Imported By (harness files) | Count |
|-------------|---------------------------|-------|
| `src.core.nlu` | `pev/nlu.py`, `pev/parser.py` | 2 |
| `src.core.llm_client` | `pev/executor.py`, `pev/planner.py` | 2 |
| `src.core.circuit_breaker` | `pev/executor.py` | 1 |
| `src.core.command_sanitizer` | `pev/executor.py`, `pev/verifier.py` | 2 |
| `src.core.verifier` | `pev/executor.py` | 1 |
| `src.core.memory_bridge` | `pev/orchestrator.py` | 1 |
| `src.core.tool_registry` | `pev/executor.py` | 1 |
| `src.core.browser_agent` | `pev/executor.py` | 1 |
| `src.core.crash_detector` | `pev/executor.py` | 1 |
| `src.core.retry` | `pev/executor.py` | 1 |
| `src.core.pev_metrics_collector` | `pev/metrics_collector.py`, `pev/health_checks.py`, `pev/dashboard_data.py` | 3 |
| `src.core.pev_dashboard_data` | `pev/dashboard_data.py` | 1 |
| `src.core.pev_health_checks` | `pev/health_checks.py` | 1 |
| `src.core.pev_structured_logger` | `pev/structured_logger.py` | 1 |
| `src.core.health_endpoint` | `pev/health_checks.py` | 1 |

Plus 13 additional files in `src/harness/core/`, `src/harness/agents/`, `src/harness/orchestration/`, and `src/harness/observability/` that import from core.

### Core Internal Dependencies

| Concern | Files Involved | Lines | Severity |
|---------|---------------|-------|----------|
| **3 error hierarchies** | `exceptions.py`, `pev_errors.py`, `error_responses.py` | 253 total | MEDIUM — inconsistent error handling across pipeline |
| **2 memory systems** | `memory.py`, `vector_memory_store.py`, `memory_bridge.py` (adapter) | ~600 | LOW — adapter pattern bridges them |
| **2 orchestrator hierarchies** | `src/core/orchestrator/` (30K lines), `src/harness/pev/orchestrator_pkg/` (1,195 lines) | 31,195 | HIGH — duplication, divergent behavior |

---

### LLM Provider Dependencies

Four provider implementations exist with a tiered fallback chain:

```
┌─────────────────────────────────────────────────────┐
│  src/core/providers.py (canonical, 458 lines)       │
│  OpenAIProvider | AnthropicProvider |                │
│  LiteLLMProvider | MekongOfable-5              │
├─────────────────────────────────────────────────────┤
│  src/core/llm_client.py (canonical, 500+ lines)     │
│  get_client() → routes through providers.py         │
├─────────────────────────────────────────────────────┤
│  src/core/fallback_chain.py (185 lines)              │
│  execute_with_fallback() → tries providers in order  │
├─────────────────────────────────────────────────────┤
│  src/core/tier_fallback_chain.py (140 lines)         │
│  Per-tier model selection chains                     │
└─────────────────────────────────────────────────────┘

Duplicate layers (being phased out):
├── src/harness/core/providers.py  (imports from core.providers)
├── src/harness/core/llm_client.py (imports from core.llm_client)
├── src/harness/core/router.py     (ALGO dup, 328 lines)
└── src/daemon/dispatcher.py       (separate, 316 lines)
```

**Import chain (canonical):**
`hybrid_router.py` -> `task_classifier.py` -> `model_selector.py` -> `cost_estimator.py` -> `mcu_gate.py` -> `fallback_chain.py` -> `providers.py` / `llm_client.py`

**Risk:** Changing `providers.py` (fan-out: affects `hybrid_router`, `llm_client`, `fallback_chain`, `harness/core/providers`, `harness/core/router`, `daemon/dispatcher`).

---

### Billing Dependencies

Three billing systems, one active:

| System | Entry Point | Tier Enum | Status |
|--------|-------------|-----------|--------|
| **MCU Billing** | `src/core/mcu_billing.py` | `TierKey` (src/seed/config/tiers.py) | **LIVE** |
| **Engine Billing** | `engine/billing/tier_rate_limit_middleware.py` | `Tier` (engine/billing/tier_config.py) | **DORMANT** — never mounted |
| **Engine Payments** | `engine/payments/usage_meter.py` | `Tier` (engine/license/license_metadata.py) | **PARTIAL** |

**Import relationships:**

```
src/core/mcu_billing.py ──uses──> src/seed/config/tiers.TierKey (canonical)
                  │
                  └──uses──> src/raas.credits.CreditStore

engine/billing/ ──uses──> src/lib/rate_limiter_factory.TierRateLimiter
                 ──uses──> src/services.license_enforcement.LicenseStatus
                 ──uses──> src/db/tier_config_repository.TierConfigRepository

engine/payments/ ──uses──> src/db/repository.LicenseRepository
                  ──uses──> src/core/logging_config.get_logger

engine/license/  ──uses──> src/core/logging_config.get_logger
                  ──uses──> src/db.repository.get_repository
```

**5 Tier enum definitions** exist across the codebase: `TierKey` (canonical), 2x `Tier` in engine, `TIER_LIMITS` in engine/license, and `DEFAULT_TIER_CONFIGS` in engine/billing.

---

## Circular Dependency Chains

| Chain | Files | Severity | Resolution |
|-------|-------|----------|------------|
| **core <-> harness** | `src/core/pev_checkpoint.py:8` imports `src.harness.pev.checkpoint` | HIGH | Move `CheckpointStore` into core; harness delegates |
| **core <-> harness** | `src/core/adapters/pev_adapter.py:19` imports `src.harness.pev.memory.MemoryStore` | MEDIUM | Lazy import — mitigated but fragile |
| **core <-> raas** | `src/core/mcu_billing.py:117` imports `src.raas.credits.CreditStore` | HIGH | mcu_billing is production-critical; CreditStore should live in core or seed |
| **core <-> raas** | `src/core/hybrid_router.py:290` imports `src.raas.credits.CreditStore` | HIGH | Same as above — breaks if raas changes CreditStore |
| **core <-> raas** | `src/raas/*.py` imports 9 core modules (hybrid_router, mcu_gate, event_bus, etc.) | HIGH | raas depends heavily on core; core partially depends on raas |
| **core <-> daemon** | `src/core/telegram_bot/ops_handlers.py:68` imports `src.daemon.heartbeat_scheduler` | LOW | Lazy import in event handler |
| **engine <-> src** | 24 files in engine/ import from src.core, src.db, src.lib, src.services | HIGH | engine boundary is not clean — engine cannot exist independently |

---

## External Dependency Inventory

Key third-party packages from `pyproject.toml`:

| Package | Version | Used By | Risk |
|---------|---------|---------|------|
| `fastapi` | ^0.109.0 | src/gateway.py, src/api/*, src/core/gateway/* | Core HTTP framework |
| `uvicorn[standard]` | ^0.27.0 | src/gateway.py | Server runtime |
| `typer` | >=0.12.0 | src/main.py, src/cli/* | CLI framework |
| `rich` | ^13.7.0 | src/cli/* | CLI rendering |
| `pydantic` | ^2.5.0 | All API models, configs | Data validation |
| `httpx` | ^0.27.0 | src/core/llm_client, src/core/providers | HTTP client for LLM providers |
| `stripe` | ^7.10.0 | src/api/billing_endpoints, engine/payments | Payment processing |
| `sentry-sdk` | ^2.0.0 | src/core/sentry_init.py | Error tracking |
| `litellm` | >=1.60.0 | src/core/providers.py | Multi-provider LLM routing |
| `lancedb` | ^0.17.0 | src/core/vector_memory_store.py | Vector DB for memory |
| `python-jose` | ^3.3.0 | src/auth/*, engine/license/* | JWT handling |
| `sqlalchemy` | >=2.0.0 | src/db/database.py | Database ORM |
| `celery` | ^5.3.0 | src/forest/inngest/ | Task queue (partial) |

---

## Module Risk Classification

| Module | Fan-out | Risk Level | Notes |
|--------|---------|------------|-------|
| **src/core/** | 143 | **CRITICAL** | Single highest-risk module; every subsystem imports from it |
| **src/raas/** | 33 | **HIGH** | Billing/payment gateway; bidirectional with core |
| **src/db/** | 29 | **HIGH** | Database layer; imported by core, api, auth, cli, engine |
| **src/command_fabric/** | 24 | **MEDIUM** | 15 CLI commands depend on it; safe to change with grep |
| **src/services/** | 15 | **MEDIUM** | Business logic services; imported by api, cli, engine |
| **src/lib/** | 14 | **MEDIUM** | Utility layer; rate limiting, raas_gate helpers |
| **src/auth/** | 13 | **MEDIUM** | Auth; imported by core, api, gateway, middleware |
| **src/api/** | 8 | **LOW** | HTTP routes; depends on core but rarely imported |
| **src/models/** | 7 | **LOW** | Data models; imported by auth, raas, services |
| **src/engine/** (billing+license+payments) | 6 | **MEDIUM** | Bidirectional with src — cannot be cleanly separated |
| **src/harness/** | 5 | **HIGH** | Being phased out but still imported by core, cli |
| **src/cli/** | 5 | **LOW** | CLI commands; depends on core but rarely imported by others |
| **src/seed/** | 4 | **LOW** | Foundation; imported by core, db, api |
| **src/config/** | 4 | **LOW** | Config; imported by engine, core |
| **src/daemon/** | 3 | **LOW** | Background workers; depends on core.file_lock |
| **src/middleware/** | 3 | **LOW** | FastAPI middleware; depends on core, auth |
| **src/usage/** | 3 | **LOW** | Usage tracking; imported by core |
| **src/analytics/** | 4 | **LOW** | Analytics; imported by core |

---

## Leaf Nodes (Safe to Deprecate)

These 16 modules are **never imported** by any other module in the codebase:

| Module | Path | Action |
|--------|------|--------|
| `src/a2ui/` | `src/a2ui/` | Candidate for removal |
| `src/ai/` | `src/ai/` | Candidate for removal |
| `src/commercial/` | `src/commercial/` | Candidate for removal |
| `src/components/` | `src/components/` | Candidate for removal |
| `src/finance/` | `src/finance/` | Candidate for removal |
| `src/i18n/` | `src/i18n/` | Candidate for removal |
| `src/jobs/` | `src/jobs/` | Candidate for removal |
| `src/marketing/` | `src/marketing/` | Candidate for removal |
| `src/observability/` | `src/observability/` | Candidate for removal (core has own `sentry_init.py`) |
| `src/old/` | `src/old/` | Candidate for removal (archive) |
| `src/pages/` | `src/pages/` | Candidate for removal |
| `src/plugins/` | `src/plugins/` | Candidate for removal |
| `src/research/` | `src/research/` | Candidate for removal |
| `src/strategies/` | `src/strategies/` | Candidate for removal |
| `src/studio/` | `src/studio/` | Candidate for removal |
| `src/tests/` | `src/tests/` | Candidate for removal (main tests in `tests/`) |

**Removing these 16 modules would reduce the codebase surface area without breaking any imports.** Verify each for hidden CLI command wiring via `src/commands/` or `src/cli/` before deleting.

---

## Confidence Level

**HIGH** — All import chains verified by `grep -rn` across the full source tree. Cross-references confirmed in source files. Fan-out counts computed from actual `from src.X.` patterns.

---

## Cross-references

| Report | Path |
|--------|------|
| Core Module Map | `plans/reports/step2-core-module-map.md` |
| PEV Engine Map | `plans/reports/step3-pev-engine-map.md` |
| LLM Router Trace | `plans/reports/step6-llm-router-trace.md` |
| Billing/Payment Map | `plans/reports/step8-billing-payment-map.md` |
| Architecture Doc | `docs/system-architecture.md` |
| Code Standards | `docs/code-standards.md` |
