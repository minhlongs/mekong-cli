# Architecture Review — Mekong CLI

**Date:** 2026-03-11
**Scope:** Core PEV engine, agent system, LLM client, overall system design

---

## 1. Core Architecture: Plan-Execute-Verify (PEV)

The PEV pattern is the DNA of Mekong CLI. Three tightly coordinated components:

```
Goal (string)
  │
  ▼
RecipePlanner (planner.py) ──► Recipe (DAG of RecipeSteps)
  │                                 │
  ▼                                 ▼
RecipeVerifier (verifier.py) ◄── RecipeExecutor (executor.py)
  │
  ▼
VerificationReport
```

### RecipePlanner (`src/core/planner.py`, 659 lines)

- Decomposes goals via LLM or rule-based fallback
- AGI v2: Detects browse/tool/evolve step types from goal text
- DAG-aware: maps task dependencies to 1-based step orders
- `replan_failed_branch()` re-decomposes only failed subtree — smart recovery
- Issues: `_rule_based_decompose` is 180+ lines with 8 branching patterns; needs splitting into strategy classes

### RecipeExecutor (`src/core/executor.py`, 489 lines)

- Supports 5 execution modes: shell, llm, api, tool, browse
- Shell: double-layer security (DANGEROUS_PATTERNS + CommandSanitizer)
- Auto-retry with configurable delay per step
- 300s subprocess timeout prevents hangs
- `shlex.split()` prevents shell injection
- Issue: `_execute_browse_step` / `_execute_tool_step` dynamically import modules — adds latency

### RecipeVerifier (`src/core/verifier.py`, 483 lines)

- Checks: exit_code, file_exists, file_not_exists, output_contains, output_not_contains, custom_checks
- Custom checks: runs subprocess with 30s timeout, sanitized
- `verify_quality_gates()` — Binh Phap 6-front quality enforcement built into verifier
- Strict mode: warnings treated as failures

### RecipeOrchestrator (`src/core/orchestrator.py`, 1048 lines — OVERSIZED)

- Coordinates all PEV phases
- Two execution modes: DAG (parallel) or Sequential
- Self-healing: failed shell steps routed to LLM for corrected command
- AGI v2 post-execution pipeline: reflection + world_model diff + code_evolution + vector_memory + collaboration
- Health endpoint on port 9192 with component checks
- ROIaaS phase completion detector triggers graceful shutdown
- Issue: 1048 lines violates 200-line rule; internal subclasses (StepExecutor, RollbackHandler, ReportFormatter) partially extract logic but orchestrator still too large

---

## 2. Agent System

### AgentBase (`src/core/agent_base.py`, 165 lines)

- Clean ABC with `plan()` + `execute()` abstract, `verify()` optional override
- `run()` implements full PEV loop with retry up to `max_retries`
- `__init_subclass__` warns at class-definition time if methods unimplemented

### Agent Roster (`src/agents/`)

| Agent | File | Domain |
|-------|------|--------|
| LeadHunter | lead_hunter.py | Sales prospecting |
| ContentWriter | content_writer.py | SEO content generation |
| RecipeCrawler | recipe_crawler.py | Recipe discovery |
| GitAgent | git_agent.py | Git operations |
| FileAgent | file_agent.py | File I/O |
| ShellAgent | shell_agent.py | Shell execution |
| MonitorAgent | monitor_agent.py | System monitoring |
| NetworkAgent | network_agent.py | HTTP/network ops |
| WorkspaceAgent | workspace_agent.py | Workspace management |
| DatabaseAgent | database_agent.py | DB operations |
| PluginAgent | plugin_agent.py | Plugin lifecycle |
| AGIBridge | agi_bridge.py | Cross-agent communication |

Additional: .md files (cfo, cmo, coo, cs, cto, etc.) are persona/prompt templates, not code agents.

### Agent Registry

`src/agents/__init__.py` exports `AGENT_REGISTRY` dict — string → class mapping for CLI lookup. Planner uses keyword matching to suggest agents: 9 categories, ~60 keywords total.

---

## 3. LLM Client Architecture (`src/core/llm_client.py`)

9-tier fallback chain with circuit breaker per provider:
1. LLM_BASE_URL (universal, any OpenAI-compatible)
2. OPENROUTER_API_KEY
3. AGENTROUTER_API_KEY
4. DASHSCOPE_API_KEY
5. DEEPSEEK_API_KEY
6. ANTHROPIC_API_KEY
7. OPENAI_API_KEY
8. GOOGLE_API_KEY (Gemini direct)
9. OLLAMA_BASE_URL
10. OfflineProvider (fallback)

Circuit breaker: 3 consecutive failures → 15s cooldown per provider.
LRU cache in `LLMCache` to avoid duplicate API calls.
Hook pipeline (pre/post call) Portkey-inspired for observability.

---

## 4. DAG Scheduler (`src/core/dag_scheduler.py`)

- Topological sort for dependency resolution
- Parallel execution via threads where independent steps exist
- `validate_dag()` checks cycles before execution
- Orchestrator falls back to sequential if DAG invalid

---

## 5. Event Bus + Memory

- `EventBus` (src/core/event_bus.py): pub/sub for cross-component events (RECIPE_AUTO_SAVED, PATTERN_DETECTED etc.)
- `MemoryStore` (src/core/memory.py): in-memory KV for goal history, tied to session
- `VectorMemoryStore` (src/core/vector_memory_store.py): hash-vector similarity for goal retrieval
- `ExecutionHistory` (src/core/execution_history.py): append-only event log, persisted per workflow

---

## 6. Architectural Strengths

- Clear separation: Planner / Executor / Verifier each own their domain
- Security-first execution: two-layer shell sanitization
- Graceful degradation: LLM unavailable → rule-based fallback throughout
- DAG + sequential modes cleanly separated in orchestrator
- AGI modules loaded via `importlib` with `try/except` — optional features don't break core

---

## 7. Architectural Weaknesses

| Issue | Location | Severity |
|-------|----------|----------|
| orchestrator.py is 1048 lines | src/core/orchestrator.py | HIGH |
| raas_auth.py 903 lines | src/core/raas_auth.py | MEDIUM |
| Dynamic imports inside execute_step | executor.py L200, L257 | MEDIUM |
| _rule_based_decompose 180-line method | planner.py | MEDIUM |
| 109K total LOC with only 26% test coverage | src/ | HIGH |
| StepExecutor.execute_and_verify references self.console but class has no console init | orchestrator.py L136 | HIGH (bug) |

---

## 8. Recommendations

1. **Split orchestrator.py** into `workflow_runner.py`, `step_executor.py`, `rollback.py`, `agi_pipeline.py`
2. **Cache dynamic imports** in executor — store BrowserAgent/ToolRegistry as class-level optionals
3. **Refactor planner decompose** into strategy pattern (BrowseStrategy, ToolStrategy, etc.)
4. **Fix StepExecutor.console reference** — `self.console` accessed but never initialized in class
5. **Separate AGI v2 modules** (reflection, world_model) from core PEV to reduce coupling
