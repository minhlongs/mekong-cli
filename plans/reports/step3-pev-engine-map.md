# PEV Engine Map — src/harness/pev/

## Complete File Listing with Sizes and Purposes

### Core Pipeline Components (src/harness/pev/)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 29 | Public API exports all PEV types and classes |
| `parser.py` | 430 | **Parser** — Markdown recipe → structured PEVRecipe with tokens, engine params, validation |
| `planner.py` | 688 | **Planner** — LLM decomposition of goals into DAG steps with retry/replan logic |
| `executor.py` | 721 | **Executor** — Runs steps (shell, LLM, API, browse, tool) with circuit breaker & retry |
| `verifier.py` | 490 | **Verifier** — Validates execution against criteria (file exists, regex, commands, TODO, logs, types, security) |
| `orchestrator.py` | 258 | **Simple Orchestrator** — Sequential glue: parse → plan → exec → verify → memory |

### Orchestrator Package (src/harness/pev/orchestrator_pkg/)
| File | Lines | Purpose |
|------|-------|---------|
| `__init__.py` | 48 | Re-exports all core orchestrator + harness deps for test patching |
| `runner.py` | 534 | **RecipeOrchestrator** — Full PEV loop with DAG scheduling, rollback, self-healing, AGI integration |
| `step_executor.py` | 129 | StepExecutor — Executes + verifies single step with optional self-healing |
| `models.py` | 58 | OrchestrationStatus, StepResult, OrchestrationResult |
| `display.py` | 95 | ReportFormatter, format_status, display_report (Rich console) |
| `rollback.py` | 153 | RollbackHandler + handle_failure helper |
| `agi.py` | 226 | AGIComponents — Lazy-loaded v2 AGI subsystems (reflection, world-model, etc.) |

### Supporting / Telemetry / State
| File | Lines | Purpose |
|------|-------|---------|
| `pev_types.py` | 125 | Core dataclasses: PromptToken, EngineParams, ValidationConditions, PEVRecipe |
| `nlu.py` | 127 | PEV NLU shim — re-exports core NLU + adds classify_intent_pev, PEV_INTENTS |
| `checkpoint.py` | 103 | Pipeline checkpoint/resume (JSON on disk) |
| `memory.py` | 27 | **Stub** MemoryStore (in-memory dict) |
| `progress_tracker.py` | 203 | ProgressPhase, ProgressTracker with callbacks & ETA |
| `workflow_state.py` | 28 | **Stub** WorkflowState + enums |
| `retry_policy.py` | 14 | **Stub** RetryPolicy with exponential backoff |
| `telemetry.py` | 20 | **Stub** TelemetryCollector |
| `execution_history.py` | 31 | **Stub** ExecutionHistory + EventKind enum |
| `dag_scheduler.py` | 16 | **Stub** DAGScheduler (trivial sequential) |
| `health_checks.py` | 115 | Registers PEV health checks with core health endpoint |
| `metrics_collector.py` | 259 | **Duplicate** of core/pev_metrics_collector.py |
| `structured_logger.py` | 320 | **Duplicate** of core/pev_structured_logger.py |
| `dashboard_data.py` | 147 | **Duplicate** of core/pev_dashboard_data.py |
| `recipes/__init__.py` | 1 | Recipe catalog (empty, just exports) |
| `recipes/__template__.md` | 25 | Recipe Markdown template |

**Total src/harness/pev/: ~5,395 lines**

