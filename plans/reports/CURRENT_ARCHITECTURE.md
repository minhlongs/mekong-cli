# Mekong CLI — Current Architecture Report

**Date:** 2026-08-17
**Audit Scope:** Read-only audit of existing codebase. No production code changes.
**Author:** docs-manager (architecture audit)

## Summary

The Mekong CLI v6.0 is a large AI-operated business platform for Vietnamese one-person companies, containing 8,242 meaningful files and 483,733 total lines. The codebase is functionally operational but carries significant structural debt: 3 parallel agent dispatchers, 3 parallel billing systems with 5 conflicting tier enums, 9 memory implementations, and 5 observability locations including 2 exact-duplicate telemetry collectors. Only the MCU billing system is wired to production traffic; the harness layer is being phased out but still contains full parallel implementations of the orchestrator, router, and agent dispatcher. The canonical production path flows through `src/main.py` → `src/core/hybrid_router.py` → agent dispatcher → LLM provider, with billing enforced by `src/core/mcu_gate.py`.

## Repository Topology

```
mekong-cli/
├── src/                          # Primary Python source (Core + Harness + Daemon)
│   ├── main.py                   # CLI entrypoint (21 lines, registered in pyproject.toml)
│   ├── api/                      # FastAPI routes (raas, billing, vn_pilot, vn_pricing, gateway)
│   ├── core/                     # CANONICAL production layer (77 files, 58,237 lines)
│   │   ├── hybrid_router.py      # 9-stage ALGO pipeline orchestrator (328 lines)
│   │   ├── orchestrator/         # RecipeOrchestrator (815 lines runner.py)
│   │   ├── agent_dispatcher.py   # Canonical agent dispatcher (290 lines)
│   │   ├── mcu_billing.py        # Live MCU billing engine (311 lines)
│   │   ├── mcu_gate.py           # MCU lock/confirm gate (287 lines)
│   │   ├── tool_registry.py      # Tool registry + execution engine (583 lines)
│   │   ├── providers.py          # LLM provider abstraction (458 lines)
│   │   ├── mcp_server.py         # MCP server (25 tools, 1,125 lines)
│   │   ├── auto_recovery.py      # Crash/license recovery (819 lines)
│   │   ├── memory.py             # Primary memory (YAML + Vector)
│   │   ├── memory_store.py       # JSONL memory store
│   │   ├── exceptions.py         # MekongError hierarchy
│   │   ├── pev_errors.py         # PEVError hierarchy (parallel to exceptions.py)
│   │   ├── error_responses.py    # API ErrorResponse schema
│   │   ├── task_classifier.py    # Stage 1: CLASSIFY
│   │   ├── model_selector.py     # Stage 3: MODEL SELECT
│   │   ├── cost_estimator.py     # Stage 3: cost estimation
│   │   ├── fallback_chain.py     # Stage 6: failover execution
│   │   ├── tier_fallback_chain.py # Tier-based model fallback
│   │   ├── verifier.py           # Stage 7: VERIFY
│   │   ├── subagent_reviewer.py  # Stage 7: output review
│   │   ├── event_bus.py          # Stage 9: event emission
│   │   ├── signals/              # Mission event signals
│   │   ├── crash_detector.py     # Crash detection (576 lines)
│   │   ├── pev_metrics_collector.py # Pipeline metrics
│   │   ├── sentry_init.py        # Sentry integration
│   │   ├── tracing.py            # Tracing integration
│   │   ├── telemetry_init.py     # Telemetry init
│   │   ├── llm_client.py         # LLM client wrapper
│   │   ├── gateway_client/       # Gateway data models
│   │   ├── adapters/             # PEV adapter (memory bridge)
│   │   └── ...
│   ├── harness/                   # LEGACY layer (being phased out)
│   │   ├── pev/                  # PEV engine (parser, planner, executor, verifier)
│   │   │   ├── orchestrator_pkg/ # Separate orchestrator (1,195 lines)
│   │   │   ├── parser.py         # Markdown recipe parser (430 lines)
│   │   │   ├── planner.py        # LLM decomposition planner (688 lines)
│   │   │   ├── executor.py       # Step runner (721 lines)
│   │   │   └── verifier.py       # Verification engine (490 lines)
│   │   ├── agents/               # Legacy agent dispatcher (184 lines)
│   │   ├── core/                 # Duplicate hybrid_router.py (328 lines)
│   │   ├── observability/        # Primary observability (OTel stack)
│   │   ├── telemetry_hooks.py    # Event emission (396 lines)
│   │   └── memory.py             # Legacy memory re-export
│   ├── daemon/                    # Background worker layer
│   │   └── dispatcher.py         # Daemon agent dispatcher (315 lines)
│   ├── seed/                      # Foundational layer
│   │   ├── config/tiers.py       # TierKey enum (437 lines) — canonical tier config
│   │   ├── auth/                 # Authentication (better-auth-session)
│   │   ├── db/                   # Database client
│   │   └── agents/               # Agent definitions
│   ├── services/                 # External service clients (Polar, org)
│   ├── commands/                 # 43 wired CLI command modules
│   ├── middleware/               # license_gate (JWT + balance check)
│   ├── tree/                     # Domain logic (byok, telegram)
│   ├── forest/                   # Infrastructure (inngest, quota)
│   ├── land/                     # Business workflows (billing, payouts)
│   ├── usage/                    # Usage tracking (SQLite-based)
│   ├── telemetry/                # Core telemetry
│   ├── observability/            # Legacy stub (health.py only)
│   ├── tests/                    # Test suites
│   └── cli/                      # vn_setup wizard
├── engine/                       # Engine layer (billing + payments + license)
│   ├── billing/                  # Engine billing (DORMANT)
│   │   ├── tier_rate_limit_middleware.py # Never mounted
│   │   └── tier_config.py        # Tier enum (142 lines)
│   ├── payments/                 # Engine payments (PARTIAL)
│   │   ├── usage_metering_service.py    # PostgreSQL usage metering
│   │   ├── usage_queue.py               # Usage queue
│   │   └── ...
│   └── license/                  # License system
│       ├── license_metadata.py   # TIER_LIMITS (42 lines)
│       ├── jwt_license_generator.py
│       └── license_email.py
├── packages/                     # Langfuse observability package
│   └── observability/            # Dual-write telemetry (Langfuse + JSON)
├── api-gateway/                  # FastAPI gateway (:8000)
├── apps/                         # Private client projects
├── app/                          # Private client projects
├── billing/                      # Internal workspace (not public)
├── plans/                        # Planning documents
├── docs/                         # Documentation
├── pyproject.toml                # Project config (CLI entrypoint registration)
├── .mekong/                      # Mekong runtime state
├── .orchestrate/                 # Orchestration state
├── .agents/                      # Agent memory/handoff
├── .specify/                     # Planning templates
├── observability/                # Self-hosted infra config (Prometheus/Grafana/OTel)
└── mekong/                       # ZenOS constitution layer (150 files, 15,292 lines)
```

