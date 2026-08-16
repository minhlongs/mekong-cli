# Step 10: Architecture Audit Issue Classification

**Generated:** 2026-08-17
**Scope:** All Phase A+B reports (7 reports, steps 1-3 and 6-9)
**Method:** Cross-referencing report findings with codebase verification

---

## 1. Summary Table

| ID | Category | Severity | Title |
|----|----------|----------|-------|
| ISS-001 | Duplication | CRITICAL | Three parallel Agent Dispatchers (core/harness/daemon) |
| ISS-002 | Duplication | CRITICAL | Three parallel Orchestrator hierarchies |
| ISS-003 | Duplication | HIGH | Identical TelemetryCollector in core and harness |
| ISS-004 | Duplication | HIGH | Identical HealthReporter in core and harness |
| ISS-005 | Duplication | HIGH | Duplicate telemetry subdirectories (core/ vs harness/) |
| ISS-006 | Duplication | HIGH | Near-identical Hybrid Router (core vs harness) |
| ISS-007 | Duplication | HIGH | Two usage metering systems (SQLite vs PostgreSQL) |
| ISS-008 | Duplication | MEDIUM | Three billing systems with different scopes |
| ISS-009 | Conflict | CRITICAL | 5+ Tier enum definitions across codebase |
| ISS-010 | Conflict | CRITICAL | Three error hierarchies with overlapping names |
| ISS-011 | Conflict | HIGH | Three agent registry sources (YAML, core, harness) |
| ISS-012 | Conflict | MEDIUM | Two CLI entrypoints (src/main.py vs cli/entrypoint.py) |
| ISS-013 | Conflict | MEDIUM | Daemon has independent LLM router/classifier |
| ISS-014 | Dead Code | HIGH | Harness PEV stubs delegating to core (6 files) |
| ISS-015 | Dead Code | MEDIUM | Empty placeholder directories (plugins/, sample/) |
| ISS-016 | Dead Code | LOW | Root-level one-time fix scripts (fix_*.py, apply_*.py) |
| ISS-017 | Missing Interface | HIGH | MCP server uses custom protocol, not standard MCP JSON-RPC |
| ISS-018 | Missing Interface | HIGH | No MekongRuntimeAdapter / MekongCoreContract interface |
| ISS-019 | Missing Interface | MEDIUM | No payment protocol abstraction (x402/MPP) |
| ISS-020 | Unsafe Path | HIGH | agi_loop.py runs infinite self-improvement with no approval gate |
| ISS-021 | Unsafe Path | MEDIUM | swarm.py exposes node management without auth verification |
| ISS-022 | Missing Gate | HIGH | engine/billing middleware defined but never mounted to gateway |
| ISS-023 | Missing Gate | MEDIUM | No canonical owner for 9+ memory system instances |
| ISS-024 | Missing Gate | MEDIUM | Observability split across 5 locations with no coordination |
| ISS-025 | Duplication | MEDIUM | Daemon has complete independent infrastructure (LLM router, circuit breaker, classifier) |
| ISS-026 | Duplication | LOW | Multiple TelemetryCollector + stub variant in harness/pev/telemetry.py |
| ISS-027 | Missing Gate | LOW | Polymarket Tier enum exists separately from canonical TierKey |

---

## 2. Duplication Issues

### ISS-001: Three Parallel Agent Dispatchers [CRITICAL]

**Locations:**
- `src/core/agent_dispatcher.py:66-290` (290 lines) — canonical, production
- `src/harness/agents/dispatcher.py:62-184` (184 lines) — harness layer
- `src/daemon/dispatcher.py:13-316` (315 lines) — daemon background worker

**Evidence:** All three implement task dispatch to agents. Core imports from harness; daemon is fully independent with its own WorkerPool, TaskRouter, and DLQ. The harness dispatcher is a subset of core's functionality.

**Impact:** Bug fixes must be applied in 3 places. Behavior diverges silently. Core/harness circular dependency.

**Recommendation:** Keep `src/core/agent_dispatcher.py` as canonical. Deprecate harness dispatcher (make it a thin re-export). Integrate daemon dispatcher via composition over core dispatcher.

---

