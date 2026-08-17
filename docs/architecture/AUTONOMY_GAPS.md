# Autonomy Gaps

## Missing Interfaces

### 1. Buzz Integration Adapter

**Gap:** No adapter exists to receive goals from Buzz and feed them into `MekongCoreRuntime`.

**Required interface:**
```python
class BuzzAdapter(Protocol):
    def receive_goal(self, payload: dict) -> Goal: ...
    def send_update(self, status: str, data: dict) -> None: ...
    def receive_feedback(self, feedback: dict) -> None: ...
```

**Current workaround:** Goals are passed as strings to `runtime.run(goal_text)`. No structured input.

**Risk:** HIGH — Buzz integration is the primary external trigger for autonomous mode.

---

### 2. Stream / Structured Output on LLMRouter

**Gap:** `LLMRouter` Protocol has `generate()` returning `str`. No streaming or structured output.

**Required additions:**
```python
def stream(self, prompt: str, model: str | None = None) -> Iterator[str]: ...
def structured_output(self, prompt: str, schema: dict, model: str | None = None) -> dict: ...
```

**Current workaround:** Full output returned as string. Caller parses if needed.

**Risk:** MEDIUM — Streaming needed for long-horizon tasks. Structured output needed for plan generation.

---

### 3. Memory Separation (Short-term vs Long-term)

**Gap:** Single `MemoryStore` / `ScopedMemoryStore`. No distinction between session memory (short-term) and persistent knowledge (long-term).

**Required interface:**
```python
class MemoryTier(Enum):
    SESSION = "session"    # Ephemeral, cleared after goal
    PERSISTENT = "persistent"  # Survives across goals
    ARCHIVE = "archive"    # Cold storage

class MemorySeparation(Protocol):
    def store(self, key: str, value: bytes, tier: MemoryTier) -> None: ...
    def retrieve(self, key: str, tier: MemoryTier) -> bytes | None: ...
    def flush_session(self) -> None: ...
```

**Current workaround:** All memory is in one store. Session memory never explicitly cleared.

**Risk:** MEDIUM — Memory leaks across long-running sessions. No TTL-based eviction.

---

### 4. Mission-Level Observability

**Gap:** Telemetry traces individual operations. No end-to-end mission trace (goal → plan → execute → verify → commit).

**Required interface:**
```python
class MissionTracer(Protocol):
    def start_mission(self, goal: str) -> MissionId: ...
    def log_step(self, mission_id: MissionId, step: str, result: Result) -> None: ...
    def end_mission(self, mission_id: MissionId, outcome: str) -> MissionRecord: ...
    def query_missions(self, filter: MissionFilter) -> list[MissionRecord]: ...
```

**Current workaround:** Telemetry events are emitted but not correlated into mission traces.

**Risk:** MEDIUM — Without mission traces, debugging autonomous runs is hard.

---

## Unsafe Execution Paths

### 5. No Approval Gate for HIGH Risk Actions

**Gap:** `Governance.classify()` classifies actions but `runtime_adapter.py` doesn't gate execution based on classification.

**Current flow:**
```
runtime.execute(task) → delegates → runs tool
```

**Missing gate:**
```
runtime.execute(task) → governance.classify(task) → if HIGH: require_approval() → if FORBIDDEN: deny
```

**Risk:** HIGH — Autonomous runtime could execute destructive actions without human approval.

**Fix:** Add `execute_with_governance()` method that checks `ActionClass` before delegating.

---

### 6. No Cost Limit Enforcement

**Gap:** `LLMRouter.estimate_cost()` exists but cost is never checked against budget/limit before execution.

**Current flow:**
```
runtime.execute(task) → estimate_cost() → ignore result → execute
```

**Missing gate:**
```
runtime.execute(task) → estimate_cost() → if cost > budget: pause/approve
```

**Risk:** MEDIUM — Autonomous loop could exhaust budget without warning.

**Fix:** Add `cost_guard` check in `execute()` before LLM call.

---

### 7. No Retry Limit on repair()

**Gap:** `repair()` method has no retry limit. Could loop infinitely on persistent failures.

**Current flow:**
```
verify() fails → repair() → execute() → verify() → repair() → ... (no limit)
```

**Missing gate:**
```
verify() fails → if retries < MAX_RETRIES: repair() else: abort
```

**Risk:** MEDIUM — Infinite repair loops could exhaust resources.

**Fix:** Add `_repair_count` field to `MekongCoreRuntimeImpl`. Abort after N retries.

---

## State/Memory Ownership Problems

### 8. No Clear Memory Owner

**Gap:** Multiple systems write to memory (`MemoryStore`, `ScopedMemoryStore`, `NeuralMemoryClient`, `MemoryBridge`). No single owner.

**Current state:**
- `runtime_adapter.py` writes observations via `remember()`
- `memory_store_adapter.py` bridges to `MemoryStore`
- `memory_scope.py` adds org isolation
- `memory_client.py` writes to neural store

**Problem:** No transaction boundary. Partial writes on failure.

**Fix:** Designate `ScopedMemoryStore` as canonical owner. All writes go through it.

---

### 9. No Capability State Ownership

**Gap:** `CapabilityBus` registers capabilities but doesn't track who registered them or when they expire.

**Current state:** Capabilities are registered in a dict. No lifecycle management.

**Problem:** Stale capabilities accumulate. No cleanup.

**Fix:** Add `registered_by`, `registered_at`, `expires_at` to `Capability` dataclass. Add cleanup method to `CapabilityBus`.

---

## Missing Observability

### 10. No Trace Correlation IDs

**Gap:** Telemetry events have no correlation ID linking them to a mission or goal.

**Current state:** Each event has `timestamp` and `payload`. No `mission_id` or `goal_id`.

**Problem:** Cannot trace a full autonomous run from start to finish.

**Fix:** Add `mission_id` to `TelemetryEvent`. Propagate through runtime methods.

---

### 11. No Cost Tracking in Telemetry

**Gap:** `estimate_cost()` returns cost but cost is never emitted to telemetry.

**Current state:** Cost is calculated but discarded.

**Problem:** Cannot track spending per mission/agent/task.

**Fix:** Emit cost in telemetry event payload after each LLM call.

---

## Summary

| Gap | Severity | Type |
|-----|----------|------|
| Buzz Adapter | HIGH | Missing interface |
| Stream/Structured Output | MEDIUM | Missing interface |
| Memory Separation | MEDIUM | Missing interface |
| Mission Observability | MEDIUM | Missing interface |
| No HIGH-risk approval gate | HIGH | Unsafe execution |
| No cost limit | MEDIUM | Unsafe execution |
| No retry limit | MEDIUM | Unsafe execution |
| Memory ownership | MEDIUM | State problem |
| Capability state | LOW | State problem |
| Trace correlation IDs | MEDIUM | Missing observability |
| Cost tracking | LOW | Missing observability |