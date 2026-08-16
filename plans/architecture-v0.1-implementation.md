# Plan: Architecture v0.1 — Make Repo Content Match Target Architecture

**Date:** 2026-08-17
**Mode:** auto --parallel
**Scope:** Fill structural gaps between audit target and current repo

## Brainstorm Contract

**Outcome:** Repo content matches `MEKONG_CORE_CONTRACT.md` target architecture — 9 Protocols implemented, missing interfaces created, repo structure reflects canonical `src/core/` layout.

**Constraints:**
- No production regressions — all existing tests pass
- ruff clean — 0 lint errors
- Preserve working business funnels (Zalo OA, Tax/Accounting, AI Video Factory)
- YAGNI: only implement what the contract explicitly requires

**Non-goals:**
- Don't merge memory systems yet (too risky, needs careful migration)
- Don't add OTel full support (future, needs spec review)
- Don't implement x402/MPP settlement (speculative per audit)

**Acceptance Criteria:**
1. `src/core/runtime_adapter.py` — `MekongCoreRuntime` Protocol implemented
2. `src/core/goal_engine.py` — `GoalEngine` Protocol implemented (not 6-line stub)
3. `src/core/protocols.py` — Formal Protocol definitions for 9 interfaces
4. `src/core/billing_meter.py` — `BillingMeter` Protocol + x402/MPP stub
5. ruff 0 errors, pytest passes

## Scout Summary

- `src/core/` has 50+ modules but NO formal Protocol definitions
- `src/core/goal_engine.py` is a 6-line stub
- `src/core/runtime_adapter.py` MISSING entirely
- `src/core/memory.py` (394 lines) exists as primary MemoryStore
- `src/core/mcu_billing.py` (314 lines) exists as BillingMeter
- `src/core/tool_registry.py` (586 lines) exists but missing `list_mcp_tools`
- `src/core/telemetry_collector.py` (370 lines) exists as ObservabilitySink
- `src/core/verifier.py` (484 lines) exists as VerificationEngine
- All business funnels pass through these modules already

## Implementation Steps

### Step 1: Create Protocol Definitions (src/core/protocols.py)
Define 9 Protocols using Python typing.Protocol:
- MekongCoreRuntime (Buzz adapter)
- LLMRouter
- ToolRegistry
- AgentDispatcher
- BillingMeter
- MemoryStore
- ObservabilitySink
- VerificationEngine
- GoalEngine

### Step 2: Implement RuntimeAdapter (src/core/runtime_adapter.py)
- MekongCoreRuntime Protocol implementation
- Buzz → Core → Goal/Context/Plan/Delegate/Execute/Observe/Verify/Repair/Remember/Commit
- Provider-agnostic: Claude/Qwen/DeepSeek/OpenAI/Local adapters
- MCP/x402/MPP as capability/economic buses

### Step 3: Implement GoalEngine (src/core/goal_engine.py)
- Expand from 6-line stub to real Protocol implementation
- `decompose(goal) → Plan`
- `adapt(plan, failure) → Plan` (replan on failure)
- `commit(plan) → Result`

### Step 4: Extend BillingMeter (src/core/mcu_billing.py)
- Add `settle_payment()` stub (x402/MPP placeholder)
- Add `record_usage()` method
- Ensure Protocol compliance

### Step 5: Extend ToolRegistry (src/core/tool_registry.py)
- Add `list_mcp_tools()` method
- Ensure Protocol compliance

### Step 6: Verify
- ruff check src/core/
- pytest tests/
- Import smoke test for all 9 Protocols