### ISS-002: Three Parallel Orchestrator Hierarchies [CRITICAL]

**Locations:**
- `src/core/orchestrator/` (~30K lines, full-featured with AGI/BMAD) — `runner.py` (815L)
- `src/harness/pev/orchestrator_pkg/` (1,195 lines total) — `runner.py` (534L), `agi.py` (226L), `step_executor.py` (129L), `rollback.py` (153L), `display.py` (95L), `models.py` (58L)
- `src/harness/pev/orchestrator.py` (258 lines) — sequential glue variant

**Evidence:** Core imports from harness; harness imports from core — circular-ish dependency. The harness orchestrator_pkg reimplements step execution, rollback, and AGI modes that already exist in core's orchestrator.

**Impact:** Circular import risk. Two execution paths for the same Plan-Execute-Verify pipeline. Rollback behavior can differ.

**Recommendation:** Merge into single orchestrator in `src/core/orchestrator/`. Deprecate `src/harness/pev/orchestrator_pkg/` and make `src/harness/pev/orchestrator.py` a thin delegation wrapper.

---

### ISS-003: Identical TelemetryCollector in Core and Harness [HIGH]

**Locations:**
- `src/core/telemetry_collector.py:41` — `class TelemetryCollector`
- `src/harness/observability/collector.py:41` — `class TelemetryCollector`

**Evidence:** Diff shows only import path differences (`from .telemetry_consent` vs `from src.core.telemetry_consent`). Logic is identical.

**Impact:** Same collector maintained in two places. Changes to one must be mirrored to other. Two active instances in runtime.

**Recommendation:** Keep `src/core/telemetry_collector.py`. Make `src/harness/observability/collector.py` a re-export or remove it.

---

### ISS-004: Identical HealthReporter in Core and Harness [HIGH]

**Locations:**
- `src/core/health_reporter.py:68` — `class HealthReporter`
- `src/harness/observability/health.py:68` — `class HealthReporter`

**Evidence:** Diff shows only import path difference. Logic identical.

**Impact:** Same as ISS-003 — dual maintenance, potential divergence.

**Recommendation:** Keep `src/core/health_reporter.py`. Deprecate `src/harness/observability/health.py`.

---

### ISS-005: Duplicate Telemetry Subdirectories [HIGH]

**Locations:**
- `src/core/telemetry/` (gpu_probe.py, instrument.py, meters.py, sdk_setup.py)
- `src/harness/observability/telemetry/` (gpu_probe.py, instrument.py, meters.py, sdk_setup.py)

**Evidence:** Both directories contain the same 4 files. The harness copy exists as part of the observability package.

**Impact:** 4 files duplicated. Two copies of GPU probing, instrumentation, and metering code.

**Recommendation:** Keep `src/core/telemetry/`. Remove `src/harness/observability/telemetry/` and update imports.

---

### ISS-006: Near-Identical Hybrid Router [HIGH]

**Locations:**
- `src/core/hybrid_router.py:84-311` (canonical, production)
- `src/harness/core/router.py:84-328` (harness copy)

**Evidence:** Diff shows only 2 differences — both are about `build_message_chain()` return value unpacking (core returns 3 values, harness returns 2). Otherwise identical 240+ line implementations.

**Impact:** The 9-stage ALGO pipeline is duplicated. A behavioral fix in one won't reach the other.

**Recommendation:** Remove `src/harness/core/router.py`. Point all harness imports to `src/core/hybrid_router.py`.

---

### ISS-007: Two Usage Metering Systems [HIGH]

**Locations:**
- `src/usage/usage_tracker.py:141` — `class UsageTracker` (SQLite, CLI-oriented)
- `engine/payments/usage_metering_service.py:183` — `class UsageMeteringService` (PostgreSQL, RaasLicenseGate)

**Evidence:** Two completely different storage backends, different APIs. `UsageTracker` uses SQLite with `_UsageMeteringMixin`. `UsageMeteringService` uses PostgreSQL with `usage_queue.py`.

**Impact:** Billing counts can differ between CLI path and gateway path. Revenue leakage risk if one overcounts or undercounts.

**Recommendation:** Decide on single metering backend. Given production gateway uses RaasLicenseGate (engine path), likely keep engine/payments as canonical. Deprecate src/usage/ SQLite tracker or unify adapter.

