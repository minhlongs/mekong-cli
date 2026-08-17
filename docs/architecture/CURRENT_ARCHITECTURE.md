# Current Architecture (Post-Phase 2)

## Overview

Mekong CLI v6.0 is an AI-operated business platform for Vietnamese one-person companies. The codebase is a single Python repository with ~150 source files, ~80 test files (6821 passing), and multiple entry points.

## Layer Structure

```
mekong (CLI) / api-gateway (FastAPI :8000)
  src/api/          — 20+ REST route modules (raas, billing, vn_pilot, etc.)
  src/cli/          — 43 Click commands + command_registry
  src/commands/     — Additional command modules (deploy, billing, autonomous)
  src/core/         — 9 Protocols + implementations (runtime, llm, billing, memory)
  src/services/     — External service clients (Polar, etc.)
  src/seed/         — Auth, DB, config, agent definitions
  src/tree/         — Domain logic (byok, telegram)
  src/forest/       — Infrastructure (inngest, quota)
  src/land/         — Business workflows (billing, payouts)
  src/raas/         — RaaS billing engine + NOWPayments integration
  src/studio/       — Video generation studio
  src/telemetry/    — Execution tracing
  src/db/           — Database ORM + migrations
  src/gateway.py    — Gateway entry point
  src/main.py       — Main entry point
```

## Key Components

### CLI Entrypoint
- `src/main.py` → `src/cli/commands_registry.py` → 43 Click commands
- Additional commands in `src/cli/billing_commands.py`, `src/cli/cook_command.py`, etc.
- `src/commands/` has deploy and other standalone commands

### Core Runtime
- `src/core/runtime_adapter.py` — `MekongCoreRuntimeImpl` implements 10-step autonomous loop (run, goal, context, plan, delegate, execute, observe, verify, repair, remember, commit)
- `src/core/governance.py` — `Governance` class with SAFE/REVIEW_REQUIRED/FORBIDDEN classifications
- `src/core/orchestrator.py` — Orchestration logic

### Protocol Layer (Phase 2)
- `src/core/protocols.py` — 9 structural Protocols + CapabilityBus + PaymentProvider
- `src/core/capability.py` — Capability dataclass + CapabilityBus Protocol
- `src/core/llm_router_adapter.py` — Adapter implementing LLMRouter Protocol
- `src/core/adapters/mcp_capability_adapter.py` — MCP → Capability bridge

### Agent System
- `src/core/agent_registry.py` — AgentRegistry (list, list_agents, get, register)
- `src/seed/agents/` — Agent definitions (tester, cto, cso, etc.)
- `.mekong/agents/` — Markdown agent prompt files

### Billing
- `src/core/mcu_billing.py` — MCUBilling (MCU-based billing + x402/MPP stub)
- `src/raas/billing_engine.py` — RaaS billing core
- `src/raas/nowpayments_*.py` — NOWPayments integration
- `src/api/billing_routes.py` — Billing API routes

### Memory
- `src/core/memory.py` — MemoryEntry + MemoryStore (basic)
- `src/core/memory_client.py` — NeuralMemoryClient
- `src/core/memory_bridge.py` — MemoryBridge Protocol
- `src/core/memory_store_adapter.py` — Adapter bridging to MemoryStore
- `src/core/memory_scope.py` — ScopedMemoryStore

### Observability
- `src/telemetry/` — Execution tracing
- `src/core/verifier.py` — Output verification
- `src/forest/` — Infrastructure (inngest event queue)

### Integration Points
- Cloudflare: referenced in `src/commands/deploy.py`, spec templates
- MCP: `src/core/mcp_server.py` (25 tools)
- OpenRouter: LLM routing via `src/core/llm_router.py`
- NOWPayments: IPN webhook → tier activation
- Polar.sh: Webhook → org activation (legacy)