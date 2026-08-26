# Mekong Architecture — Autonomous Runtime v0.1

> Refreshed: 2026-08-26 · Branch state: `ada77e6b41` · Scope: v0.1 foundation
> ("smallest correct foundation" — see
> [IMPLEMENTATION_PLAN.md](./architecture/IMPLEMENTATION_PLAN.md) for the full
> audit-to-action mapping).

Mekong CLI is an open-source autonomous runtime for Solo Companies and Solo
Vibe Coders: one operator delegates goals to AI agents that plan, execute,
verify, repair, and pay for tools — on your own infrastructure.

## Component map (text diagram)

```
 External callers                CLI surface (36 Typer groups via build_app())
 ───────────────                 ─────────────────────────────────────────────
 Buzz / webhook payload ──┐      mekong run --goal "..."  [src/commands/run.py]
                          │                  │
                          ▼                  ▼
        ┌──────────────────────────────────────────────────────────┐
        │            MekongCoreRuntimeImpl                         │
        │            src/core/runtime_adapter.py                   │
        │                                                          │
        │  goal → plan → delegate → execute → observe → verify     │
        │        → repair (≤3) → remember → commit                 │
        │                                                          │
        │  run()           : plain text entry, idempotent mission   │
        │  run_from_payload(): Buzz entry, pre-assigned mission_id │
        │  execute() gates : governance → capability → cost        │
        └───────┬──────────────────┬──────────────────┬─────────────┘
                ▼                  ▼                  ▼
   ┌────────────────────┐ ┌─────────────────┐ ┌──────────────────────┐
   │ CapabilityBus      │ │ Governance      │ │ PaymentProvider       │
   │ InMemory impl;     │ │ ONE decision    │ │ BillingAdapter (MCU), │
   │ BUILTIN/CLI/MCP    │ │ path: risk map  │ │ MockPaymentProvider,  │
   │ sources via        │ │ + audit + loud  │ │ x402-shape codec      │
   │ adapters           │ │ auto-approve    │ │ (mock-only)           │
   └────────────────────┘ └─────────────────┘ └──────────────────────┘
                │                  │                  
                ▼                  ▼                  
   ┌────────────────────┐ ┌─────────────────────────────────────────┐
   │ ToolRegistry / MCP │ │ ExecutionRuntime Protocol               │
   │ adapter            │ │ LocalExecutionRuntime: subprocess +     │
   │ (sync_from_mcp)    │ │ sandboxed fs + sanitizer + timeouts     │
   └────────────────────┘ │ (Cloudflare/Docker = planned, not built)│
                          └─────────────────────────────────────────┘

 Outbound updates: BuzzAdapter.send_update → injectable (url,payload)->int
 transport; silent no-op without callback_url. Core never requires Buzz.
```

## The four buses in one page

| Bus | Doc | Entry class | v0.1 state |
|-----|-----|-------------|------------|
| Lifecycle (core contract) | [core-contract.md](./core-contract.md) | `MekongCoreRuntimeImpl` | Wired; pinned by contract tests |
| Capabilities | [capability-bus.md](./capability-bus.md) | `InMemoryCapabilityBus` | Injected into `mekong run` by default |
| Economic | [economic-bus.md](./economic-bus.md) | `PaymentProvider` protocol | Interface + mock/x402-shape providers |
| Buzz/runtime | [buzz-runtime-adapter.md](./buzz-runtime-adapter.md) | `BuzzRuntimeAdapter` | Versioned `v0.1`, in-process |

Execution isolation is documented in
[runtime-adapters.md](./runtime-adapters.md); the risk/approval model in
[autonomy-model.md](./autonomy-model.md).

## Design rules enforced by tests

1. **One lifecycle engine** — no second goal→commit loop outside
   `runtime_adapter.py` (`tests/test_core_lifecycle_contract.py`).
2. **Provider-neutral core** — no vendor SDK imports in `src/core/`
   (`tests/test_core_boundary.py`; `llm_client.py` is the single documented
   transitional exception).
3. **One policy decision path** — every execution decision flows through
   `Governance.classify_risk` with mandatory audit entries.
4. **No custody** — economic code never touches keys, wallets, or networks.
5. **Buzz-optional core** — buzz import only lazily inside
   `run_from_payload`.

## Known limitations (honest list)

- `plan()`/`delegate()` remain single-step stubs.
- `LLMRouter.stream()` yields one chunk (no native streaming);
  `tool_call()` is still missing from the protocol.
- MemoryStore protocol has zero conformant implementations (3-way split).
- Network policy in `LocalExecutionRuntime` is a deny-all placeholder struct,
  not an enforcement layer.

Full gap analysis: [architecture/ARCHITECTURE_AFTER_PHASE_2.md](./architecture/ARCHITECTURE_AFTER_PHASE_2.md).