---

### ISS-008: Three Billing Systems [MEDIUM]

**Locations:**
- `src/core/mcu_billing.py` — MCU Billing (LIVE, wired to gateway)
- `engine/billing/` — Tier-based rate limiting (DORMANT, never mounted)
- `engine/payments/` — Usage metering (PARTIAL, used by RaasLicenseGate)

**Evidence:** Only MCU billing is wired to the live gateway (`src/gateway.py`). Engine billing middleware exists but `tier_rate_limit_middleware.ConfiguredMiddleware` is never mounted.

**Impact:** Two of three billing systems are dead or dormant. Confusion about which system handles what.

**Recommendation:** Merge engine/billing tier logic into MCU billing or remove it. One billing system, one source of truth.

---

## 3. Conflict Issues

### ISS-009: 5+ Tier Enum Definitions [CRITICAL]

**Locations:**
- `src/seed/config/tiers.py:29` — `class TierKey(Enum)` — canonical (BASIC, PREMIUM, ENTERPRISE, MASTER)
- `engine/billing/tier_config.py:14` — `class Tier(Enum)` — engine billing
- `engine/license/license_metadata.py` — `Tier` enum (via TIER_LIMITS)
- `src/polymarket/sdk.py:30` — `class Tier(Enum)` — polymarket
- `src/db/tier_config_repository.py:14` — `class TierConfig` — DB model
- `src/lib/rate_limiter_factory.py:142` — `class TierRateLimiter` — rate limiting

**Evidence:** At least 5 separate enum/class definitions with the name "Tier" or "TierConfig". Values may diverge between definitions.

**Impact:** A user's tier can mean different things depending on which module interprets it. Rate limits, billing amounts, and feature gates can silently disagree.

**Recommendation:** Deprecate all but `src/seed/config/tiers.TierKey`. Force all modules to import from there. Add CI check for `class Tier` imports outside seed/.

---

### ISS-010: Three Error Hierarchies with Overlapping Names [CRITICAL]

**Locations:**
- `src/core/exceptions.py` — `MekongError` base, with `PlanningError`, `ExecutionError`, `VerificationError`, `RollbackError`
- `src/core/pev_errors.py` — `PEVError` base, with `PlanningError`, `ExecutionError`, `VerificationError`
- `src/core/error_responses.py` — `ErrorResponse` (API layer, different shape entirely)

**Evidence:** Both exceptions.py and pev_errors.py define `PlanningError`, `ExecutionError`, `VerificationError` with different base classes. Code importing "PlanningError" may get the wrong one.

**Impact:** Exception handling can catch the wrong type. Error responses lose information when crossing layers. API error shape doesn't match internal error shape.

**Recommendation:** Unify into single error hierarchy under `src/core/exceptions.py`. PEV errors should be subclasses of MekongError, not parallel hierarchy.

---

### ISS-011: Three Agent Registry Sources [HIGH]

**Locations:**
- `agents/registry.yaml` — YAML-based registry (root)
- `src/core/agent_registry.py:1-345` (345 lines) — Python registry
- `src/harness/agents/registry.py:1-103` (103 lines) — Harness registry

**Evidence:** Three separate systems define which agents exist and how to load them. The YAML file, the core Python module, and the harness module each maintain agent definitions independently.

**Impact:** Agent availability depends on which registry is consulted. Adding an agent in one place doesn't make it visible to others.

**Recommendation:** Keep `src/core/agent_registry.py` as canonical. Make it load from `agents/registry.yaml`. Deprecate `src/harness/agents/registry.py`.

---

### ISS-012: Two CLI Entrypoints [MEDIUM]

**Locations:**
- `src/main.py` — Primary Python entrypoint
- `cli/entrypoint.py` — Secondary entrypoint

**Evidence:** Both files exist as separate entry points. The `src/main.py` is the primary path; `cli/entrypoint.py` is likely legacy.

**Impact:** Users or scripts invoking the wrong entrypoint may get different behavior or missing commands.

**Recommendation:** Consolidate to single entrypoint. If `cli/entrypoint.py` is legacy, deprecate it.

