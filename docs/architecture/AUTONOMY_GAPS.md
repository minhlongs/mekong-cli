# Autonomy Gaps

> Re-verified: 2026-08-23 · HEAD: 0878f966f

All 11 gaps below were re-assessed against the tree at HEAD `0878f966f`, after
the 142-file deletion sweep (PR #2). **All 11 remain CLOSED — no regression was
introduced by the sweep.** Each verdict below carries fresh file/line evidence
captured at this HEAD. Where a closure is real but weakened by production
wiring, that is called out explicitly.

**Test evidence:** 40/40 targeted gap-closure tests pass at HEAD
(`tests/test_buzz_adapter.py`, `tests/test_mission_tracer.py`,
`tests/test_e2e_mission.py`, `tests/test_10_missions.py`,
`tests/test_tool_permission_registry.py`).

## Missing Interfaces

### 1. Buzz Integration Adapter

**Status:** CLOSED-weakened (re-verified 2026-08-23)

**Gap:** No adapter exists to receive goals from Buzz and feed them into `MekongCoreRuntime`.

**Required interface:**
```python
class BuzzAdapter(Protocol):
    def receive_goal(self, payload: dict) -> Goal: ...
    def send_update(self, status: str, data: dict) -> None: ...
    def receive_feedback(self, feedback: dict) -> None: ...
```

**Verdict at HEAD:** `BuzzAdapter` exists with all three methods
(`buzz_adapter.py:26-67`). `receive_goal` parses `goal`/`text`, `context`,
`callback_url`, `mission_id` and raises on a missing goal. **Weakened:**
`send_update` (`buzz_adapter.py:61-63`) only *builds* a status dict — it never
POSTs to `callback_url`. The callback is constructed but not transmitted, so
Buzz receives no asynchronous status. `runtime.run_from_payload`
(`runtime_adapter.py:191-212`) wraps the adapter for structured goals.

**Risk:** HIGH — Buzz integration is the primary external trigger for autonomous mode.

---

### 2. Stream / Structured Output on LLMRouter

**Status:** CLOSED-partial (re-verified 2026-08-23)

**Gap:** `LLMRouter` Protocol has `generate()` returning `str`. No streaming or structured output.

**Required additions:**
```python
def stream(self, prompt: str, model: str | None = None) -> Iterator[str]: ...
def structured_output(self, prompt: str, schema: dict, model: str | None = None) -> dict: ...
```

**Verdict at HEAD:** Both methods exist on the Protocol
(`protocols.py:147-148`) and are implemented in `LLMRouterAdapter`.
**Partial:** `stream` yields exactly ONE chunk — the full response — because
`LLMClient` has no native streaming; this is a documented limitation
(`llm_router_adapter.py:107ff`). `structured_output` delegates to
`LLMClient.generate_json` (`llm_router_adapter.py:127-141`).

**Risk:** MEDIUM — Streaming needed for long-horizon tasks. Structured output needed for plan generation.

---

### 3. Memory Separation (Short-term vs Long-term)

**Status:** CLOSED (re-verified 2026-08-23)

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

**Verdict at HEAD:** `MemoryTier` defines SESSION/PERSISTENT/ARCHIVE with TTLs
(`memory_separation.py:19-31`). `flush_session` is wired into the runtime
(`runtime_adapter.py:165` in `start_mission`, and `runtime_adapter.py:373-378`).

**Risk:** MEDIUM — Memory leaks across long-running sessions. No TTL-based eviction.

---

### 4. Mission-Level Observability

**Status:** CLOSED (re-verified 2026-08-23)

**Gap:** Telemetry traces individual operations. No end-to-end mission trace (goal → plan → execute → verify → commit).

**Required interface:**
```python
class MissionTracer(Protocol):
    def start_mission(self, goal: str) -> MissionId: ...
    def log_step(self, mission_id: MissionId, step: str, result: Result) -> None: ...
    def end_mission(self, mission_id: MissionId, outcome: str) -> MissionRecord: ...
    def query_missions(self, filter: MissionFilter) -> list[MissionRecord]: ...
```

**Verdict at HEAD:** `mission_tracer.py` is intact and wired into the runtime
(`runtime_adapter.py:134` tracer field, `:170-181` start_mission, `:449-476`
step/finish). The PR #2 deletion of `telemetry_hooks.py` did **NOT** break
mission tracing — the tracer and collector are independent of the removed
upload pipeline. **Caveats:** the tracer is in-memory only
(`mission_tracer.py:43`), and the plain `run()` path never calls
`start_mission`, so `_mission_id` stays `None` and steps are silently untraced
for non-payload runs.

**Risk:** MEDIUM — Without mission traces, debugging autonomous runs is hard.

---

## Unsafe Execution Paths

### 5. No Approval Gate for HIGH Risk Actions

**Status:** CLOSED-class-level / INERT-in-prod-wiring (re-verified 2026-08-23)

**Gap:** `Governance.classify()` classifies actions but `runtime_adapter.py` doesn't gate execution based on classification.

**Current flow:**
```
runtime.execute(task) → delegates → runs tool
```

**Missing gate:**
```
runtime.execute(task) → governance.classify(task) → if HIGH: require_approval() → if FORBIDDEN: deny
```

**Verdict at HEAD:** The gate is implemented in `execute()`
(`runtime_adapter.py:254-278`) — FORBIDDEN is denied, REVIEW_REQUIRED requires
approval. **But it is INERT in production wiring:** the prod constructor
(`run.py:37-46`) omits `governance=`, so `self._governance` is `None` and the
gate never fires for `mekong run`.

**Risk:** HIGH — Autonomous runtime could execute destructive actions without human approval.

**Fix:** Add `execute_with_governance()` method that checks `ActionClass` before delegating.

---

### 6. No Cost Limit Enforcement

**Status:** CLOSED-class-level / INERT-in-wiring (re-verified 2026-08-23)

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

**Implemented:** `MekongCoreRuntimeImpl` accepts an optional `max_cost_usd`
ceiling (`runtime_adapter.py:120,136`). `_check_cost_guard()`
(`runtime_adapter.py:411-430`) accumulates estimated cost across tasks and
returns an error string when the ceiling would be breached, short-circuiting
`execute()` before the LLM call. Spend is tracked on `_spent_cost_usd` and
reset per mission via `start_mission()`. When no ceiling is configured the
guard is a no-op and behavior is unchanged.

**Verdict at HEAD:** Cost-guard commits `9dc6c6237` and `850f25acc` are both
verified ancestors of HEAD; the code is present. **But it is INERT in
production wiring:** `run.py` omits `max_cost_usd=`, so the guard never
activates for `mekong run`.

**Fix:** Add `cost_guard` check in `execute()` before LLM call.

---

### 7. No Retry Limit on repair()

**Status:** CLOSED (re-verified 2026-08-23)

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

**Verdict at HEAD:** `_MAX_REPAIR_ATTEMPTS = 3` (`runtime_adapter.py:116`).
The task loop (`runtime_adapter.py:392-409`) caps repair attempts, and
`repair()` escalates after 3 retries (`runtime_adapter.py:346-354`).

**Fix:** Add `_repair_count` field to `MekongCoreRuntimeImpl`. Abort after N retries.

---

## State/Memory Ownership Problems

### 8. No Clear Memory Owner

**Status:** CLOSED-within-runtime (re-verified 2026-08-23)

**Gap:** Multiple systems write to memory (`MemoryStore`, `ScopedMemoryStore`, `NeuralMemoryClient`, `MemoryBridge`). No single owner.

**Current state:**
- `runtime_adapter.py` writes observations via `remember()`
- `memory_store_adapter.py` bridges to `MemoryStore`
- `memory_scope.py` adds org isolation
- `memory_client.py` writes to neural store

**Problem:** No transaction boundary. Partial writes on failure.

**Fix:** Designate `ScopedMemoryStore` as canonical owner. All writes go through it.

**Implemented:** `MemorySeparation.store_raw()` is the single write path for
untagged entries — every fallback route now lands on the canonical
`ScopedMemoryStore` backend. The `remember()` method in `runtime_adapter.py`
falls back to `store_raw()` (not a second backend) when the tiered `store()`
fails (`runtime_adapter.py:360-370`), ensuring there is exactly one memory
owner within the runtime. **Caveat:** broader multi-store sprawl across the
repo (tenants.db, seed memory, memory_canonical vs memory_store) persists
outside the runtime boundary.

---

### 9. No Capability State Ownership

**Status:** CLOSED (re-verified 2026-08-23)

**Gap:** `CapabilityBus` registers capabilities but doesn't track who registered them or when they expire.

**Current state:** Capabilities are registered in a dict. No lifecycle management.

**Problem:** Stale capabilities accumulate. No cleanup.

**Fix:** Add `registered_by`, `registered_at`, `expires_at` to `Capability` dataclass. Add cleanup method to `CapabilityBus`.

**Implemented:** `Capability` now carries ownership fields
(`registered_by`/`registered_at`/`expires_at`, `capability.py:64-66`) plus
`is_expired()` (`capability.py:73`). `InMemoryCapabilityBus` is the canonical
implementation: it stamps a default owner on `register()`, refuses expired
capabilities in `execute()`, and evicts them in `cleanup()`. The
`CapabilityBus` Protocol gained a `cleanup()` method so any adapter can
implement the same lifecycle.

---

## Missing Observability

### 10. No Trace Correlation IDs

**Status:** CLOSED (re-verified 2026-08-23)

**Gap:** Telemetry events have no correlation ID linking them to a mission or goal.

**Current state:** Each event has `timestamp` and `payload`. No `mission_id` or `goal_id`.

**Problem:** Cannot trace a full autonomous run from start to finish.

**Verdict at HEAD:** `TelemetryEvent` carries `mission_id`
(`telemetry_collector.py:39`), and the runtime propagates it into emitted
events (`runtime_adapter.py:328,389`). **Caveat:** the same `None` caveat as
gap #4 applies — plain `run()` never starts a mission, so `mission_id` is
`None` for non-payload runs.

**Fix:** Add `mission_id` to `TelemetryEvent`. Propagate through runtime methods.

---

### 11. No Cost Tracking in Telemetry

**Status:** CLOSED (re-verified 2026-08-23)

**Gap:** `estimate_cost()` returns cost but cost is never emitted to telemetry.

**Current state:** Cost is calculated but discarded.

**Problem:** Cannot track spending per mission/agent/task.

**Verdict at HEAD:** `estimated_cost` is computed in `execute()`
(`runtime_adapter.py:283-290`) and propagated through `observe()` into the
telemetry event (`runtime_adapter.py:317-333`), so cost lands in telemetry and
memory per task.

**Fix:** Emit cost in telemetry event payload after each LLM call.

---

## NEW WIRING DEFECTS (found this refresh)

These are not regressions of the 11 gaps above — they are production-wiring
defects discovered during the 2026-08-23 re-assessment that weaken several
closures in practice.

1. **`mekong run` production path is BROKEN.** `_NullTelemetry`
   (`run.py:54-58`) defines only `record_event()`, but the runtime calls
   `self._telemetry.emit(...)` unconditionally (`runtime_adapter.py:324,389`).
   Verified statically: `hasattr(_NullTelemetry(), "emit") == False` →
   `AttributeError` at the first `observe()`. The production constructor also
   omits `governance=`, `max_cost_usd=`, and a tracer, so the approval gate
   (gap #5), cost guard (gap #6), and mission tracing (gap #4) are all INERT
   in prod wiring.
2. **`GOVERNANCE_AUTO_APPROVE` env bypass.** `governance.py:124-128`
   auto-approves REVIEW_REQUIRED actions when `GOVERNANCE_AUTO_APPROVE` is set
   to `true`/`1`/`yes`, silently bypassing the human-approval gate.
3. **dna manifests are eval-time-only.** Governance manifests under `dna/` are
   enforced only in evals (`solo_ceo.py`), not in the production runtime path.

## License Gating (post-deletion status)

License gating is **INTACT** after the `license_gate_core.py` deletion. The
gate now lives inline in `src/lib/raas_gate/__init__.py:64-243`
(`RaasLicenseGate`), is consumed by the middleware `src/middleware/license_gate.py:52`,
which is wired into `src/api/gateway_mission_routes.py:31,60`, and is backed by
`engine/license/`. No regression from the sweep.

## Summary

| Gap | Severity | Type | Verdict at HEAD |
|-----|----------|------|-----------------|
| Buzz Adapter | HIGH | Missing interface | CLOSED-weakened (callback never POSTs) |
| Stream/Structured Output | MEDIUM | Missing interface | CLOSED-partial (stream yields 1 chunk) |
| Memory Separation | MEDIUM | Missing interface | CLOSED |
| Mission Observability | MEDIUM | Missing interface | CLOSED (in-memory; plain run() untraced) |
| No HIGH-risk approval gate | HIGH | Unsafe execution | CLOSED-class / INERT-in-prod-wiring |
| No cost limit | MEDIUM | Unsafe execution | CLOSED-class / INERT-in-wiring |
| No retry limit | MEDIUM | Unsafe execution | CLOSED |
| Memory ownership | MEDIUM | State problem | CLOSED-within-runtime |
| Capability state | LOW | State problem | CLOSED |
| Trace correlation IDs | MEDIUM | Missing observability | CLOSED (mission_id=None caveat) |
| Cost tracking | LOW | Missing observability | CLOSED |

**11 of 11 still closed at HEAD `0878f966f` — no regression from the 142-file
deletion sweep.** Closures #4/#5/#6/#10/#11 are weakened in practice by the
`run.py` wiring omissions and the `_NullTelemetry.emit()` bug documented in
NEW WIRING DEFECTS.