---

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PEV PIPELINE (Plan → Exec → Verify)              │
└─────────────────────────────────────────────────────────────────────────┘

     ┌──────────────┐
     │   INPUT      │  Goal string OR Markdown recipe file
     │  (goal/md)   │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │   PARSER     │  src/harness/pev/parser.py:RecipeParser
     │  (parse md)  │  → PEVRecipe {prompt_tokens, engine_params, validation, steps}
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │   PLANNER    │  src/harness/pev/planner.py:RecipePlanner
     │  (decompose) │  → PlanningContext → DAG steps with dependencies
     │   via LLM    │  → replan_failed_branch() for retry
     └──────┬───────┘
            │
            ▼
     ┌──────────────────────────────────────────┐
     │           EXECUTOR (per step)            │  src/harness/pev/executor.py:RecipeExecutor
     │  ┌─────┬─────┬─────┬─────┬───────────┐   │
     │  │shell│ LLM │ API │browse│  tool    │   │
     │  └─────┴─────┴─────┴─────┴───────────┘   │
     │  - circuit breaker (per step type)       │
     │  - ExponentialBackoff retry              │
     │  - CommandSanitizer for shell            │
     └──────┬────────────────────────────────────┘
            │ ExecutionResult {exit_code, stdout, stderr, duration_ms}
            ▼
     ┌──────────────────────┐
     │      VERIFIER        │  src/harness/pev/verifier.py:RecipeVerifier
     │  Hard gates (fail):  │  - file_exists, regex_match, command_success
     │  Soft checks (warn): │  - todo_completion, log_probe, no_any_types
     │                      │  - security_scan
     └──────┬───────────────┘
            │ VerificationReport {passed, checks[], errors[], warnings[]}
            ▼
     ┌──────────────┐
     │   MEMORY     │  src/core/memory_bridge.MemoryBridge (via PevBridge adapter)
     │  (persist)   │  → records plan, exec results, verification
     └──────────────┘
```

### Two Orchestration Entry Points

| Orchestrator | Location | Complexity |
|--------------|----------|------------|
| **PEVOrchestrator** | `src/harness/pev/orchestrator.py` | Simple sequential — no DAG, no rollback, no self-heal |
| **RecipeOrchestrator** | `src/harness/pev/orchestrator_pkg/runner.py` | Full — DAG scheduling, parallel groups, rollback, self-heal, AGI, BMAD workflows |

---

## Dependencies on src/core/ (Every Import Listed)

### Direct Imports from src/harness/pev/ → src/core/

| Harness File | Core Module | Imported Names |
|--------------|-------------|----------------|
| `orchestrator.py` | `memory_bridge` | `MemoryBridge`, `MemoryKind`, `MemoryRecord`, `get_bridge` |
| `orchestrator.py` | `pev_metrics_collector` | `get_pev_metrics` |
| `executor.py` | `circuit_breaker` | `get_circuit_breaker` |
| `executor.py` | `crash_detector` | `CrashPatternDetector` |
| `executor.py` | `retry` | `ExponentialBackoff`, `call_with_retry` |
| `executor.py` | `command_sanitizer` | `CommandSanitizer` |
| `executor.py` | `verifier` | `ExecutionResult` |
| `executor.py` | `llm_client` | `get_client` |
| `executor.py` | `tool_registry` | `ToolRegistry` |
| `executor.py` | `browser_agent` | `BrowserAgent` |
| `verifier.py` | `command_sanitizer` | `CommandSanitizer` |
| `parser.py` | `nlu` | `classify_intent` |
| `nlu.py` | `nlu` | `IntentClassifier`, `IntentResult`, `classify_intent`, `classify_intent_pev`, `PEV_INTENTS`, `PEV_ALIAS_KEYWORDS`, `LEGACY_PEV_ALIAS_MAP` |
| `planner.py` | `llm_client` | `get_client` |
| `dashboard_data.py` | `pev_dashboard_data` | `get_dashboard_data` |
| `dashboard_data.py` | `pev_metrics_collector` | `PEVMetricsCollector`, `get_pev_metrics` |
| `metrics_collector.py` | `pev_metrics_collector` | `get_pev_metrics` |
| `structured_logger.py` | `pev_structured_logger` | `get_pev_logger` |
| `health_checks.py` | `pev_health_checks` | `register_pev_health_checks` |
| `health_checks.py` | `health_endpoint` | `ComponentStatus`, `register_component_check` |
| `health_checks.py` | `pev_metrics_collector` | `get_pev_metrics` |

### Core Orchestrator Package (src/core/orchestrator/) — Separate but Related
- `src/core/orchestrator/runner.py` (30K lines!) — Full `RecipeOrchestrator` with BMAD, AGI
- Imports from `src/harness/pev/` via `from ..planner`, `from ..verifier`, etc.
- Re-exports harness deps in `src/core/orchestrator/__init__.py` for test patching

---

## Duplicated Files: src/core/pev_*.py vs src/harness/pev/

| File Pair | Lines (core) | Lines (harness) | Relationship |
|-----------|--------------|-----------------|--------------|
| `pev_dashboard_data.py` | 147 | 147 | **Exact duplicate** — harness re-exports core singleton |
| `pev_metrics_collector.py` | 259 | 259 | **Exact duplicate** — harness re-exports core singleton |
| `pev_structured_logger.py` | 320 | 320 | **Exact duplicate** — harness re-exports core singleton |
| `pev_health_checks.py` | 115 | 115 | **Exact duplicate** — harness re-exports core register fn |
| `pev_checkpoint.py` | 10 | 103 | **Thin wrapper** — core delegates to harness.CheckpointStore |

**Pattern**: `src/core/pev_*.py` are **canonical implementations**; `src/harness/pev/` copies re-export them for backward compatibility. The core versions are the source of truth.

**Exception**: `checkpoint.py` — harness has full implementation (103 lines), core is 10-line delegator.

---

## Recipe System Relationship

```
src/harness/pev/recipes/
├── __init__.py          # Empty catalog
├── __template__.md      # Template with frontmatter + sections
└── hello-world.md       # Example recipe (549 bytes)