---

### ISS-013: Daemon Has Independent LLM Router/Classifier [MEDIUM]

**Locations:**
- `src/daemon/llm_router.py` — Full LLM router with circuit breaker, model routing
- `src/daemon/classifier.py` — Task classifier
- `src/core/hybrid_router.py` — Canonical 9-stage pipeline
- `src/core/task_classifier.py` — Canonical classifier

**Evidence:** Daemon reimplements LLM routing and task classification completely independently from the core 9-stage pipeline. Uses its own `ModelConfig`, `CircuitBreaker`, and `TaskRouter`.

**Impact:** Model selection and circuit breaker state can differ between daemon and main pipeline. Bug fixes to core pipeline don't reach daemon.

**Recommendation:** Daemon should delegate to core's hybrid_router for classification and model selection. Keep daemon's circuit breaker as a thin wrapper.

---

## 4. Dead Code Issues

### ISS-014: Harness PEV Stubs Delegating to Core [HIGH]

**Locations:**
- `src/harness/pev/memory.py` — stub
- `src/harness/pev/workflow_state.py` — stub
- `src/harness/pev/retry_policy.py` — stub
- `src/harness/pev/telemetry.py` — contains duplicate TelemetryCollector (see ISS-026)
- `src/harness/pev/execution_history.py` — stub
- `src/harness/pev/dag_scheduler.py` — stub

**Evidence:** Step 3 report explicitly identifies these as "minimal stubs, real implementations live in core." They exist solely to maintain import compatibility.

**Impact:** 6 dead files add cognitive load. New developers must understand they're stubs, not implementations.

**Recommendation:** Deprecate stubs with warnings. Update all harness imports to point directly to core. Remove stubs in cleanup phase.

---

### ISS-015: Empty Placeholder Directories [MEDIUM]

**Locations:**
- `plugins/` — empty directory
- `sample/` — empty directory

**Evidence:** Step 1 report identifies `plugins/` and `sample/` as empty. Also noted: `cloudflare-skills/`, `agy-marketplace/`, `models/` were empty.

**Impact:** Misleading directory structure. Developers may assume functionality exists where it doesn't.

**Recommendation:** Remove empty directories. If they represent planned features, track them in roadmap instead.

---

### ISS-016: Root-Level One-Time Fix Scripts [LOW]

**Locations:**
- Root-level `fix_*.py`, `apply_*.py`, `verify_*.py` scripts (6 total identified in step 1)

**Evidence:** Step 1 report: "All 6 root-level fix_*.py / apply_*.py / verify_*.py scripts are one-time repair scripts that should be deleted or moved to .archive/."

**Impact:** Minor clutter. No runtime risk.

**Recommendation:** Move to `.archive/` or delete. These served their purpose.

---

## 5. Conflict Issues (Additional)

### ISS-025: Daemon Has Complete Independent Infrastructure [MEDIUM]

**Locations:**
- `src/daemon/dispatcher.py` (315L) — independent dispatcher
- `src/daemon/llm_router.py` — independent LLM routing
- `src/daemon/classifier.py` — independent classification
- `src/daemon/circuit_breaker.py` — independent circuit breaker
- `src/daemon/worker_pool.py` — independent worker pool
- `src/daemon/task_router.py` — independent task routing

**Evidence:** Daemon reimplements dispatcher, LLM routing, classification, circuit breaking, worker management, and task routing — all independently from core. Not 1-2 files, but 6+ files forming a complete parallel runtime.

**Impact:** Daemon is effectively a separate application within the monorepo. Changes to core infrastructure don't propagate to daemon. Two systems competing for same LLM endpoints with different circuit breaker states.

**Recommendation:** Either daemon should compose core modules (preferred) or be split into its own package with explicit boundary.

---

### ISS-026: Triple TelemetryCollector [LOW]

**Locations:**
- `src/core/telemetry_collector.py:41` — canonical
- `src/harness/observability/collector.py:41` — copy (see ISS-003)
- `src/harness/pev/telemetry.py:12` — third variant

**Evidence:** A third TelemetryCollector exists in `src/harness/pev/telemetry.py` as a stub/minimal variant. Three classes with same name across three packages.

