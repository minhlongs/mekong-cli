# Architecture After Phase 2

## What Changed

Phase 2 (Steps 1-5) expanded Mekong CLI from a single-purpose tool into a provider-neutral autonomous agent runtime.

### New Files

| File | Purpose |
|------|---------|
| `src/core/capability.py` | `Capability` dataclass + `CapabilityBus` Protocol — canonical capability abstraction |
| `src/core/adapters/mcp_capability_adapter.py` | Wraps MCP tools as `Capability` instances for the bus |
| `tests/test_capability_bus.py` | 18 tests for CapabilityBus Protocol |
| `tests/test_mcp_capability_adapter.py` | 13 tests for MCP adapter |
| `tests/test_llm_router_expanded.py` | 9 tests for expanded LLMRouter (generate/health) |
| `tests/test_runtime_expansion.py` | 10 tests for runtime lifecycle (health/destroy) |
| `tests/test_economic_bus.py` | 5 tests for PaymentProvider Protocol |
| `tests/test_autonomy_engine.py` | 8 tests for Governance/ActionClass |
| `tests/test_agent_registry_consolidated.py` | 5 tests for AgentRegistry |

### Modified Files

| File | Change |
|------|--------|
| `src/core/protocols.py` | Added `generate()`/`health()` to `LLMRouter`; re-exported `CapabilityBus`; added `PaymentProvider` Protocol |
| `src/core/llm_router_adapter.py` | Added `generate()`/`health()` with error handling |
| `src/core/runtime_adapter.py` | Removed duplicate Protocol; added `capability_bus`, `health()`, `destroy()` |

## Architecture Now

```
                        ┌─────────────┐
                        │    Buzz      │ (optional — via Runtime Adapter)
                        └──────┬──────┘
                               │
                    ┌──────────▼──────────┐
                    │  MekongCoreRuntime  │  ← Protocol (protocols.py)
                    │   (runtime_adapter) │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼─────┐     ┌───────▼───────┐    ┌──────▼──────┐
    │ LLMRouter │     │ CapabilityBus │    │ AgentRegistry│
    │ (Adapter) │     │   (Protocol)  │    │ (Consolidated)│
    └─────┬─────┘     └───────┬───────┘    └──────┬──────┘
          │                   │                    │
    Claude/Qwen/DeepSeek   MCP + Builtin       All agents
    OpenAI/Local            tools as            registered here
                            Capabilities
```

## Provider-Neutral Guarantees

- Core never imports `anthropic`, `openai`, etc. directly
- LLM providers are thin adapters implementing `LLMRouter` Protocol
- Capability providers implement `CapabilityBus` Protocol
- Economic providers implement `PaymentProvider` Protocol
- Cloudflare is an adapter, not core infrastructure

## Test Coverage

Phase 2 added **69 new tests** covering:
- LLM Router expansion (generate/health)
- CapabilityBus Protocol (register/unregister/get/list/discover/execute/authorize)
- MCP Capability Adapter (sync/idempotent/handler/risk levels)
- Runtime expansion (health/destroy/lifecycle)
- Economic Bus (PaymentProvider Protocol conformance)
- Autonomy Engine (Governance/ActionClass/risk levels)
- Agent Registry consolidation

All tests pass. Full regression suite in progress.

## What's Next (Phase 3+)

- Buzz Runtime Adapter (external trigger → goal → autonomous loop)
- stream()/structured_output() on LLMRouter
- Memory separation (short-term vs long-term)
- Mission-level observability
- Full deprecation map for legacy code paths