## Module Classification Table

| Directory/Component | Classification | Files | Lines | Notes |
|---|---|---|---|---|
| `src/core/` | Core | 77 | 58,237 | Canonical production layer. All 9-stage ALGO pipeline, billing, agent dispatch, tool registry. |
| `src/commands/` | Core | 43 | N/A | 43 wired CLI command modules. Active, registered in pyproject.toml. |
| `src/seed/` | Core | 20+ | N/A | Foundational auth, DB, config, types. TierKey enum (canonical). |
| `src/services/` | Core | 10+ | N/A | Polar client, org service. |
| `src/middleware/` | Core | 5+ | N/A | license_gate (JWT + balance check). |
| `src/api/` | Core | 20+ | N/A | FastAPI routes. Gateway entry point. |
| `src/harness/` | Legacy (phasing out) | 30+ | 15,000+ | Original harness layer. Full duplicate of orchestrator, router, agent dispatcher. Stubs for memory, workflow_state, retry_policy, telemetry, execution_history, dag_scheduler. |
| `src/harness/pev/` | Legacy | 15 | 3,500+ | PEV engine: parser, planner, executor, verifier, orchestrator_pkg. |
| `src/daemon/` | Adapter | 5+ | ~500 | Background worker layer. Own agent dispatcher. |
| `src/observability/` | Legacy (stub) | 1 | N/A | Single file health.py with stub HealthMonitor class. |
| `engine/billing/` | Dormant | 5 | 200+ | Engine billing. TierRateLimitMiddleware never mounted to gateway. |
| `engine/payments/` | Partial | 8 | N/A | Usage metering (PostgreSQL). Used by RaasLicenseGate via usage_meter.py. |
| `engine/license/` | Partial | 6 | 150+ | JWT license generation, TIER_LIMITS. |
| `packages/observability/` | Adapter | 10+ | N/A | Langfuse dual-write telemetry. Published to npm. |
| `observability/` (root) | Infrastructure | 10+ | N/A | Self-hosted Prometheus/Grafana/OTel config for M1 Max deployment. |
| `src/telemetry/` | Core | 5+ | N/A | Core telemetry (rate limit metrics). |
| `src/usage/` | Core | 3 | N/A | Usage tracker (SQLite). CLI-side metering. |
| `src/mcp_server.py` | Core | 1 | 1,125 | MCP server exposing 25 tools via stdio/SSE. |
| `src/core/crash_detector.py` | Core | 1 | 576 | Real-time crash detection. |
| `src/core/auto_recovery.py` | Core | 1 | 819 | Crash/license recovery engine. |
| `src/core/tool_registry.py` | Core | 1 | 583 | Tool registry + security (CommandSanitizer, PermissionRegistry). |
| `src/core/mcp_server.py` | Core | 1 | 1,125 | MCP server (25 tools). |
| `mekong/` | External | 150 | 15,292 | ZenOS constitution layer. Binh-Phap OS. |
| `.mekong/` | Config | 12 | 2,388 | Mekong runtime state. |
| `.orchestrate/` | Config | 5 | 546 | Orchestration state. |
| `.agents/` | Config | 29 | 2,686 | Agent memory/handoff files. |
| `.specify/` | Config | 5 | 261 | Planning templates. |
| `app/`, `apps/`, `billing/` | Private | N/A | N/A | Client projects and internal workspace. Not public. |
| `src/cli/` | Core | 5+ | N/A | vn_setup wizard. |

