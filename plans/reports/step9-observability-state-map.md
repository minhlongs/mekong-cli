# Observability, Telemetry & State/Memory System Map
## Mekong CLI v6.0 — Architecture Audit

---

## 1. OBSERVABILITY SYSTEM MAP

### 1.1 All Observability Locations

| Location | Type | Status | Purpose |
|----------|------|--------|---------|
| `src/harness/observability/` | **Primary (Harness)** | Active | Full OTel stack: collector, health, metrics, tracing, dashboards, provisioning |
| `src/observability/` | **Legacy Stub** | Inactive | Single file `health.py` with stub HealthMonitor class |
| `observability/` (root) | **Infra Config** | Active | Self-hosted Prometheus/Grafana/OTel config for M1 Max deployment |
| `packages/observability/` | **Langfuse Package** | Active | Dual-write telemetry: Langfuse (remote) + JSON (local) — publishes to npm |
| `src/telemetry/` | **Core Telemetry** | Active | Rate limit metrics, telemetry integration |

### 1.2 src/harness/observability/ — Detailed Structure

```
src/harness/observability/
├── __init__.py              # Exports: TelemetryCollector, tracing, metrics, health
├── collector.py             # TelemetryEvent, TelemetryCollector (JSONL to .mekong/telemetry.jsonl)
├── health.py                # HealthMetrics, HealthReporter → RaaS Gateway
├── metrics.py               # In-memory agent metrics (think time, tool calls, memory hits)
├── tracing.py               # TraceContext, SpanContext, trace_middleware (contextvars)
├── otel-collector.yaml      # OTel Collector config
├── prometheus.yml           # Prometheus scrape config
├── docker-compose.yml       # Full stack: prometheus, grafana, otel-collector
├── dashboards/
│   ├── agent-performance.json
│   ├── cost-analysis.json
│   └── m1max-health.json
├── provisioning/
│   ├── dashboards/dashboard-provider.yaml
│   └── datasources/prometheus.yaml
├── raas_auth/__init__.py    # Stub RaaSAuthClient
└── telemetry/
    ├── __init__.py
    ├── instrument.py        # @observe_agent decorator
    ├── gpu_probe.py         # M1 Max GPU sampler (reads powermetrics JSON)
    ├── meters.py            # 5 MVP OTel instruments
    └── sdk_setup.py         # OTel bootstrap (OTLP gRPC exporter)
```

**Key Classes/Functions:**
- `TelemetryCollector` (collector.py:28) — anonymized events, JSONL persistence
- `HealthReporter` (health.py:30) — CLI health → RaaS Gateway
- `METERS` singleton (meters.py:100) — 5 instruments: invocation_ms, token_cost_usd, gpu_util, model_drift, retry_total
- `@observe_agent` (instrument.py:10) — auto-instrumentation decorator
- `GpuProbe` (gpu_probe.py:14) — M1 Max GPU util via powermetrics
- `TraceContext`, `SpanContext` (tracing.py:20, 55) — per-command trace IDs

### 1.3 packages/observability/ — Langfuse Package (npm package)

```
packages/observability/
├── __init__.py              # Exports: ObservabilityFacade, LangfuseProvider, traced
├── observability_facade.py  # Dual-write: Langfuse + TelemetryCollector
├── langfuse_provider.py     # Langfuse SDK wrapper (graceful degradation)
├── trace_decorator.py       # @traced(name="step") contextvar decorator
├── package.json             # npm package config
├── pyproject.toml           # Python package config
└── src/                     # TypeScript sources (event-observer, logger)
```

**Key Classes:**
- `ObservabilityFacade` (observability_facade.py:12) — singleton dual-write coordinator
- `LangfuseProvider` (langfuse_provider.py:16) — wraps Langfuse SDK
- `@traced` (trace_decorator.py:25) — auto-span with contextvar propagation

### 1.4 observability/ (root) — Self-Hosted Infra

```
observability/
├── .env.observability.template
├── agent_metrics.py          # Duplicate of harness metrics.py
├── docker-compose.observability.yml
├── otel-collector-config.yaml
├── prometheus.yml
├── provisioning/
│   ├── dashboards/dashboard-provider.yaml
│   └── datasources/prometheus.yaml
└── README.md                 # Bring-up instructions for M1 Max
```

**Note:** `agent_metrics.py` is **exact duplicate** of `src/harness/observability/metrics.py`