**Impact:** Import confusion. Runtime behavior depends on which `TelemetryCollector` is imported.

**Recommendation:** Consolidate to single source. Remove duplicate locations.

---

## 6. Missing Interface Issues

### ISS-017: MCP Server Uses Custom Protocol [HIGH]

**Locations:**
- `src/core/mcp_server.py:162` — `class MekongMcpServer` (1,125 lines)

**Evidence:** The MCP server exposes 25 tools but uses a custom handler pattern (`_handle_memory_search`, `_handle_tasks_list`, etc.) rather than implementing standard MCP JSON-RPC `tools/list` and `tools/call` methods. No evidence of JSON-RPC transport layer.

**Impact:** MCP clients (Claude Desktop, other AI tools) cannot connect to Mekong as a standard MCP server. The "25 tools" are internal-only.

**Recommendation:** Implement standard MCP JSON-RPC protocol for `tools/list` and `tools/call`. Wrap existing handler methods as the backend. This is what makes Mekong interoperable.

---

### ISS-018: No MekongRuntimeAdapter / MekongCoreContract Interface [HIGH]

**Locations:** Cross-cutting — no file found

**Evidence:** Step reports note "No MekongRuntimeAdapter or MekongCoreContract interface" for Buzz integration. The codebase has adapters in `src/core/adapters/` (e.g., `pev_adapter.py`, `memory_store_adapter.py`) but no top-level contract defining what the runtime provides.

**Impact:** External consumers (Buzz, future integrations) cannot depend on a stable API contract. Internal modules couple directly to implementations.

**Recommendation:** Define `MekongCoreContract` Protocol in `src/core/contracts.py` specifying the runtime's public surface. Implement against it. Use it as the adapter boundary for Buzz and other consumers.

---

### ISS-019: No Payment Protocol Abstraction [MEDIUM]

**Locations:**
- `engine/billing/tier_config.py` — Stripe/Polar-specific
- `engine/payments/usage_metering_service.py` — PostgreSQL-specific
- `engine/license/` — JWT license-specific

**Evidence:** No generic payment protocol abstraction exists. Billing code is directly coupled to specific payment providers (Polar, Stripe) and storage backends. No x402 or MPP abstraction layer.

**Impact:** Switching payment providers requires rewriting billing logic. Cannot add new payment methods without touching core billing code.

**Recommendation:** Define `PaymentProtocol` Protocol in `src/land/billing/` or `src/core/contracts.py`. Implement Polar, Stripe, PayOS as adapters against it. Low priority unless payment provider switching is imminent.

---

## 7. Unsafe Path Issues

### ISS-020: agi_loop.py Infinite Self-Improvement Without Approval Gate [HIGH]

**Locations:**
- `src/core/agi_loop.py:1-30` — "Tom Hum Self-Improvement Engine"

**Evidence:** `agi_loop.py` runs in an infinite loop: ASSESS -> PLAN -> EXECUTE -> VERIFY -> MEMORIZE -> REPORT -> COOLDOWN -> repeat. Spawns CC CLI sessions to implement changes. No approval gate, no human-in-the-loop check, no maximum iteration limit visible in the header. While `autonomous.py:206` has `self.governance.request_approval(goal, decision)`, `agi_loop.py` does not.

**Impact:** Autonomous code modification without approval could introduce bugs or security issues. No circuit breaker on the improvement loop itself.

**Recommendation:** Add approval gate for EXECUTE phase. Add maximum iteration cap. Add circuit breaker on failure count. This is the highest-risk autonomous path in the codebase.

---

### ISS-021: swarm.py Exposes Node Management Without Auth [MEDIUM]

**Locations:**
- `src/core/swarm.py` — `SwarmRegistry` class

**Evidence:** `SwarmRegistry` provides `add_node()`, `remove_node()`, `list_nodes()` with no authentication or authorization checks. Nodes are persisted to file.

**Impact:** Any code with access to the swarm registry can add rogue nodes, redirect traffic, or remove healthy nodes.

**Recommendation:** Add node identity verification (mutual TLS or signed tokens). Add admin-only gate for add/remove operations.

---

## 8. Missing Gate Issues

