# LLM Router & Agent Dispatcher Architecture Map

## Executive Summary

The Mekong CLI contains **duplicate implementations** across three layers:
- `src/harness/` — original harness layer (being phased out)
- `src/core/` — canonical core layer (production)
- `src/daemon/` — daemon/background worker layer (separate concern)

---

## 9-Stage ALGO Pipeline (src/core/hybrid_router.py)

| Stage | Name | File | Lines | Description |
|-------|------|------|-------|-------------|
| 1 | **CLASSIFY** | `src/core/task_classifier.py` | 102-110 | `classify_task()` → `TaskProfile` (complexity, domain, agent_role, mcu_cost). Also `classify_multi_agent()` for multi-agent workflows |
| 1.5 | **LOAD MATCHING COMMAND** | `src/core/command_loader.py` | 112-123 | `find_best_command()` matches goal to CLI command, injects as system prompt |
| 2 | **MCU CHECK + LOCK** | `src/core/mcu_gate.py` | 124-142 | `MCUGate.try_lock()` — atomic SQLite transaction, reserves MCU credits |
| 3 | **MODEL SELECT** | `src/core/model_selector.py` | 144-156 | `select_model_with_tier()` → `ModelConfig` (model_id, provider, tokens, temp, cost) |
| 4+5+6 | **EXECUTE** | `src/core/agent_dispatcher.py` + `src/core/fallback_chain.py` | 158-248 | Build messages via `build_message_chain()`, execute with `execute_with_fallback()` |
| 7 | **VERIFY OUTPUT** | `src/core/subagent_reviewer.py` | 249-272 | `SubagentReviewer` validates output quality, triggers re-execution if failed |
| 8 | **MCU CONFIRM** | `src/core/mcu_gate.py` | 274-282 | `MCUGate.confirm()` — commits MCU deduction or refunds on failure |
| 9 | **RETURN RESULT** | `src/core/hybrid_router.py` | 284-311 | Adds viral watermark for free tier, returns `MissionResult` |

**Entry Point:** `route_and_execute(goal, tenant_id, mission_id, mcu_gate, system_state)` at line 84

---

## Agent Dispatcher Comparison (3 Implementations)

| Aspect | `src/harness/agents/dispatcher.py` | `src/core/agent_dispatcher.py` | `src/daemon/dispatcher.py` |
|--------|-----------------------------------|--------------------------------|----------------------------|
| **Purpose** | ALGO 8 — Prompt building + context injection | ALGO 8 Phase B — Adds memory & learning layer | Task dispatch to worker pool |
| **Layer** | Harness (legacy) | **Core (canonical)** | Daemon (background workers) |
| **Key Function** | `build_message_chain(agent_role, goal, tenant_id, domain)` | `build_message_chain(..., inject_memory=True)` | `Dispatcher.dispatch_loop(process_fn)` |
| **Returns** | `(messages, system_prompt)` | `(messages, system_prompt, available_tools)` | Task dispatch orchestration |
| **Memory Injection** | ❌ No | ✅ Yes (`_memory_context_for`, `_duplicate_warning`) | N/A |
| **Hub Loading** | `HUBS_DIR = .../packages/agents/hubs` | Same | N/A |
| **Agent Prompt Dir** | `.../agents` | `.../.mekong/agents` | N/A |
| **Imports By** | `src/harness/core/router.py` | `src/core/hybrid_router.py` | `src/daemon/agent_loop.py`, `mission_control.py` |

**Verdict:** `src/core/agent_dispatcher.py` is **canonical** for LLM routing pipeline. `src/daemon/dispatcher.py` is for **background task queue management** (different concern). `src/harness/agents/dispatcher.py` is **legacy duplicate**.

---