### 1.5 src/telemetry/ — Rate Limit Telemetry

```
src/telemetry/
├── __init__.py
└── rate_limit_metrics.py     # RateLimitEvent, RateLimitMetricsEmitter, TelemetryIntegration
```

- Emits rate limit events to DB (rate_limit_events table) for dashboard integration

### 1.6 src/core/ — Core Telemetry Modules

| File | Lines | Purpose |
|------|-------|---------|
| `telemetry_collector.py` | 308 | Same as harness collector — usage events (command_executed, session_started, etc.) |
| `telemetry_uploader.py` | 87 | Batch upload to analytics backend |
| `telemetry_consent.py` | 134 | GDPR/opt-in consent management |
| `telemetry_reporter.py` | 293 | SQLite usage records + RaaS Gateway reporting |
| `telemetry_hooks.py` | 396 | Event emission to RaaS Gateway (cli:command, cli:error, llm:call) |
| `telemetry_init.py` | 22 | OTel initialization for FastAPI |
| `telemetry_models.py` | 138 | ExecutionTrace, StepTrace, SubsystemHealth dataclasses |
| `health_endpoint.py` | 285 | FastAPI /health endpoint server |
| `health_reporter.py` | 301 | Duplicate of harness HealthReporter |
| `pev_health_checks.py` | 116 | PEV component health registration |
| `pev_metrics_collector.py` | 260 | Pipeline metrics (execution time, success/fail, retries) |
| `crash_detector.py` | 576 | Real-time crash detection (exit codes, OOM, fatal exceptions) |
| `anomaly_detector.py` | 357 | Z-score anomaly detection on 7-day baselines |

---

## 2. MEMORY SYSTEM COMPARISON TABLE (6+ Implementations)

| # | System | Location | Lines | Backend | Persistence | Scope | Canonical? |
|---|--------|----------|-------|---------|-------------|-------|------------|
| 1 | **MemoryStore (YAML+Vector)** | `src/core/memory.py` | 316 | YAML + VectorMemoryStore | `.mekong/memory.yaml` + vector_index.json | Global (CLI-wide) | **YES — Primary** |
| 2 | **MemoryStore (JSONL)** | `src/core/memory_store.py` | 142 | JSONL append-only | `.mekong/memory.jsonl` | Global (CLI-wide) | **YES — Secondary** |
| 3 | **VectorMemoryStore** | `src/core/vector_memory_store.py` | 380 | In-memory + JSON file | JSON collections (episodic/semantic/procedural) | Global | **Component of #1** |
| 4 | **SeedMemory** | `src/seed/memory.py` | 109 | SQLite (+ Chroma stub) | `/tmp/seed_memory.db` | Per-agent | **Legacy/Seed** |
| 5 | **MemoryBridge + Adapters** | `src/core/memory_bridge.py` + `src/core/adapters/` | 134+177+156+123 | Protocol + 4 adapters | Delegates to wrapped store | Multi-scope | **Unification Layer** |
| 6 | **ScopedMemoryStore** | `src/core/memory_scope.py` | ~200 | In-memory dict | In-memory (with scope keys) | (app,org,user,agent,session) | **Experimental** |
| 7 | **PEV MemoryStore** | `src/harness/pev/memory.py` | 28 | In-memory dict | In-memory only | PEV orchestrator | **Harness stub** |
| 8 | **MekongCLI MemoryBackend** | `src/mekongcli/core/memory/backends.py` | 22 | Protocol only | None (interface) | Goal engine | **New abstraction** |
| 9 | **MemoryClient (Neural/Mem0)** | `src/core/memory_client.py` | 129 | HTTP (NeuralMemory) / Mem0 | Remote server | Configurable | **External provider** |

---

## 3. STATE OWNERSHIP ANALYSIS

### 3.1 Canonical Memory Systems

**Primary: `src/core/memory.py` — MemoryStore (YAML + Vector)**
- Used by: `src/core/agi_score.py`, `src/core/smart_router.py`, `src/core/autonomous.py`, `src/core/telegram_handlers.py`, `src/core/mcp_server.py`, `src/mekongcli/core/goal_engine/service.py`
- CLI commands: `src/commands/memory_commands.py`, `src/cli/commands/memory.py`
- Persists to: `.mekong/memory.yaml` (human-readable) + `.mekong/vector_index.json` (semantic search)
- Features: Vector semantic search, failure pattern analysis, fix suggestions, compression

