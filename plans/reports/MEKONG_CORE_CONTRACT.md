# Mekong Core Contract

**Date:** 2026-08-17
**Scope:** Target interface contract for Mekong Core
**Author:** docs-manager (informed by architecture audit reports)

## Summary

This document defines the **target interface contract** for Mekong Core -- the provider-agnostic runtime that Buzz and external consumers call into. It is NOT the current implementation. The contract specifies the exact Protocol classes, method signatures, and supporting types that Mekong Core must expose. Current code has partial implementations scattered across duplicate modules (three agent dispatchers, three orchestrators, six memory systems); this contract provides the single canonical surface those fragments must converge into. All interfaces are provider-agnostic: no LLM vendor, payment processor, or database dependency leaks into the Protocol definitions.

---

## MekongCoreRuntime Interface (Buzz Adapter Contract)

The primary interface that Buzz (and any other caller) uses to interact with Mekong Core. Implements the full autonomous loop: goal decomposition through execution, observation, verification, repair, memory, and commit.

```python
class MekongCoreRuntime(Protocol):
    """Primary interface that Buzz calls to interact with Mekong Core."""

    async def goal(self, intent: str, context: Context) -> Goal:
        """Parse user intent into a structured Goal with criteria and priority."""
        ...

    async def plan(self, goal: Goal) -> Plan:
        """Decompose a Goal into an ordered Plan of Steps."""
        ...

    async def delegate(self, plan: Plan) -> list[Task]:
        """Map Plan steps to concrete Tasks with assigned agents and params."""
        ...

    async def execute(self, task: Task) -> Result:
        """Execute a single Task via the appropriate agent/tool, returning output or error."""
        ...

    async def observe(self, result: Result) -> Observation:
        """Collect metrics, side effects, and quality signals from a Result."""
        ...

    async def verify(self, observation: Observation, criteria: Criteria) -> Verification:
        """Check whether an Observation satisfies the Goal criteria."""
        ...

    async def repair(self, verification: Verification) -> RepairAction:
        """Determine a repair strategy when verification fails."""
        ...

    async def remember(self, observation: Observation) -> MemoryEntry:
        """Persist execution observations to memory for future context."""
        ...

    async def commit(self, result: Result) -> CommitRecord:
        """Atomically finalize a result: record to history, release resources, notify."""
        ...
```

### Loop Semantics

The runtime loop is strictly ordered:

```
goal -> plan -> delegate -> [for each task: execute -> observe -> verify -> (repair if failed)] -> remember -> commit
```

`repair` returns a `RepairAction` with strategy (`retry` | `fallback` | `escalate` | `rollback`). The runtime re-enters the loop at the appropriate point based on strategy. Maximum iteration cap must be enforced externally (e.g., 3 retries before escalate).

---

## Supporting Interfaces

### LLMRouter (Provider-Agnostic)

Wraps the 9-stage ALGO pipeline into a clean Protocol. Current implementation lives in `src/core/hybrid_router.py` (functions: `classify_task`, `select_model_with_tier`, `estimate_cost`, `MCUGate`, `execute_with_fallback`).

```python
class LLMRouter(Protocol):
    """Provider-agnostic LLM routing with classification, selection, and fallback."""

    async def classify(self, task: Task) -> TaskType:
        """Classify task complexity, domain, and agent role."""
        ...

    async def select_model(self, tier: str, task_type: TaskType) -> ModelSelection:
        """Select optimal model+provider for tier and task type."""
        ...

    async def execute(self, prompt: str, model: ModelSelection) -> LLMResponse:
        """Send prompt to selected model, return response."""
        ...

    async def fallback(self, failed: LLMResponse, tier: str) -> LLMResponse:
        """Execute fallback chain when primary model fails."""
        ...
```

### ToolRegistry (MCP-Compatible)

Wraps the current `src/core/tool_registry.py` (532 lines) into a Protocol. Must expose MCP-compatible tool schemas for interop with external MCP clients.