### ISS-022: Engine Billing Middleware Never Mounted [HIGH]

**Locations:**
- `engine/billing/tier_rate_limit_middleware.py` — `ConfiguredMiddleware` defined
- `src/gateway.py` — does not import or mount it

**Evidence:** Step 8 report: "ConfiguredMiddleware never mounted." The middleware exists but is not wired into the FastAPI gateway. Engine billing tier enforcement is effectively dead.

**Impact:** Tier-based rate limiting for engine billing is never enforced. Users on any tier get unlimited engine requests (assuming they pass the license gate).

**Recommendation:** Either mount the middleware and activate tier rate limiting, or remove it entirely. Half-implemented security controls are worse than no control.

---

### ISS-023: No Canonical Owner for 9+ Memory System Instances [MEDIUM]

**Locations:**
- `src/core/memory.py` — `MemoryStore` (YAML+JSONL)
- `src/core/memory_store.py` — `MemoryEntry`, `MemoryStore` (JSONL)
- `src/core/memory_bridge.py` — `MemoryBridge` protocol
- `src/core/memory_client.py` — `NeuralMemoryClient`
- `src/core/memory_scope.py` — `ScopedMemoryStore`
- `src/core/vector_memory_store.py` — `VectorMemoryStore`
- `src/core/adapters/memory_store_adapter.py` — `MemoryStoreBridge`
- `src/core/gateway/models.py` — `MemoryEntryInfo`, `MemoryStatsResponse`
- `src/harness/pev/memory.py` — stub

**Evidence:** 9 files implementing or adapting memory. `MemoryBridge` protocol exists but isn't universally adopted. No single owner or entry point for "memory."

**Impact:** Memory state can be scattered across YAML, JSONL, vector store, and in-memory. A write to one store isn't visible to readers of another. The bridge adapter only covers PEV.

**Recommendation:** Designate `MemoryBridge` as the single interface. Implement MemoryStore, VectorMemoryStore, and ScopedMemoryStore as backends behind it. Route all access through bridge. Remove direct MemoryStore access.

---

### ISS-024: Observability Split Across 5 Locations [MEDIUM]

**Locations:**
- `src/harness/observability/` — Primary OTel stack (collector, health, metrics, tracing, dashboards, provisioning)
- `src/observability/` — Legacy stub (single file `health.py` with stub `HealthMonitor`)
- `observability/` (root) — Infra config (Prometheus/Grafana/OTel)
- `packages/observability/` — Langfuse package (npm, dual-write)
- `src/core/telemetry/` + `src/core/telemetry_*.py` — Core telemetry

**Evidence:** 5 separate observability locations with partial overlap. No single coordinate point for "where does telemetry go?" The root observability/ is infra config, not code. `src/observability/health.py` is a dead stub.

**Impact:** Telemetry data can be written to multiple backends without coordination. Dashboards may show incomplete data. Debugging requires knowing which observability path is active.

**Recommendation:** Designate `src/harness/observability/` as canonical runtime observability. Remove `src/observability/` stub. Consolidate `src/core/telemetry_*` into harness. Keep root `observability/` as infra config only.

---

### ISS-027: Polymarket Tier Enum Separate from Canonical [LOW]

**Locations:**
- `src/polymarket/sdk.py:30` — `class Tier(Enum)` with TierLimits

**Evidence:** Polymarket defines its own Tier enum separate from `src/seed/config/tiers.TierKey`. Values may diverge.

**Impact:** Low risk — Polymarket is a separate concern. But if tiers ever need to align, this will be a migration headache.

**Recommendation:** Either align Polymarket Tier with canonical TierKey or document that Polymarket tiers are intentionally separate domain-specific tiers.

---

## 9. Cross-Cutting Concerns Summary

### Root Cause Pattern: The Harness Layer

The majority of duplication and conflicts trace to one architectural decision: **`src/harness/` was created as a parallel implementation of `src/core/`** and was never fully consolidated. Evidence:

- Harness dispatcher (184L) vs Core dispatcher (290L) — ISS-001
- Harness orchestrator_pkg (1,195L) vs Core orchestrator (~30K) — ISS-002
- Harness collector (identical to core) — ISS-003
- Harness health (identical to core) — ISS-004
- Harness telemetry/ (identical to core) — ISS-005
- Harness router (near-identical to core) — ISS-006
- Harness PEV stubs (6 files) — ISS-014