**Secondary: `src/core/memory_store.py` — MemoryStore (JSONL)**
- Used by: `src/core/agent_dispatcher.py`, `src/cli/memory_commands.py` (partial)
- Persists to: `.mekong/memory.jsonl` (append-only, one JSON per line)
- Schema: `{timestamp, agent, action, outcome, tags}`

### 3.2 Unification Layer: MemoryBridge

`src/core/memory_bridge.py` defines `MemoryBridge` protocol with 4 adapters:
| Adapter | Wraps | Backend |
|---------|-------|---------|
| `MemoryStoreBridge` | `src/core/memory.py` | YAML + Vector |
| `SeedBridge` | `src/seed/memory.py` | SQLite |
| `PevBridge` | `src/harness/pev/memory.py` | In-memory dict |
| `ScopedBridge` | `src/core/memory_scope.py` | Scoped in-memory |

Factory: `get_memory_bridge(backend: str)` in `memory_bridge.py:112`

### 3.3 External Provider: MemoryClient

`src/core/memory_client.py` — Factory for external memory:
- `MEMORY_PROVIDER=mem0` → `packages.memory.memory_facade` (Mem0 + Qdrant)
- `MEMORY_PROVIDER=neural` → `NeuralMemoryClient` (HTTP to nmem server)
- `MEMORY_PROVIDER=yaml` → `None` (use MemoryStore directly)

### 3.4 Deprecated / Experimental

| System | Status | Reason |
|--------|--------|--------|
| `src/observability/health.py` | Dead stub | Single class, never used |
| `src/harness/pev/memory.py` | Harness stub | In-memory only, PEV internal |
| `src/core/memory_scope.py` | Experimental | Multi-scope isolation, not wired to persistence |
| `src/mekongcli/core/memory/` | New abstraction | Protocol only, no implementation yet |

---

## 4. TELEMETRY DUPLICATION ANALYSIS

### 4.1 Collector Duplication (CRITICAL)

| File | Location | Lines | Status |
|------|----------|-------|--------|
| `TelemetryCollector` | `src/harness/observability/collector.py` | 308 | **Active (Harness)** |
| `TelemetryCollector` | `src/core/telemetry_collector.py` | 308 | **Active (Core) — NEAR DUPLICATE** |

**Evidence:** Both files have identical structure, same event types (`command_executed`, `session_started`, `session_ended`, `error_occurred`), same anonymization (SHA256 hash), same JSONL persistence pattern.

### 4.2 Health Reporter Duplication (CRITICAL)

| File | Location | Lines | Status |
|------|----------|-------|--------|
| `HealthReporter` | `src/harness/observability/health.py` | 301 | **Active (Harness)** |
| `HealthReporter` | `src/core/health_reporter.py` | 301 | **Active (Core) — EXACT DUPLICATE** |

**Evidence:** Line-by-line identical including `HealthMetrics` dataclass, `record_command()`, `report_to_gateway()`, singleton `get_health_reporter()`.

### 4.3 Metrics Duplication (MODERATE)

| File | Location | Lines | Status |
|------|----------|-------|--------|
| `metrics.py` | `src/harness/observability/metrics.py` | 73 | **Active (Harness)** |
| `agent_metrics.py` | `observability/agent_metrics.py` (root) | 73 | **Dead duplicate** |

**Evidence:** Root `observability/agent_metrics.py` is exact copy of harness version.

### 4.4 Tracing Systems (Multiple)

| System | Location | Type |
|--------|----------|------|
| `TraceContext` + `SpanContext` | `src/harness/observability/tracing.py` | Contextvars-based |
| `TraceContext` + `SpanContext` | `src/core/tracing.py` | Contextvars-based (255 lines) |
| `ObservabilityFacade` + `@traced` | `packages/observability/` | Langfuse + contextvar |
| OTel SDK | `src/harness/observability/telemetry/sdk_setup.py` | OTel native |

**Note:** `src/core/tracing.py` and `src/harness/observability/tracing.py` are **different implementations** (core is more complete with structlog integration).

---

## 5. FILE:LINE REFERENCES