Root /recipes/ (not in harness):
└── cloudflare/          # Client project recipes (not PEV)
```

**Parser** (`parser.py:430`) reads Markdown recipes with YAML frontmatter:
```yaml
---
id: recipe-id
name: "Readable Name"
intent: deploy
model: claude-sonnet-4
temperature: 0.2
retries: 3
---
```

**Planner** (`planner.py:688`) can also generate recipes from goals via LLM.

**RecipeOrchestrator** (`runner.py`) can load BMAD workflows from `packages/core/bmad/loader.py`.

---

## State Management Inventory

| State Type | Location | Persistence |
|------------|----------|-------------|
| **Pipeline Checkpoint** | `checkpoint.py:CheckpointStore` | JSON file `.pev/checkpoints/{pipeline_id}.json` |
| **In-Memory Memory** | `memory.py:MemoryStore` | Ephemeral (dict) — wrapped by `PevBridge` for MemoryBridge |
| **Metrics** | `metrics_collector.py:PEVMetricsCollector` | In-memory + periodic disk snapshot |
| **Structured Logs** | `structured_logger.py:PEVStructuredLogger` | JSON lines to stdout/file |
| **Execution History** | `execution_history.py:ExecutionHistory` | In-memory list (stub) |
| **Progress Tracking** | `progress_tracker.py:ProgressTracker` | In-memory with callbacks |
| **Workflow State** | `workflow_state.py:WorkflowState` | In-memory dataclass (stub) |
| **Dashboard Data** | `dashboard_data.py:PEVDashboardData` | Reads from metrics + checkpoint files |

---

## CLI Entrypoints

| Command | File | Orchestrator Used |
|---------|------|-------------------|
| `mekong pev run` | `src/cli/pev_commands.py` | `PipelineManager` → `RecipeOrchestrator` (core) |
| `mekong cook` | `src/cli/cook_command.py` | `RecipeOrchestrator` (core) |
| `mekong workflow` | `src/cli/workflow_commands.py` | BMAD workflows via `RecipeOrchestrator` |

---

## Verifier Line Count Verification

**Plan claim**: 16.2K lines  
**Actual**: `verifier.py` = **490 lines** (src/harness/pev/verifier.py)  
**Core verifier**: `src/core/verifier.py` = ~200 lines (ExecutionResult + basic checks)

**Conclusion**: The 16.2K claim is **incorrect**. The actual verifier is ~490 lines in harness + ~200 in core = **~690 lines total**.

---

## Key Observations

1. **Two parallel orchestrator hierarchies**: 
   - `src/core/orchestrator/` (30K lines, full-featured with AGI/BMAD)
   - `src/harness/pev/orchestrator_pkg/` (1,195 lines, simpler but similar)
   - Core imports from harness; harness imports from core — circular-ish

2. **Massive duplication**: 3 telemetry files (metrics, logger, dashboard) are identical in core and harness (~700 lines each)

3. **Many stubs in harness**: `memory.py`, `workflow_state.py`, `retry_policy.py`, `telemetry.py`, `execution_history.py`, `dag_scheduler.py` — these are minimal stubs, real implementations live in core

4. **Recipe system is Markdown-based** with YAML frontmatter, parsed by `parser.py` into structured `PEVRecipe` with LLM prompt tokens

5. **Memory bridge adapter** (`src/core/adapters/pev_adapter.py`) wraps harness `MemoryStore` to satisfy `MemoryBridge` protocol

6. **NLU is centralized** in `src/core/nlu.py`; harness `nlu.py` is just a re-export shim
