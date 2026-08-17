# Dependency Map

## Core Protocol Dependencies

```
protocols.py (canonical)
  ├── capability.py (re-exported)
  ├── runtime_adapter.py (imports Plan, PlanStatus, Step)
  ├── llm_router_adapter.py (imports LLMRouter)
  ├── mcp_capability_adapter.py (imports Capability)
  ├── tests/test_*.py (import Protocol types)
  └── Future: Buzz adapter, stream adapters
```

## Runtime Dependency Chain

```
main.py / gateway.py
  ├── commands_registry.py (CLI dispatch)
  │     └── 43 command modules (src/cli/*.py, src/commands/*.py)
  ├── runtime_adapter.py
  │     ├── protocols.py (MekongCoreRuntime Protocol)
  │     ├── llm_router_adapter.py
  │     ├── capability.py (CapabilityBus)
  │     ├── memory_store_adapter.py
  │     ├── verifier.py
  │     └── telemetry
  └── api/gateway routes (FastAPI)
        ├── billing_routes.py → mcu_billing.py
        ├── raas_billing_service.py → raas/billing_engine.py
        └── vn_payments_routes.py → nowpayments_router.py
```

## Billing Dependency Chain

```
mcu_billing.py (MCUBilling singleton)
  ├── db/schema.py (tier config, usage records)
  ├── protocols.py (PaymentProvider Protocol)
  └── raas/nowpayments_*.py (external payment)

raas/billing_engine.py
  ├── mcu_billing.py
  ├── billing_core.py
  ├── billing_idempotency.py
  └── nowpayments_webhook_handler.py → NOWPayments IPN
```

## Agent System Dependencies

```
agent_registry.py (AgentRegistry)
  ├── seed/agents/*.py (AgentBase subclasses)
  ├── .mekong/agents/*.md (prompt files)
  └── protocols.py (AgentDispatcher Protocol)

runtime_adapter.py
  └── agent_registry.py (via AgentDispatcher)
```

## Memory Dependencies

```
memory_store_adapter.py (MemoryStoreAdapter)
  ├── core/memory.py (MemoryStore)
  ├── core/memory_client.py (NeuralMemoryClient)
  ├── core/memory_bridge.py (MemoryBridge Protocol)
  └── core/memory_scope.py (ScopedMemoryStore)
```

## Key External Dependencies

| Module | External Dependency | Purpose |
|--------|--------------------|---------|
| llm_router.py | OpenRouter API | LLM routing |
| llm_client.py | anthropic/openai libs | Direct LLM calls |
| mcp_server.py | MCP protocol | Tool execution |
| nowpayments_*.py | NOWPayments API | Crypto payments |
| inngest/ | Inngest cloud | Event queue |
| db/schema.py | SQLite/Postgres | Data persistence |
| gateway.py | FastAPI, uvicorn | API server |

## Circular Dependency Risk

- `protocols.py` re-exports `CapabilityBus` from `capability.py` — safe (one-way)
- `runtime_adapter.py` imports from `protocols.py` only — safe
- `mcp_capability_adapter.py` imports from both `capability.py` and `protocols.py` — safe
- No identified circular dependencies in Phase 2 additions

## Orphaned/Disconnected Components

| Component | Status | Issue |
|-----------|--------|-------|
| `src/core/orchestrator.py` | Isolated | No callers found in src/ — may be dead code |
| `src/forest/` | Partial | inngest integration incomplete |
| `src/studio/` | Partial | Video studio scaffold only |
| `src/strategies/polymarket/` | Isolated | Separate domain, no core integration |