## LLM Provider Abstraction Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM PROVIDER LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  src/harness/core/providers.py  ← DUPLICATE (identical)         │
│  src/core/providers.py           ← CANONICAL                    │
│                                                                  │
│  Classes:                                                        │
│  • LLMProvider (ABC)                                             │
│  • GeminiProvider                                                │
│  • OpenAICompatibleProvider                                      │
│  • OfflineProvider                                               │
│  • LiteLLMProvider (proxy with auto-failback)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  src/harness/core/llm_client.py  ← DUPLICATE (identical)        │
│  src/core/llm_client.py           ← CANONICAL                   │
│                                                                  │
│  Features:                                                       │
│  • Auto-detects 10 provider priority from env vars              │
│  • Runtime failover with circuit breaker (3 failures → 15s cool)│
│  • Portkey-inspired: hooks pipeline, LRU cache                  │
│  • BYOK (Bring Your Own Key) — no proxy by default              │
│  • Presets: mekong/adapters/llm-providers.yaml                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SEED/FOUNDATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  src/seed/llm_client.py         ← LEGACY (Ollama-only, mocked)  │
│                                                                  │
│  Simple Ollama-compatible client:                                │
│  • chat(messages) → str                                         │
│  • embed(text) → list[float]                                    │
│  • No failover, no provider abstraction                         │
│  • Used only in tests & seed/main.py                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Import Chain (Canonical Path)

```python
# In src/core/hybrid_router.py (line 28)
from src.core.llm_client import get_client

# In src/core/llm_client.py (lines 41-47)
from .providers import (
    GeminiProvider,
    LLMProvider,
    LLMResponse,
    OfflineProvider,
    OpenAICompatibleProvider,
)
```

**Important:** `src/harness/core/llm_client.py` re-exports via `src/harness/__init__.py` but **all production code imports from `src.core.llm_client`**.

---

## Classification → Model Selection → Execution Flow

```
┌─────────────────┐
│   User Goal     │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 1: classify_task(goal)            │
│  src/core/task_classifier.py             │
│  Returns: TaskProfile                    │
│  - complexity: simple/standard/complex   │
│  - domain: code/analysis/chat/ops        │
│  - agent_role: coder/analyst/reviewer    │
│  - mcu_cost: 1-10                        │
│  - data_sensitivity: public/sensitive    │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 1.5: classify_multi_agent(goal)   │
│  Returns: List[agent_role]               │
│  (enables multi-agent pipeline)          │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 2: MCUGate.try_lock(tenant, mcu)  │
│  src/core/mcu_gate.py                    │
│  Atomic SQLite: check balance → reserve  │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 3: select_model_with_tier()       │
│  src/core/model_selector.py              │
│  Input: TaskProfile + SystemState        │
│  Output: ModelConfig                     │
│  - model_id (e.g., "gemini-2.5-flash")   │
│  - provider (gemini/openai/anthropic)    │
│  - max_tokens, temperature               │
│  - cost_per_mtok_input/output            │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 4+5: build_message_chain()        │
│  src/core/agent_dispatcher.py            │
│  - load_agent_prompt(agent_role)         │
│  - inject hub context (Water Protocol)   │
│  - inject_memory (past similar tasks)    │
│  - inject duplicate warnings             │
│  Returns: (messages, system_prompt, tools)│
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 6: execute_with_fallback()        │
│  src/core/fallback_chain.py              │
│  - Try primary model                     │
│  - On failure: fallback via TierFallback │
│    Chain (src/core/tier_fallback_chain)  │
│  - CRITICAL: sensitive → NEVER API       │
│    only local models (OfflineProvider)   │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 7: SubagentReviewer.verify()      │
│  src/core/subagent_reviewer.py           │
│  Quality gate → re-execute if needed     │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 8: MCUGate.confirm(refund?)       │
│  Commit or refund MCU                    │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│  STAGE 9: Return MissionResult           │
│  + viral watermark (free tier)           │
└──────────────────────────────────────────┘
```

---

## Canonical vs Duplicate Identification