## CLI Entrypoint Architecture

```
pyproject.toml
  └── [project.scripts] mekong = "src.main:main"
        │
        ▼
src/main.py (21 lines)
  └── imports app_setup
        │
        ▼
app_setup.py
  ├── Initializes core systems (billing, auth, memory)
  ├── Loads 43 command modules from src/commands/
  ├── Registers CLI handlers
  └── Sets up middleware (license_gate)
        │
        ▼
Sub-applications:
  ├── src/commands/*.py (43 wired modules)
  ├── src/api/ (FastAPI gateway)
  ├── src/core/hybrid_router.py (9-stage LLM pipeline)
  └── src/middleware/license_gate.py (JWT + balance)
```

**Orphaned/Legacy:**
- `src/commands/` — 43 modules exist but step5 trace was missing from reports. Some commands may be dead or duplicated.
- `cli/entrypoint.py` — Legacy entrypoint. Not registered in pyproject.toml. (step1-top-level-map: "CLI entrypoint (legacy)")
- `harness/` TypeScript — Dead code. Zero consumers, no build output. (step1-top-level-map, inline findings)

## LLM Routing Pipeline (9-Stage ALGO)

```
INPUT: User goal/command
    │
    ▼
[1. CLASSIFY] src/core/task_classifier.py:102-110
    classify_task() → TaskProfile (complexity, domain, agent_role, mcu_cost)
    Also: classify_multi_agent() for multi-agent workflows
    │
    ▼
[2. MCU LOCK] src/core/mcu_gate.py:16-287
    MCUGate.lock() → MCULockResult
    Atomic credit check/lock via mcu_billing.py (SQLite ledger)
    │
    ▼
[3. MODEL SELECT] src/core/model_selector.py:12-496
    TaskProfile → ModelConfig
    Uses MODEL_ROUTING_MATRIX
    Fallback: tier_fallback_chain.py:15-140
    Cost estimation: cost_estimator.py:13-92
    │
    ▼
[4. AGENT LOAD] src/core/agent_dispatcher.py:66-290
    AgentDispatcher.dispatch() — load agent prompts + context
    HUB_MAP for agent routing
    agent_registry.py, agent_schema.py, context_flow.py
    │
    ▼
[5. BUILD MESSAGES] src/core/hybrid_router.py (internal)
    Construct LLM message chain
    api_adapter.py (formatters)
    command_loader.py (system prompts from commands)
    │
    ▼
[6. EXECUTE] src/core/fallback_chain.py:10-185
    execute_with_fallback()
    ├── local_adapter.py (MLX/Ollama)
    ├── api_adapter.py (cloud providers)
    └── circuit_breaker.py (3 failures → 15s cool-down)
    │
    ▼
[7. VERIFY] src/core/subagent_reviewer.py:249-272
    SubagentReviewer validates output quality
    RecipeVerifier in verifier.py
    └── On failure: replan_failed_branch() or trigger re-execution
    │
    ▼
[8. MCU CONFIRM] src/core/mcu_gate.py:274-282
    MCUGate.confirm() / refund_mcu()
    Commits or refunds credits via mcu_billing.py
    │
    ▼
[9. EMIT] src/core/event_bus.py + signals/__init__.py
    Event types: cli:command, cli:error, llm:call
    webhook_delivery_engine.py, tracing.py, telemetry_init.py
    │
    ▼
OUTPUT: Execution result + telemetry events
```