```python
class ToolRegistry(Protocol):
    """Dynamic tool registry with MCP-compatible schema exposure."""

    async def register(self, tool: Tool) -> ToolId:
        """Register a tool (builtin, CLI-discovered, or API-derived)."""
        ...

    async def execute(self, tool_id: ToolId, params: dict) -> ToolResult:
        """Execute a registered tool with given parameters, respecting permission gates."""
        ...

    async def list_tools(self) -> list[Tool]:
        """List all registered tools with metadata."""
        ...

    async def list_mcp_tools(self) -> list[MCPTool]:
        """List tools as MCP-compatible schemas (name, description, inputSchema)."""
        ...
```

**Key constraint:** `CommandSanitizer` (fail-closed) must be enforced at the `execute` boundary. PermissionRegistry gates access per-tool. This is security-critical and must not be bypassable.

### AgentDispatcher (Single Canonical Dispatch)

Replaces three parallel implementations: `src/core/agent_dispatcher.py`, `src/harness/agents/dispatcher.py`, `src/daemon/dispatcher.py`.

```python
class AgentDispatcher(Protocol):
    """Single canonical agent dispatch with prompt loading and memory injection."""

    async def dispatch(self, task: Task, agent: AgentId) -> DispatchResult:
        """Dispatch a task to a specific agent, returning combined output."""
        ...

    async def load_agent(self, agent_id: AgentId) -> Agent:
        """Load agent definition (prompt, context, hub expertise)."""
        ...

    async def list_agents(self) -> list[Agent]:
        """List all available agents with metadata."""
        ...
```

**Current state:** `src/core/agent_dispatcher.py` loads agents from `.mekong/agents/` and `packages/agents/hubs/`. Functions: `build_message_chain`, `load_agent_prompt`. This is the canonical implementation; the harness and daemon copies are duplicates to remove.

### BillingMeter (x402/MPP-Compatible)

Wraps `src/core/mcu_billing.py` (`MCUBilling` class backed by SQLite WAL via `CreditStore`). Must extend for x402/MPP payment protocol support.

```python
class BillingMeter(Protocol):
    """Credit-based billing with x402/MPP payment extension point."""

    async def check_quota(self, principal: str) -> QuotaStatus:
        """Check remaining quota for a principal (org/user)."""
        ...

    async def deduct(self, principal: str, amount: float, currency: str) -> Receipt:
        """Deduct credits and return atomic receipt."""
        ...

    async def get_tier(self, principal: str) -> Tier:
        """Get current tier for a principal (BASIC | PREMIUM | ENTERPRISE | MASTER)."""
        ...

    async def get_balance(self, principal: str) -> Balance:
        """Get current balance for a principal."""
        ...

    async def settle_payment(self, payment: Payment) -> Settlement:
        """x402/MPP extension: settle an external payment into credits."""
        ...
```

**Current state:** `MCUBilling` has `add_credits`, `deduct`, `check_balance` methods backed by SQLite WAL. Tier data comes from `src/seed/config/tiers.py` (`TierKey`). `settle_payment` is the new extension point for x402/MPP and does not exist yet.

### MemoryStore (Single Canonical Memory)

Replaces six current implementations: `memory.py`, `memory_store.py`, `memory_bridge.py`, `vector_memory_store.py`, `memory_scope.py`, `memory_client.py`. The target is a single Protocol that any backend (YAML, JSONL, vector, SQLite) can implement.

```python
class MemoryStore(Protocol):
    """Single canonical memory interface with scope-based access."""

    async def store(self, key: str, value: Any, scope: Scope) -> StoreResult:
        """Persist a value under a key within a scope (session, org, global)."""
        ...

    async def retrieve(self, key: str, scope: Scope) -> Any:
        """Retrieve a value by key within a scope."""
        ...

    async def search(self, query: str, scope: Scope) -> list[MemoryEntry]:
        """Semantic or keyword search within a scope."""
        ...

    async def forget(self, key: str, scope: Scope) -> ForgetResult:
        """Remove a value by key within a scope."""
        ...
```

**Current state:** `memory_store.py` is JSONL append-only with schema `{timestamp, agent, action, outcome, tags}`. `vector_memory_store.py` adds semantic search. `memory_bridge.py` and `memory_scope.py` are adapters. These must converge behind this single Protocol.

