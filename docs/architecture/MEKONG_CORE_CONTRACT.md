# Mekong Core Contract

## Non-Negotiable Rules

1. **Provider-neutral core** — Core never imports provider-specific libraries directly. All providers are adapters implementing Protocols.
2. **No vendor lock-in** — Buzz, Cloudflare, Anthropic, OpenAI, x402, MPP are all adapters. None are hard-coded.
3. **Structural typing** — All boundaries use `typing.Protocol` (runtime_checkable). No inheritance required.
4. **Single source of truth** — Each concept has exactly one canonical definition. Duplicates are adapters or wrappers, not independent systems.
5. **Backward compatibility** — Existing commands, APIs, and workflows must not break. Adapters wrap legacy code.
6. **YAGNI + KISS + DRY** — No speculative features. No duplicate systems. Extract shared logic.
7. **Test before commit** — 100% pass rate on new tests. Regression checks on existing tests.

## Canonical Protocols

| Protocol | Location | Purpose |
|----------|----------|---------|
| `MekongCoreRuntime` | `protocols.py` | 10-step autonomous loop |
| `LLMRouter` | `protocols.py` | Provider-agnostic LLM routing |
| `ToolRegistry` | `protocols.py` | Dynamic tool registry |
| `AgentDispatcher` | `protocols.py` | Single canonical dispatch |
| `BillingMeter` | `protocols.py` | MCU billing + settlement |
| `MemoryStore` | `protocols.py` | Single canonical memory |
| `ObservabilitySink` | `protocols.py` | OTel-compatible traces |
| `VerificationEngine` | `protocols.py` | Output verification |
| `GoalEngine` | `protocols.py` | Goal decomposition + replanning |
| `CapabilityBus` | `capability.py` (re-exported) | Capability abstraction |
| `PaymentProvider` | `protocols.py` | Payment abstraction |

## Canonical Implementations

| Protocol | Implementation | Status |
|----------|---------------|--------|
| `MekongCoreRuntime` | `MekongCoreRuntimeImpl` (runtime_adapter.py) | ✅ Phase 2 |
| `LLMRouter` | `LLMRouterAdapter` (llm_router_adapter.py) | ✅ Phase 2 |
| `CapabilityBus` | In-process dict-based (MockBus in tests) | ✅ Phase 2 |
| `PaymentProvider` | `MCUBilling` (mcu_billing.py) | ✅ (settle_payment is stub) |
| `AgentDispatcher` | `AgentRegistry` (agent_registry.py) | ✅ (partial) |
| `MemoryStore` | `MemoryStoreAdapter` → `ScopedMemoryStore` | 🔄 In progress |
| `ToolRegistry` | `MCPCapabilityAdapter` (mcp_capability_adapter.py) | 🔄 MCP only |
| `VerificationEngine` | `Verifier` (verifier.py) | 🔄 Basic |
| `ObservabilitySink` | Telemetry (telemetry/) | 🔄 Basic |
| `GoalEngine` | Not yet implemented | ❌ Missing |

## Provider Adapters

### LLM Providers
| Provider | Adapter File | Status |
|----------|-------------|--------|
| Claude (Anthropic) | Via `llm_client.py` | ✅ |
| OpenAI | Via `llm_client.py` | ✅ |
| Qwen | Via `llm_router.py` | 🔄 Router supports |
| DeepSeek | Via `llm_router.py` | 🔄 Router supports |
| Local models | Via `llm_router.py` | 🔄 Router supports |

### Capability Providers
| Provider | Adapter File | Status |
|----------|-------------|--------|
| MCP | `mcp_capability_adapter.py` | ✅ Phase 2 |
| Filesystem | Not yet | ❌ Missing |
| Shell | Not yet | ❌ Missing |
| Browser | Not yet | ❌ Missing |
| Cloudflare | Not yet | ❌ Missing |

### Economic Providers
| Provider | Adapter File | Status |
|----------|-------------|--------|
| x402 | Stub in `mcu_billing.py` | 🔄 Stub |
| MPP | Stub in `mcu_billing.py` | 🔄 Stub |
| NOWPayments | `raas/nowpayments_*.py` | ✅ |

## Invariants

1. **Core imports only from `protocols.py`** — Core modules import Protocol types from `protocols.py` only. Never import adapter implementations.
2. **Adapters import from core** — Adapters import Protocol types and implement them.
3. **No circular imports** — `protocols.py` is the leaf. No module imports `protocols.py` from within `protocols.py`.
4. **Protocols are structural** — No `@runtime_checkable` enforcement on core boundaries (kept for test convenience only).
5. **Adapters are thin** — An adapter should be <200 lines. If it's bigger, split it.
6. **Tests mirror structure** — Each Protocol has a `test_protocol_compliance.py` test. Each adapter has a `test_*_adapter.py` test.

## Anti-Patterns (Forbidden)

| Anti-Pattern | Why Forbidden | Example |
|--------------|---------------|---------|
| Core imports adapter | Breaks provider-neutral guarantee | `from src.core.llm_client import ...` in `runtime_adapter.py` |
| Hard-coded provider | Vendor lock-in | `import anthropic` in core |
| Duplicate registry | Confusion about source of truth | `DEFAULT_PROMPTS` + `.mekong/agents/*.md` |
| Binary classification | Insufficient for autonomy | `Governance.classify()` with 3 outcomes only |
| Infinite retry | Resource exhaustion | `repair()` with no limit |
| Dict-based memory | No isolation, no TTL | `MemoryStore` basic dict |