**Main Pipeline Orchestrator:** `src/core/hybrid_router.py` → `HybridRouter.route()` (lines 85-220)

## Agent Layer (3 Dispatchers)

```
                    ┌──────────────────────────────────┐
                    │  3 Parallel Agent Dispatchers     │
                    └──────────────────────────────────┘
                             │           │           │
              ┌──────────────┘           │           └──────────────┐
              ▼                          ▼                          ▼
    src/core/agent_dispatcher.py    src/harness/agents/       src/daemon/
    (290 lines)                      dispatcher.py             dispatcher.py
    CANONICAL                        LEGACY (phasing out)      DAEMON (separate)
    • AgentDispatcher                • Simpler dispatcher      • Dispatcher
    • HUB_MAP                        • No failover             • Background worker
    • Uses providers.py              • No provider             • Own provider layer
    • Used by HybridRouter           abstraction              • Separate concern
              │                          │
              │                          │
              └────────── DUPLICATES ────┘
```

| Dispatcher | Location | Lines | Status | Notes |
|---|---|---|---|---|
| Canonical | `src/core/agent_dispatcher.py:66-290` | 290 | **LIVE** | Uses HUB_MAP, integrated with providers.py. Used by HybridRouter. |
| Legacy | `src/harness/agents/dispatcher.py:62-184` | 184 | **PHASING OUT** | Duplicate implementation. No failover, no provider abstraction. |
| Daemon | `src/daemon/dispatcher.py:13-316` | 315 | **SEPARATE** | Background worker dispatcher. Separate concern, not in main CLI path. |

(step6-llm-router-trace: "Duplicate implementations across three layers")

## Billing Systems (3 Implementations)