### ObservabilitySink (OTel-Compatible)

Wraps `src/core/telemetry_collector.py` (`TelemetryCollector` class with `TelemetryEvent` dataclass). Must produce OpenTelemetry-compatible signals.

```python
class ObservabilitySink(Protocol):
    """OTel-compatible telemetry emission for traces, metrics, and events."""

    async def emit_event(self, event: Event) -> None:
        """Record a structured event (command_executed, session_started, etc.)."""
        ...

    async def emit_metric(self, metric: Metric) -> None:
        """Record a numeric metric (MCU usage, latency, error rate)."""
        ...

    async def emit_trace(self, trace: Trace) -> None:
        """Record a distributed trace span (goal -> plan -> execute -> verify)."""
        ...
```

**Current state:** `TelemetryCollector` emits anonymized events with consent gating (`TelemetryConsent`). Events: `command_executed`, `session_started`, `session_ended`, `error_occurred`. The OTel extension adds trace/span support; the consent model must be preserved.

### VerificationEngine

Wraps `src/core/verifier.py` (`RecipeVerifier` with `VerificationStatus` enum). Note: reports reference `pev/verifier.py` but no `pev/` directory exists -- the verifier is at `src/core/verifier.py` directly.

```python
class VerificationEngine(Protocol):
    """Structured verification of execution results against criteria."""

    async def verify(self, result: Result, criteria: Criteria) -> Verification:
        """Run all applicable checks and return pass/fail with details."""
        ...

    async def check_exit_code(self, result: Result) -> CheckResult:
        """Verify the exit code of a command execution result."""
        ...

    async def check_output(self, result: Result, pattern: str) -> CheckResult:
        """Verify that output matches a regex or exact pattern."""
        ...

    async def check_file(self, path: str) -> CheckResult:
        """Verify that a file exists and meets expectations."""
        ...
```

**Current state:** `RecipeVerifier` in `src/core/verifier.py` implements `VerificationStatus` enum (`PASSED`, `FAILED`, `WARNING`). `CommandSanitizer` is used for safety. The Protocol formalizes the check-by-type pattern.

### GoalEngine

Wraps the partial orchestration in `src/core/orchestrator/runner.py` (`RecipeOrchestrator`). Currently implements `Plan -> Execute -> Verify` but lacks decompose/adapt.

```python
class GoalEngine(Protocol):
    """Goal decomposition, prioritization, and adaptive replanning."""

    async def decompose(self, goal: Goal) -> list[Step]:
        """Break a Goal into atomic Steps with dependencies."""
        ...

    async def prioritize(self, steps: list[Step]) -> list[Step]:
        """Reorder steps by priority, cost, and dependency constraints."""
        ...

    async def adapt(self, plan: Plan, feedback: Feedback) -> Plan:
        """Modify a Plan based on execution feedback or verification failures."""
        ...
```

**Current state:** `RecipeOrchestrator` orchestrates with `RecipePlanner`, `RecipeVerifier`, `RecipeExecutor`, `DAGScheduler`, `RetryPolicy`, and `Constitution` (constitutional review). It imports from `src/core/planner.py`, `src/core/verifier.py`, `src/core/executor.py`, `src/core/dag_scheduler.py`. The `adapt` method does not exist yet; replanning logic is scattered.

---

## Supporting Types

All types are plain Python dataclasses. No framework dependencies.

