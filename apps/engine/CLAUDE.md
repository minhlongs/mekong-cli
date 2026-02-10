# Mekong Engine — Core Execution Engine

> **第三篇 謀攻 (Mou Gong)** — Supreme excellence: winning through planning, not brute force
>
> This file governs CC CLI behavior ONLY when working inside `apps/engine/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Role:** The Plan-Execute-Verify engine — the brain of Mekong CLI
**Source:** `src/core/` Python modules (referenced by this app context)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| CLI Framework | Typer + Rich |
| Validation | Pydantic |
| LLM Client | OpenAI-compatible (via Antigravity Proxy) |
| Testing | pytest |

## Core Components

| Module | Class | Purpose |
|--------|-------|---------|
| `planner.py` | `RecipePlanner` | LLM-powered task decomposition with rule-based fallback |
| `executor.py` | `RecipeExecutor` | Multi-mode runner: shell, LLM, API modes |
| `verifier.py` | `RecipeVerifier` | Result validation with criteria matching |
| `orchestrator.py` | `RecipeOrchestrator` | Full Plan→Execute→Verify with rollback + self-healing |
| `parser.py` | `RecipeParser` | Recipe YAML/MD file parsing |
| `llm_client.py` | `LLMClient` | OpenAI-compatible API client |
| `nlu.py` | `IntentClassifier` | Natural language intent → recipe routing |
| `telemetry.py` | `TelemetryCollector` | Execution tracing and metrics |
| `memory.py` | `MemoryStore` | Goal→recipe matching memory |

## Development Rules (Domain-Specific)

### Python Standards
- Type hinting required for ALL functions
- Docstrings for every class and public method
- `ExecutionResult` dataclass for structured output (exit_code, stdout, stderr, metadata)
- Import typing with `TYPE_CHECKING` guard for circular dependencies

### Architecture Patterns
- Agents inherit `AgentBase` with `plan()` → `execute()` → `verify()` flow
- Orchestrator uses rollback: reverses completed steps via `step.params.rollback`
- Self-healing: LLM corrects failed shell commands automatically
- NLU pre-routing: high-confidence goals skip planning phase

### Testing
- Run with `python3 -m pytest` (not `python`, not available on this Mac)
- 62 tests, ~2.5min runtime (file_stats scans entire repo)
- Test files use snake_case: `test_*.py` (override kebab-case rule)
- pytest-timeout plugin NOT installed — don't use --timeout flag

### Error Handling
- `MekongError` hierarchy in `src/core/exceptions.py`
- `RollbackError` for rollback failures
- All exceptions must be caught and logged

## Quality Gates

- `python3 -m pytest` — all 62 tests must pass
- No `# type: ignore` without justification
- All operations must be idempotent
- Comprehensive logging via Rich console