**Resolution path:** Designate `src/core/` as the single source of truth. Convert all harness duplicates to thin re-exports or deprecation wrappers. Remove after one release cycle.

### Root Cause Pattern: No Canonical Type Registry

Tier enums (5+) and error hierarchies (3) exist because there's no single import point that other modules are required to use. The `src/seed/config/tiers.py` TierKey is close to being canonical but isn't enforced.

### Root Cause Pattern: Daemon as Separate Application

The daemon (`src/daemon/`) reimplements dispatcher, LLM routing, classification, circuit breaking, worker pool, and task routing. It should compose core modules, not duplicate them.

---

## 10. Priority-Ordered Fix List (Top 20)

| Priority | ID | Category | Action | Effort | Risk if Deferred |
|----------|----|----------|--------|--------|-------------------|
| 1 | ISS-009 | Conflict | Unify Tier enums to single TierKey | Medium | Billing drift, wrong rate limits |
| 2 | ISS-010 | Conflict | Merge 3 error hierarchies | Medium | Wrong exception caught, silent failures |
| 3 | ISS-001 | Duplication | Consolidate 3 dispatchers | High | Bug fix divergence, circular imports |
| 4 | ISS-002 | Duplication | Merge 3 orchestrator hierarchies | High | Circular imports, dual execution paths |
| 5 | ISS-020 | Unsafe | Add approval gate to agi_loop | Low | Autonomous code changes without oversight |
| 6 | ISS-017 | Missing | Implement standard MCP JSON-RPC | Medium | MCP interop broken |
| 7 | ISS-022 | Missing Gate | Mount or remove engine billing middleware | Low | Silent tier enforcement gap |
| 8 | ISS-003 | Duplication | Remove duplicate TelemetryCollector | Low | Dual telemetry emission |
| 9 | ISS-004 | Duplication | Remove duplicate HealthReporter | Low | Dual health reporting |
| 10 | ISS-005 | Duplication | Remove duplicate telemetry/ subdirectory | Low | Maintenance confusion |
| 11 | ISS-006 | Duplication | Remove duplicate Hybrid Router | Medium | 9-stage pipeline divergence |
| 12 | ISS-007 | Duplication | Unify usage metering (SQLite vs PG) | High | Billing count mismatch, revenue risk |
| 13 | ISS-011 | Conflict | Consolidate agent registries | Medium | Agent availability inconsistency |
| 14 | ISS-023 | Missing Gate | Designate canonical memory owner | Medium | Memory state scattered |
| 15 | ISS-024 | Missing Gate | Consolidate observability locations | Medium | Incomplete telemetry |
| 16 | ISS-025 | Conflict | Daemon should compose core modules | High | Parallel infrastructure drift |
| 17 | ISS-018 | Missing | Define MekongCoreContract interface | Medium | No stable API for integrations |
| 18 | ISS-013 | Conflict | Daemon should use core's LLM router | Medium | Model selection divergence |
| 19 | ISS-014 | Dead Code | Remove 6 harness PEV stubs | Low | Cognitive load |
| 20 | ISS-008 | Duplication | Consolidate 3 billing systems | High | Dead code confusion |

---

## 11. Limitations

**What this classification did NOT cover:**

- **Step 4 (TypeScript harness)** and **Step 5 (CLI entrypoint trace)** reports were missing from the reports directory. These may contain additional issues around TypeScript/Python boundary, CLI command duplication, and harness TypeScript integration.
- **Detailed line-by-line code review** — this classification is based on report summaries plus targeted verification. Some issues may need deeper inspection during remediation.
- **Runtime behavior analysis** — no dynamic tracing was done. Some "dead code" may actually be invoked through dynamic imports or entrypoints not visible in static analysis.
- **Test coverage assessment** — whether the duplicate systems have adequate test coverage was not evaluated.
- **Performance impact** — dual telemetry collectors or multiple billing paths may have measurable runtime cost, but this was not measured.

---

*Generated by architecture audit — all findings verified against codebase where possible.*