```python
from dataclasses import dataclass, field
from typing import Any
from enum import Enum

# --- Enums ---

class Tier(str, Enum):
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    ENTERPRISE = "ENTERPRISE"
    MASTER = "MASTER"

class TaskType(str, Enum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_AGENT = "multi_agent"

class PlanStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class RepairStrategy(str, Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    ESCALATE = "escalate"
    ROLLBACK = "rollback"

class Scope(str, Enum):
    SESSION = "session"
    ORG = "org"
    GLOBAL = "global"

# --- Core Types ---

@dataclass
class Context:
    principal: str          # Who/what is executing (org ID or user ID)
    session_id: str         # Conversation/session identifier
    metadata: dict          # Arbitrary context data (model, tier, environment)
    memory: MemoryStore     # Memory backend
    billing: BillingMeter   # Billing backend
    tools: ToolRegistry     # Available tools

@dataclass
class Goal:
    id: str
    intent: str
    context: Context
    criteria: Criteria
    priority: int

@dataclass
class Plan:
    id: str
    goal_id: str
    steps: list[Step]
    status: PlanStatus

@dataclass
class Step:
    id: str
    description: str
    dependencies: list[str]  # Step IDs this depends on
    params: dict

@dataclass
class Task:
    id: str
    step: Step
    agent: AgentId
    params: dict

@dataclass
class Result:
    task_id: str
    output: Any
    error: str | None
    metadata: dict

@dataclass
class Observation:
    result: Result
    metrics: dict
    side_effects: list[SideEffect]

@dataclass
class SideEffect:
    kind: str               # file_write, api_call, db_change, etc.
    target: str
    data: dict

@dataclass
class Criteria:
    checks: list[CheckSpec]

@dataclass
class CheckSpec:
    kind: str               # exit_code | output_pattern | file_exists | custom
    params: dict

@dataclass
class Verification:
    passed: bool
    checks: list[CheckResult]
    failures: list[str]

@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str

@dataclass
class RepairAction:
    strategy: RepairStrategy
    params: dict

@dataclass
class MemoryEntry:
    key: str
    value: Any
    scope: Scope
    timestamp: float

@dataclass
class CommitRecord:
    id: str
    result: Result
    memory_refs: list[str]
    timestamp: float

@dataclass
class ModelSelection:
    provider: str
    model: str
    tier: str

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict
    error: str | None

@dataclass
class Tool:
    id: str
    name: str
    description: str
    tool_type: str          # builtin | cli | api | mcp
    input_schema: dict
    permissions: dict

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict      # JSON Schema

@dataclass
class ToolResult:
    output: Any
    error: str | None
    duration_ms: float

@dataclass
class Agent:
    id: str
    name: str
    prompt: str
    context: dict
    hub_expertise: list[str]

@dataclass
class AgentId:
    name: str               # e.g., "cto", "cmo", "coo"

@dataclass
class DispatchResult:
    agent: AgentId
    output: str
    tokens_used: int
    error: str | None

@dataclass
class QuotaStatus:
    remaining: float
    limit: float
    tier: Tier

@dataclass
class Receipt:
    id: str
    principal: str
    amount: float
    currency: str
    timestamp: float

@dataclass
class Balance:
    credits: float
    tier: Tier

@dataclass
class Payment:
    source: str
    amount: float
    currency: str
    protocol: str           # x402 | mpp | manual

@dataclass
class Settlement:
    success: bool
    credits_added: float
    receipt: Receipt

@dataclass
class StoreResult:
    success: bool
    key: str

@dataclass
class ForgetResult:
    success: bool
    key: str

@dataclass
class Event:
    name: str
    attributes: dict
    timestamp: float

@dataclass
class Metric:
    name: str
    value: float
    unit: str
    attributes: dict

@dataclass
class Trace:
    span_id: str
    parent_span_id: str | None
    name: str
    start_time: float
    end_time: float | None
    attributes: dict

@dataclass
class Feedback:
    plan_id: str
    failed_step: str | None
    error: str | None
    suggestion: str | None
```

---

## Interface Mapping: Current to Target

