# Technical Debt & Refactor Plan — Mekong CLI

**Date:** 2026-03-11
**Scope:** File size violations, real TODOs, coupling issues, split recommendations

---

## 1. Real Technical Debt Items

### 1.1 Actual TODOs in Source (2 items)

```
src/commands/ocop_commands.py:83   — TODO: Integrate with LLM client for actual analysis
src/commands/ocop_commands.py:153  — TODO: Integrate with LLM client for actual listing generation
```

Both in OCOP agricultural export commands — LLM stubs returning placeholder output instead of real analysis. Low-risk feature gap, not a core engine issue.

**Fix:** Wire `get_client()` from `src/core/llm_client.py` — same pattern used in executor.

### 1.2 Bug: StepExecutor.self.console Not Initialized

In `orchestrator.py` `StepExecutor.execute_and_verify()` (L136), `self.console.print(...)` is called but `StepExecutor.__init__` never initializes `self.console`. This will raise `AttributeError` on any shell step that fails and triggers self-healing.

```python
# Current (broken):
class StepExecutor:
    def __init__(self, executor, verifier, llm_client, history, telemetry):
        self.executor = executor
        # self.console NEVER SET

    def execute_and_verify(self, step, ...):
        self.console.print("[yellow]🔧 Attempting AI self-correction...[/yellow]")  # AttributeError
```

**Fix:** Add `self.console = Console()` to `StepExecutor.__init__`.

---

## 2. File Size Violations (>200 lines)

Priority order for splitting:

### Priority 1 — CRITICAL (>900 lines)

**`src/core/orchestrator.py` — 1048 lines**

Split into 5 focused modules:

```
src/core/orchestrator.py          (~150 lines) — RecipeOrchestrator entry point only
src/core/step_executor.py         (~180 lines) — StepExecutor class
src/core/rollback_handler.py      (~80 lines)  — RollbackHandler class
src/core/report_formatter.py      (~60 lines)  — ReportFormatter class
src/core/agi_post_execution.py    (~120 lines) — _post_execution_agi pipeline
```

`OrchestrationResult`, `StepResult`, `OrchestrationStatus` → move to `src/core/orchestration_types.py`

**`src/raas/sync_client.py` — 932 lines**

Split into:
```
src/raas/sync_client.py           (~150 lines) — SyncClient main class
src/raas/sync_operations.py       (~200 lines) — per-operation methods
src/raas/sync_retry_logic.py      (~100 lines) — retry/backoff handling
src/raas/sync_serializers.py      (~150 lines) — data transformation
```

**`src/core/raas_auth.py` — 903 lines**

Split into:
```
src/core/raas_auth.py             (~150 lines) — RaaSAuth main class
src/core/raas_jwt_handler.py      (~150 lines) — JWT operations
src/core/raas_session_manager.py  (~150 lines) — session lifecycle
src/core/raas_token_cache.py      (~100 lines) — token caching
```

### Priority 2 — HIGH (700-900 lines)

**`src/lib/raas_gate.py` — 881 lines** → split into `raas_gate_core.py`, `raas_gate_validators.py`, `raas_gate_quota.py`

**`src/core/auto_recovery.py` — 807 lines** → split into `auto_recovery_detector.py`, `auto_recovery_strategies.py`

**`src/core/telegram_bot.py` — 752 lines** → split into `telegram_bot.py`, `telegram_handlers.py`, `telegram_message_builder.py`

### Priority 3 — MEDIUM (500-750 lines)

- `src/commands/raas_maintenance_commands.py` — 743 lines
- `src/cli/billing_commands.py` — 725 lines
- `src/jobs/nightly_reconciliation.py` — 718 lines
- `src/raas/billing_sync.py` — 699 lines
- `src/raas/sdk.py` — 675 lines
- `src/core/planner.py` — 659 lines
- `src/core/command_authorizer.py` — 648 lines

---

## 3. Coupling Issues

### 3.1 orchestrator.py imports 15+ modules at top level

```python
from .dag_scheduler import DAGScheduler, validate_dag
from .event_bus import EventType, get_event_bus
from .execution_history import EventKind, ExecutionEvent, ExecutionHistory
from .executor import RecipeExecutor
from .health_endpoint import register_component_check, start_health_server
from .memory import MemoryEntry, MemoryStore
from .nlu import IntentClassifier
from .parser import Recipe, RecipeStep
from .planner import PlanningContext, RecipePlanner
from .retry_policy import RetryPolicy
from .telemetry import TelemetryCollector
from .verifier import RecipeVerifier, VerificationReport
from .workflow_state import StepStatus, WorkflowState, WorkflowStatus
from .command_sanitizer import CommandSanitizer
from ..raas.phase_completion_detector import get_detector
from ..core.graceful_shutdown import get_shutdown_handler, ...
```

Symptoms: any change to a dependency requires orchestrator reload. Circular import risk increases with each addition.

**Fix:** Introduce `OrchestratorConfig` dataclass to pass dependencies; use lazy init via `_init_agi_module` pattern more broadly.

### 3.2 planner.py `_rule_based_decompose` — 180-line method

8 if/elif branches with duplicated task-dict construction. Violates SRP and OCP.

**Refactor:** Strategy pattern:
```python
class DecompositionStrategy(Protocol):
    def matches(self, goal: str) -> bool: ...
    def decompose(self, goal: str) -> list[dict]: ...

class BrowseStrategy(DecompositionStrategy): ...
class ToolStrategy(DecompositionStrategy): ...
class ImplementStrategy(DecompositionStrategy): ...
# ...

STRATEGIES = [BrowseStrategy(), ToolStrategy(), ImplementStrategy(), ...]
```

### 3.3 Late imports inside methods

Executor imports `BrowserAgent`, `ToolRegistry` inside method bodies on every call:
```python
def _execute_tool_step(self, step):
    from src.core.tool_registry import ToolRegistry  # ← imported every invocation
    registry = ToolRegistry()
```

**Fix:** Cache at class level as optional:
```python
class RecipeExecutor:
    _tool_registry: Optional[ToolRegistry] = None
    _browser_agent: Optional[BrowserAgent] = None
```

---

## 4. Dead Code / Unused Patterns

- `.md` files in `src/agents/` (cfo.md, cmo.md, cto.md etc.) are prompt templates, not Python — should live in `prompts/` or `mekong/personas/` for clarity
- `tests/test_rate_limiting_failing_tests.md` — a markdown file in tests/ dir, likely a note left behind
- `tests/test_hydration_safety.ts` — TypeScript file in Python test suite, never collected by pytest

---

## 5. Optimization Opportunities

| Area | Current | Improvement |
|------|---------|-------------|
| LLM circuit breaker cooldown | 15s | Configurable per provider |
| MemoryStore | In-memory only | Persist to disk for session continuity |
| DAG parallel execution | Thread pool | asyncio.gather for I/O-bound steps |
| CommandSanitizer | Instantiated per call | Singleton / class-level instance |
| Recipe auto-save | MD file per run | Deduplicate by content hash (already uses goal hash) |

---

## 6. Refactor Execution Order

1. **Fix `StepExecutor.console` bug** — 1 line, zero risk
2. **Fix ocop_commands.py TODOs** — wire LLM client, ~20 lines each
3. **Split orchestrator.py** — highest impact, extract StepExecutor first
4. **Split planner._rule_based_decompose** — strategy pattern
5. **Fix late imports in executor** — cache at class level
6. **Split raas_auth.py + sync_client.py** — lower urgency, no core impact
7. **Clean up .ts and .md in tests/** — cosmetic