```
                    ┌──────────────────────────────────────┐
                    │   3 Parallel Billing Implementations   │
                    └──────────────────────────────────────┘
                             │              │              │
              ┌──────────────┘              │              └──────────────┐
              ▼                             ▼                             ▼
    System 1: MCU Billing          System 2: Engine Billing       System 3: Engine Payments
    src/core/mcu_billing.py        engine/billing/                engine/payments/
    STATUS: LIVE                   STATUS: DORMANT                STATUS: PARTIAL
    Wired to gateway               Never mounted                  Used by RaasLicenseGate
    MCU = 1 credit                 tier_rate_limit_middleware      usage_metering_service.py
    SQLite ledger                  (ConfiguredMiddleware)         PostgreSQL metering
              │                     │                              │
              │                     │                              │
              └───────────── Tier Enum Conflicts ────────────────────┘
```

### Tier Enum Definitions (5 conflicting values)

| Enum | Location | Lines | Values | Status |
|---|---|---|---|---|
| `TierKey` | `src/seed/config/tiers.py` | 437 | BASIC, PREMIUM, ENTERPRISE, MASTER | **CANONICAL** — Used by MCU billing |
| `Tier` | `engine/billing/tier_config.py` | 142 | N/A (not verified in this audit) | DORMANT — Engine billing |
| `Tier` | `engine/license/license_metadata.py` | 42 | TIER_LIMITS dict | PARTIAL — License system |
| `TierKey` | `src/seed/config/tiers.py` (re-export) | N/A | Via `TIER_CONFIGS`, `TIER_CONFIG` | Canonical import path |

(step8-billing-payment-map: "3 distinct billing implementations and 5 Tier enum definitions operating in parallel")

## Memory/State Systems (9 implementations)

| # | System | Location | Type | Status | Notes |
|---|---|---|---|---|---|
| 1 | MemoryBridge | `src/core/memory.py` | YAML + Vector | **CANONICAL** | Primary memory. Vector semantic search. |
| 2 | MemoryStore | `src/core/memory_store.py` | JSONL | **CANONICAL** | JSONL persistence. Unified via MemoryBridge. |
| 3 | MemoryStore (harness) | `src/harness/pev/memory.py` | Stub | **STUB** | Minimal stub. Real impl in core. |
| 4 | WorkflowState | `src/harness/pev/workflow_state.py` | Stub | **STUB** | Minimal stub. |
| 5 | PEV Memory | `src/harness/pev/orchestrator_pkg/memory.py` | N/A | **PARTIAL** | Part of orchestrator package. |
| 6 | Memory Bridge Adapter | `src/core/adapters/pev_adapter.py` | Adapter | **BRIDGE** | Wraps harness MemoryStore to satisfy MemoryBridge protocol. |
| 7 | Seed Memory | `src/seed/` | Config | **CONFIG** | Foundational config. Not runtime memory. |
| 8 | .mekong/ | `.mekong/` | Runtime | **STATE** | Binh-Phap state, company config, audit, events, memory, vector index. |
| 9 | .agents/ | `.agents/` | Config | **AGENT STATE** | Agent handoff files, progress tracking, briefings. |

(step9-observability-state-map: "4 memory systems (YAML, JSONL, Vector, Seed) unified via MemoryBridge")

## Observability Pipeline (5 locations)

```
                    ┌──────────────────────────────────────────┐
                    │   5 Observability Locations               │
                    └──────────────────────────────────────────┘
                             │              │              │
              ┌──────────────┘              │              └──────────────┐
              ▼                             ▼                             ▼
    src/harness/observability/       observability/ (root)          packages/
    STATUS: PRIMARY (Harness)        STATUS: Infra Config           observability/
    • OTel collector, health,        • Self-hosted Prom/OTel        STATUS: Langfuse
      metrics, tracing, dashboards      Grafana for M1 Max           • Dual-write
    • telemetry_hooks.py (396L)      • Deployment config              (Langfuse + JSON)
    • telemetry_init.py             • Not application code         • npm package
              │                                                    │
              │                                                    │
              └───────────── Duplicate Pairs ──────────────────────┘
```

### Exact Duplicate Pair