| File | Status | Reason |
|------|--------|--------|
| `src/core/hybrid_router.py` | ✅ **CANONICAL** | Main entry point, imports from core/* |
| `src/harness/core/router.py` | ❌ **DUPLICATE** | Near-identical, imports from core/*, legacy |
| `src/core/providers.py` | ✅ **CANONICAL** | Has `extra_headers` support |
| `src/harness/core/providers.py` | ❌ **DUPLICATE** | Missing `extra_headers` param |
| `src/core/llm_client.py` | ✅ **CANONICAL** | Imported by 20+ production files |
| `src/harness/core/llm_client.py` | ❌ **DUPLICATE** | Identical, re-exported only for harness compat |
| `src/seed/llm_client.py` | ⚠️ **LEGACY** | Ollama-only, mocked in tests, NOT in routing path |
| `src/core/agent_dispatcher.py` | ✅ **CANONICAL** | Has memory injection (Phase B) |
| `src/harness/agents/dispatcher.py` | ❌ **DUPLICATE** | No memory, different agent dir path |
| `src/daemon/dispatcher.py` | ✅ **SEPARATE CONCERN** | Worker pool task dispatch, not LLM routing |
| `src/daemon/llm_router.py` | ✅ **SEPARATE CONCERN** | Capability-based routing for daemon workers |
| `src/daemon/task_router.py` | ✅ **SEPARATE CONCERN** | Priority queue + DLQ for background tasks |
| `src/daemon/classifier.py` | ✅ **SEPARATE CONCERN** | Simple keyword classifier for daemon missions |

---

## Key Integration Points

1. **Hybrid Router → LLM Client**: `src/core/hybrid_router.py:28` imports `get_client` from `src.core.llm_client`

2. **Fallback Chain → Providers**: `src/core/fallback_chain.py:14` imports `ModelConfig, detect_provider` from `src.core.model_selector`, uses providers via LLM client

3. **Model Selector → Tier Fallback**: `src/core/model_selector.py:13` imports `TierFallbackChain, resolve_tier_chain` from `src.core.tier_fallback_chain`

4. **Agent Dispatcher → Memory**: `src/core/agent_dispatcher.py:169` calls `_memory_context_for()` which queries vector memory store

5. **Daemon Layer Independence**: `src/daemon/*` has its own `llm_router.py`, `task_router.py`, `classifier.py` — **does NOT use** `src/core/hybrid_router.py`

---

## Recommendations

1. **Delete `src/harness/core/router.py`** — duplicate of `src/core/hybrid_router.py`
2. **Delete `src/harness/core/providers.py`** — duplicate of `src/core/providers.py` (missing `extra_headers`)
3. **Delete `src/harness/core/llm_client.py`** — duplicate of `src/core/llm_client.py`
4. **Delete `src/harness/agents/dispatcher.py`** — legacy, missing memory injection
5. **Keep `src/daemon/*` separate** — different architectural concern (background worker orchestration)
6. **Consolidate `src/seed/llm_client.py`** — only used in tests, consider removing or marking deprecated

---

## File:Line Reference Index

- **9-Stage Pipeline**: `src/core/hybrid_router.py:84-311`
- **Task Classifier**: `src/core/task_classifier.py:13-290`
- **Model Selector**: `src/core/model_selector.py:12-496`
- **Cost Estimator**: `src/core/cost_estimator.py:13-92`
- **MCU Gate**: `src/core/mcu_gate.py:16-287`
- **Fallback Chain**: `src/core/fallback_chain.py:10-185`
- **Agent Dispatcher (canonical)**: `src/core/agent_dispatcher.py:66-290`
- **Agent Dispatcher (harness)**: `src/harness/agents/dispatcher.py:62-184`
- **Agent Dispatcher (daemon)**: `src/daemon/dispatcher.py:13-316`
- **Providers (canonical)**: `src/core/providers.py:40-458`
- **LLM Client (canonical)**: `src/core/llm_client.py:24-500+`
- **Tier Fallback Chain**: `src/core/tier_fallback_chain.py:15-140`
- **Hybrid Router (harness dup)**: `src/harness/core/router.py:84-328`
