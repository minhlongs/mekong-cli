# Current Architecture (Post-Phase 2)

Refreshed: 2026-08-23 · HEAD: 0878f966f

## Overview

Mekong CLI v6.0 is an AI-operated business platform for Vietnamese one-person companies. The codebase is a single Python repository with ~830 source files under `src/`, ~376 test files, and multiple entry points.

## Layer Structure

```
mekong (CLI) / api-gateway (FastAPI :8000)
  src/api/          — 37 REST route modules (raas, billing, vn_pilot, webhooks, etc.)
  src/cli/          — Typer CLI: app_setup.py aggregator + command modules
  src/commands/     — 38 command modules (run, deploy, zalo_oa, thue_dnvn, ke_toan, ...)
  src/core/         — Protocols + implementations (runtime, llm, billing, memory, orchestrator)
  src/services/     — External service clients (Polar, org service)
  src/seed/         — Auth, DB, config, agent definitions
  src/raas/         — RaaS billing engine + NOWPayments integration + CreditStore
  src/studio/       — Video generation studio (models.py only)
  src/telemetry/    — rate_limit_metrics.py only
  src/db/           — Database ORM + migrations
  src/gateway.py    — Gateway entry point
  src/main.py       — Main entry point
```

Note: the `tree`, `forest`, and `land` layers cited in earlier docs never existed in git history and have been removed from this document.

## Key Components

### CLI Entrypoint
- `src/main.py` → `src/cli/app_setup.py` — Typer aggregator registering 53 live top-level commands (28 `add_typer` groups + direct commands). The old `commands_registry.py` (Click-based, 43 commands) was deleted in PR #2.
- Command modules live in `src/cli/*.py` (cook_command, goal_commands, ui_commands, billing_commands, etc.) and `src/commands/*.py`.
- Three full Typer apps are NOT registered in `app_setup.py` and are unreachable from the CLI: `src/cli/billing_commands.py`, `src/cli/pev_commands.py`, `src/cli/usage_commands.py`.

### Core Runtime
- `src/core/runtime_adapter.py` — `MekongCoreRuntimeImpl` implements the 10-step autonomous loop (run, goal, context, plan, delegate, execute, observe, verify, repair, remember, commit)
- `src/core/governance.py` — `Governance` class with SAFE/REVIEW_REQUIRED/FORBIDDEN classifications
- `src/core/orchestrator/` — LIVE package (modularized from the former single-file orchestrator): `runner.py` (RecipeOrchestrator), `step_executor.py`, `models.py`, `rollback.py`, `agi.py`, `display.py`. Imported by 14 src modules (cook_command, gateway, raas_router, telegram, agi_score, ...) plus 10 test files — NOT dead code.

### Protocol Layer (Phase 2)
- `src/core/protocols.py` — structural Protocols + CapabilityBus + PaymentProvider
- `src/core/capability.py` — Capability dataclass + CapabilityBus Protocol
- `src/core/llm_router_adapter.py` — Adapter implementing LLMRouter Protocol
- `src/core/adapters/mcp_capability_adapter.py` — MCP → Capability bridge (currently broken, see Critical Defects)

### Agent System
- `src/core/agent_registry.py` — AgentRegistry (list, list_agents, get, register)
- `src/seed/agents/` — Agent definitions (tester, cto, cso, etc.)
- `.mekong/agents/` — Markdown agent prompt files (empty — no files exist)

### Billing
- `src/core/mcu_billing.py` — MCUBilling singleton; storage backed by `src/raas/credits.py` CreditStore (SQLite WAL, `mcu_billing.py:150-153`)
- `src/core/billing_adapter.py` — BillingAdapter wrapping MCUBilling; the unified billing interface (replaced the deleted `billing_core.py`)
- `src/raas/billing_engine.py` — RaaS billing core
- `src/raas/nowpayments_*.py` — NOWPayments integration
- `src/api/billing_routes.py` — Billing API routes

### Memory
- `src/core/memory_canonical.py` — canonical MemoryEntry + MemoryStore (YAML + vector, ~20 consumers). The old `memory.py` was deleted in PR #2.
- `src/core/memory_store.py` — JSONL-backed MemoryStore (consumers: design_intelligence, agent_dispatcher, memory command)
- `src/core/protocols.py` — `MemoryStore` Protocol (store/retrieve/delete/search) with ZERO exact conformers — aspirational
- `src/core/memory_client.py` — NeuralMemoryClient
- `src/core/memory_bridge.py` — MemoryBridge Protocol
- `src/core/memory_store_adapter.py` — Adapter bridging to MemoryStore
- `src/core/memory_scope.py` — ScopedMemoryStore