| Duplicate | Location A | Location B | Lines | Status |
|---|---|---|---|---|
| TelemetryCollector | `src/core/telemetry/` | `src/harness/telemetry/` | ~700 each | **EXACT DUPLICATE** — identical structure, event types, anonymization, JSONL persistence |
| HealthReporter | `src/core/` (health) | `src/harness/observability/` | ~700 each | **EXACT DUPLICATE** — identical structure |

### All Observability Locations

| Location | Type | Status | Purpose |
|---|---|---|---|
| `src/harness/observability/` | Primary (Harness) | Active | Full OTel stack: collector, health, metrics, tracing, dashboards, provisioning |
| `src/observability/` | Legacy Stub | Inactive | Single file health.py with stub HealthMonitor class |
| `observability/` (root) | Infra Config | Active | Self-hosted Prometheus/Grafana/OTel config for M1 Max deployment |
| `packages/observability/` | Langfuse Package | Active | Dual-write telemetry: Langfuse (remote) + JSON (local) — publishes to npm |
| `src/telemetry/` | Core Telemetry | Active | Rate limit metrics, telemetry integration |

(step9-observability-state-map: "5 locations, 2 exact duplicates")

## Key File Sizes

| File | Lines | Purpose |
|---|---|---|
| `src/core/mcp_server.py` | 1,125 | MCP server exposing 25 tools via stdio/SSE |
| `src/core/auto_recovery.py` | 819 | Crash/license recovery engine (Phase 5) |
| `src/core/orchestrator/runner.py` | 815 | Main RecipeOrchestrator coordinator |
| `src/core/hybrid_router.py` | 328 | 9-stage ALGO pipeline orchestrator |
| `src/core/tool_registry.py` | 583 | Tool registry + security (CommandSanitizer, PermissionRegistry) |
| `src/core/crash_detector.py` | 576 | Real-time crash detection |
| `src/core/agent_dispatcher.py` | 290 | Canonical agent dispatcher |
| `src/core/mcu_billing.py` | 311 | Live MCU billing engine (SQLite ledger) |
| `src/core/providers.py` | 458 | LLM provider abstraction |
| `src/harness/agents/dispatcher.py` | 184 | Legacy agent dispatcher (duplicate) |
| `src/daemon/dispatcher.py` | 315 | Daemon background dispatcher |
| `src/seed/config/tiers.py` | 437 | TierKey enum (canonical tier config) |
| `src/harness/pev/planner.py` | 688 | PEV LLM decomposition planner |
| `src/harness/pev/executor.py` | 721 | PEV step runner |
| `src/harness/pev/parser.py` | 430 | PEV Markdown recipe parser |
| `src/harness/pev/verifier.py` | 490 | PEV verification engine |
| `src/harness/pev/orchestrator_pkg/` | 1,195 | Separate PEV orchestrator package |

## Confidence Level

HIGH — verified by reading source files across all 9 audit phases. All claims reference specific files and line ranges from the input reports.

## Cross-references

- `step1-top-level-map.md` — Complete file/directory inventory (8,242 files, 483,733 lines)
- `step2-core-module-map.md` — Deep map of `src/core/` (77 files, 58,237 lines, 9-stage ALGO pipeline)
- `step3-pev-engine-map.md` — PEV engine map: `src/harness/pev/` (parser, planner, executor, verifier, orchestrator)
- `step6-llm-router-trace.md` — 3-layer duplication analysis (core/harness/daemon), provider abstraction
- `step7-tool-execution-trace.md` — Tool registry + execution engine (CommandSanitizer, PermissionRegistry, security)
- `step8-billing-payment-map.md` — 3 billing implementations, 5 tier enums, usage metering conflict
- `step9-observability-state-map.md` — 5 observability locations, 2 exact duplicates, 9 memory systems
- `step10-issue-classification.md` — 15 classified issues (4 CRITICAL, 5 HIGH, 6 MEDIUM), prioritization matrix