### Crash & Anomaly Detection
- `src/core/crash_detector.py:32` — `CRASH_PATTERNS` regex for fatal exceptions
- `src/core/crash_detector.py:91` — `detect_crash_signals()` OOM/signal detection
- `src/core/crash_detector.py:276` — `CrashDetector.analyze_step()` stderr analysis
- `src/core/crash_detector.py:372` — Auto-recovery trigger
- `src/core/anomaly_detector.py:17` — `AnomalyCategory` enum (spike, drop, pattern_break)
- `src/core/anomaly_detector.py:177` — Z-score baseline calculation (7-day rolling)

### Tracing
- `src/harness/observability/tracing.py:20` — `TraceContext` dataclass
- `src/harness/observability/tracing.py:55` — `SpanContext` dataclass
- `src/harness/observability/tracing.py:280` — `@trace_middleware` decorator
- `src/core/tracing.py:20` — Core `TraceContext` (structlog integration)
- `packages/observability/trace_decorator.py:25` — `@traced` decorator

### Metrics (OTel)
- `src/harness/observability/telemetry/meters.py:20` — `METERS` singleton (5 instruments)
- `src/harness/observability/telemetry/meters.py:35` — `invocation_ms` Histogram
- `src/harness/observability/telemetry/meters.py:50` — `token_cost_usd` Counter
- `src/harness/observability/telemetry/meters.py:65` — `gpu_util` Gauge
- `src/harness/observability/telemetry/meters.py:80` — `model_drift` Gauge
- `src/harness/observability/telemetry/meters.py:90` — `retry_total` Counter

### GPU Probe
- `src/harness/observability/telemetry/gpu_probe.py:14` — `GpuProbe` class
- `src/harness/observability/telemetry/gpu_probe.py:61` — Reads `/tmp/mekong_gpu_metrics.json`

### Memory Persistence Files
- `.mekong/memory.yaml` — YAML entries (MemoryStore from memory.py)
- `.mekong/memory.jsonl` — JSONL entries (MemoryStore from memory_store.py)
- `.mekong/vector_index.json` — VectorMemoryStore collections
- `.mekong/events.jsonl` — Telemetry events (TelemetryCollector)

---

## 6. RISKS & RECOMMENDATIONS

### Critical (Must Fix)
1. **Duplicate TelemetryCollector** — Two identical collectors writing to potentially different paths. Consolidate to single source in `src/harness/observability/collector.py` and re-export from core.

2. **Duplicate HealthReporter** — Exact duplicate. Remove `src/core/health_reporter.py`, import from harness.

3. **Dead observability/health.py** — Remove `src/observability/` directory entirely (stub only).

### High Priority
4. **Multiple Tracing Systems** — Three independent tracing implementations. Standardize on OTel (harness) + Langfuse facade (packages) for dual-write.

5. **Memory Fragmentation** — 6+ memory systems with partial overlap. Adopt MemoryBridge as canonical interface, deprecate direct MemoryStore imports.

6. **Root observability/agent_metrics.py** — Remove duplicate, use harness version.

### Medium Priority
7. **PEV MemoryStore** — In-memory stub, not persistent. Either persist or remove.

8. **ScopedMemoryStore** — Experimental, not integrated. Complete or remove.

9. **MemoryClient provider detection** — Uses `packages.memory` import which may not exist. Add graceful fallback.

---

## 7. SUMMARY

| Category | Active Systems | Duplicates | Dead/Stub |
|----------|----------------|------------|-----------|
| **Collectors** | 2 (harness + core) | 1 pair identical | 0 |
| **Health Reporters** | 2 (harness + core) | 1 pair identical | 1 (src/observability/) |
| **Metrics** | 1 (harness) | 1 (root observability/) | 0 |
| **Tracing** | 3 (harness, core, packages) | Partial overlap | 0 |
| **Memory** | 4 (YAML, JSONL, Vector, Seed) | Bridge unifies | 2 (PEV, Scoped) |

**Canonical Path Forward:**
1. **Observability** → `src/harness/observability/` + `packages/observability/` (Langfuse)
2. **Memory** → `src/core/memory.py` (YAML+Vector) + `src/core/memory_store.py` (JSONL) unified via `MemoryBridge`
3. **Telemetry** → Single `TelemetryCollector` in harness, re-exported
4. **Health** → Single `HealthReporter` in harness, re-exported
5. **Tracing** → OTel SDK (harness) + Langfuse facade (packages)

---

*Report generated: 2026-08-16*
*Work context: /Users/macbook/mekong-cli*
*Reports path: /Users/macbook/mekong-cli/plans/reports/*