| Target Interface | Current Implementation | File | Status |
|---|---|---|---|
| `MekongCoreRuntime` | `RecipeOrchestrator` (partial) | `src/core/orchestrator/runner.py` | Missing: `goal`, `delegate`, `observe`, `repair`, `remember`, `commit` |
| `LLMRouter` | `hybrid_router.py` ALGO pipeline | `src/core/hybrid_router.py` | Functions exist: `classify_task`, `select_model_with_tier`, `estimate_cost`, `MCUGate`, `execute_with_fallback`. Not a Protocol. |
| `ToolRegistry` | `MekongToolRegistry` | `src/core/tool_registry.py` | Exists with 4 tool types (builtin/cli/api/mcp). Missing: `list_mcp_tools`, formal Protocol. `CommandSanitizer` already enforced at execute boundary. |
| `AgentDispatcher` | `build_message_chain` + `load_agent_prompt` | `src/core/agent_dispatcher.py` | Exists. Duplicates in `src/harness/agents/dispatcher.py` and `src/daemon/dispatcher.py` must be removed. |
| `BillingMeter` | `MCUBilling` | `src/core/mcu_billing.py` | Exists with SQLite WAL backend. Missing: `settle_payment` (x402/MPP). Tier from `src/seed/config/tiers.py`. |
| `MemoryStore` | 6 implementations | `src/core/memory*.py`, `src/core/vector_memory_store.py` | `memory_store.py` (JSONL), `vector_memory_store.py` (semantic), `memory_bridge.py` (adapter), `memory_scope.py`, `memory_client.py`, `memory.py`. Must converge behind one Protocol. |
| `ObservabilitySink` | `TelemetryCollector` | `src/core/telemetry_collector.py` | Exists with consent gating. Missing: OTel trace/span support. |
| `VerificationEngine` | `RecipeVerifier` | `src/core/verifier.py` | Exists with `VerificationStatus` enum. Note: reports reference `pev/verifier.py` but no `pev/` directory exists. |
| `GoalEngine` | `RecipeOrchestrator` + `RecipePlanner` | `src/core/orchestrator/runner.py`, `src/core/planner.py` | Partial. `decompose` exists in planner. Missing: `adapt` (replan on failure). DAG scheduler exists in `src/core/dag_scheduler.py`. |

### Duplication to Resolve Before Implementation

| Duplicate System | Canonical | Files to Remove |
|---|---|---|
| Agent Dispatcher x3 | `src/core/agent_dispatcher.py` | `src/harness/agents/dispatcher.py`, `src/daemon/dispatcher.py` |
| Orchestrator x3 | `src/core/orchestrator/runner.py` | `src/harness/core/router.py`, `src/daemon/dispatcher.py` |
| TelemetryCollector x2 | `src/core/telemetry_collector.py` | `src/harness/telemetry.py` (if exists) |
| Memory systems x6 | Single `MemoryStore` impl | Merge `memory_store.py` + `vector_memory_store.py`; remove `memory_bridge.py` after convergence |
| Error hierarchies x2 (was x3) | `src/core/exceptions.py` | `pev_errors.py` deleted 2026-08-18 (0 importers). Remaining: merge `error_responses.py` into `exceptions.py` |

---

## Provider-Agnostic Boundaries

The following must NOT appear in any Protocol definition or supporting type:

- LLM vendor names (OpenRouter, Anthropic, OpenAI, Ofable-5, MLX)
- Payment processor names (NOWPayments, Polar, Stripe)
- Database implementations (SQLite, PostgreSQL, Redis)
- Framework imports (FastAPI, Pydantic, SQLAlchemy)
- File system paths (all paths resolved at implementation time, not interface time)

Provider selection happens inside implementations, never at the Protocol boundary.

---

## Confidence Level

| Aspect | Confidence | Rationale |
|---|---|---|
| Interface definitions | HIGH | All methods derived from existing function signatures and report-verified behavior |
| Supporting types | HIGH | Types match current dataclass shapes in codebase |
| Interface mapping | HIGH | Verified against actual file headers and class signatures |
| x402/MPP compatibility | MEDIUM | `settle_payment` is speculative; no x402 implementation exists yet |
| OTel compatibility | MEDIUM | Extension adds trace/span; consent model needs validation |
| Provider-agnostic claims | HIGH | Current `providers.py` already abstracts vendor selection |

---

## Cross-references

- `plans/reports/step2-core-module-map.md` -- full file listing with 77 Python files, 58K lines
- `plans/reports/step6-llm-router-trace.md` -- 9-stage ALGO pipeline details, duplication map
- `plans/reports/step7-tool-execution-trace.md` -- ToolRegistry, CommandSanitizer, permission gates
- `plans/reports/step10-issue-classification.md` -- ISS-001 through ISS-017, prioritized gaps
- `plans/reports/DEPRECATION_MAP.md` -- what to remove before implementing contracts
- `plans/reports/DUPLICATION_MAP.md` -- what to merge before implementing contracts