The MemoryStore is a three-way split: `memory_store.py` (JSONL), `memory_canonical.py` (YAML+vector), and `protocols.MemoryStore` (Protocol, no exact conformers). No single canonical implementation satisfies the Protocol.

### Observability
- `src/telemetry/rate_limit_metrics.py` — the only module left in `src/telemetry/`; PR #2 removed the 976-line telemetry pipeline (hooks, uploader, commands, queries)
- `src/core/mission_tracer.py` + `src/core/telemetry_collector.py` — mission tracing lives here (in-memory only)
- `src/core/verifier.py` — Output verification

### Integration Points
- Cloudflare: referenced in `src/commands/deploy.py`, spec templates
- MCP: `src/core/mcp_server.py` (25 tools via FastMCP stdio/SSE)
- OpenRouter: LLM routing via `src/core/llm_router_adapter.py`
- NOWPayments: IPN webhook → tier activation
- Polar.sh: Webhook → org activation (legacy)

## Unmapped Subsystems (added at this refresh)

| Path | Contents | Status |
|---|---|---|
| `src/design_intelligence/` | 10 .py + `knowledge/` | LIVE, contract-compliant; 4 consumers (ui_commands, ui_study, ui_benchmark, gate_check) |
| `src/mekongcli/` | 22 files — GoalEngine stack (goal_engine, governance, memory, orchestrator, swarm, telemetry, verification) | LIVE; imported by cook_command, goal_commands, commands/implement |
| `src/mekong/` | 38 .py — particle/founder/treasury/zenpay domain | LIVE, internal only |
| `src/old/` | 4 files (a2ui copy) | DEAD — zero importers, duplicates live `src/a2ui` |
| `src/daemon/` | scheduler/jidoka/mission_control | Mostly isolated; only `heartbeat_scheduler.py` externally imported |

## Critical Defects (report-only, found at this audit)

1. **`mekong run` production path broken** — `src/commands/run.py:54-58` `_NullTelemetry` defines only `record_event()`, but `src/core/runtime_adapter.py:324,389` calls `self._telemetry.emit(...)` unconditionally → AttributeError at first observe(). Production constructor also omits `governance=`, `max_cost_usd=`, and tracer, so approval gate, cost guard, and mission tracing are all inert in prod wiring.
2. **MCP capability adapter silently broken** — `src/core/adapters/mcp_capability_adapter.py:55` imports nonexistent `MCPServer` (real class is `MekongMcpServer`, `src/core/mcp_server.py:165`); try/except swallows the error so sync_from_mcp discovers ZERO tools. Handler lookup `_handle_{tool_name}` also misses the `cc_` prefix. Tests mask this with MagicMock.
3. **Daemon scheduler = unsandboxed arbitrary shell exec** — `src/daemon/scheduler.py:100` runs the entire text of any file dropped in the watch dir via `executor.run_shell()` — no CommandSanitizer, no allowlist, no approval. Full user privileges, 1800s timeout.
4. **Masked broken imports** — `src/command_fabric/router.py:25` imports nonexistent `cli.tui.router` (real: `src/cli/tui/router.py`); `src/cli/commands/implement/__init__.py:188` imports `SQLiteGoalStore` from the wrong module (`verification` instead of `goal_engine`); `src/agents/agi_bridge.py:24,34` spawns nonexistent `apps/openclaw-worker/task-watcher.js` → `mekong agi start` dead-on-arrival.

## Funnel Reachability

The three core funnels' code is intact but none has a registered CLI command surface:

- **Zalo OA** — `src/commands/zalo_oa.py` intact and tests pass, but NOT registered in `app_setup.py`; reachable only via `python -m`.
- **Tax & Accounting** — `src/commands/thue_dnvn.py` and `src/commands/ke_toan.py` are pure libraries with no `main()` and no CLI registration; tests pass.
- **Sophia (AI Video Factory)** — no command surface in this repo; only keyword routing via `src/core/nlp_commander.py`.

The `vn_setup` onboarding wizard was deleted in PR #2, removing the one true funnel entry point. 16 commands advertised in COMMAND_REGISTRY.md are missing from the live CLI.
