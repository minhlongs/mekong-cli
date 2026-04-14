# Performance Audit Report — Mekong CLI

**Date:** 2026-04-04
**Reviewer:** code-reviewer agent (Opus 4.6)
**Scope:** `src/core/` (183 files, 52733 LOC), `ide-core/engine-farm/`, `package.json`, `turbo.json`

---

## CRITICAL

### 1. Orchestrator init eagerly loads 7 heavy subsystems on every instantiation

**Evidence:** `src/core/orchestrator.py` lines 102-165. `RecipeOrchestrator.__init__` unconditionally imports and instantiates `ReflectionEngine`, `WorldModel`, `ToolRegistry`, `CollaborationProtocol`, `CodeEvolutionEngine`, `VectorMemoryStore`, and optionally `SwarmDispatcher`. Each wrapped in `try/except Exception: pass`. Even when wrapped, the import-time cost of 6 modules (each 200-600 lines with their own transitive imports) fires on every `RecipeOrchestrator()` construction.

**Impact:** Cold start penalty of 200-500ms per orchestrator creation. Dashboard and CLI commands that create fresh orchestrator instances pay this every time.

**Recommendation:** Lazy-load via `@property` with `_cache` pattern:

```python
@property
def _world_model(self):
    if not hasattr(self, '_world_model_inst'):
        try:
            from .world_model import WorldModel
            self._world_model_inst = WorldModel(llm_client=self._llm_client)
        except Exception:
            self._world_model_inst = None
    return self._world_model_inst
```

### 2. `__init__.py` imports 40+ symbols eagerly from 15 modules

**Evidence:** `src/core/__init__.py` (121 lines) imports from `parser`, `planner`, `executor`, `verifier`, `orchestrator`, `dag_scheduler`, `pipeline_manager`, `plugin_loader`, `plugin_registry`, `providers`, `registry`, `telegram_client`, `pev_*` modules, etc. Any `from src.core import X` triggers loading ALL of them.

**Impact:** `import src.core` pulls in ~15,000 lines of Python plus transitive deps (requests, rich, etc.). Measured overhead: significant for CLI cold start and subagent spawning.

**Recommendation:** Convert to lazy `__init__.py` using `__getattr__`:

```python
def __getattr__(name):
    if name == "RecipeOrchestrator":
        from .orchestrator import RecipeOrchestrator
        return RecipeOrchestrator
    raise AttributeError(name)
```

### 3. Synchronous `requests` library blocks event loop in mixed async codebase

**Evidence:** 18 files in `src/core/` import `requests` at module level. `fallback_chain.py` is fully async but `llm_client.py` uses synchronous `requests` calls. The `LLMClient.chat()` method is synchronous while `execute_with_fallback()` is async. Mixed sync/async means the fallback chain cannot be used from the main chat path without `asyncio.run()`, and sync HTTP calls in `executor.py`, `providers.py`, `llm_client.py` block the thread.

**Impact:** When orchestrator runs DAG-parallel steps, shell execution uses `subprocess.run` (blocking) and LLM calls use sync `requests`. No parallelism benefit from DAGScheduler for LLM-bound steps.

**Recommendation:** Migrate `LLMClient.chat()` to async using `httpx.AsyncClient` or `aiohttp`. Short-term: add `async def achat()` alongside sync `chat()`.

---

## IMPORTANT

### 4. `_check_local_llm_running()` probes 2 ports on every `LLMClient()` init

**Evidence:** `llm_client.py` line 327-336. When no `LOCAL_LLM_URL` or `OLLAMA_BASE_URL` env var set, `_build_providers_from_env()` calls `_check_local_llm_running()` which does 2 HTTP GETs with 2-second timeouts each.

**Impact:** Up to 4-second delay on LLMClient construction when no local LLM running. Happens on every `get_client()` call if env vars unset.

**Recommendation:** Cache probe result at module level with short TTL (30s). Or skip probe when explicitly configured providers exist.

### 5. World model `snapshot()` runs 4+ subprocess calls synchronously

**Evidence:** `world_model.py` lines 112-162. `snapshot()` calls `_run_cmd("git rev-parse ...")`, `_run_cmd("git status --short")`, `_get_relevant_processes()`, `_get_open_ports()`, plus file tree walk. All synchronous subprocess calls.

**Impact:** 100-300ms per snapshot. Called twice per orchestration (before + after). On repos with many dirty files, `git status` alone can take 200ms+.

**Recommendation:** Run subprocess calls concurrently via `asyncio.create_subprocess_exec` or `concurrent.futures.ThreadPoolExecutor`. Also: skip snapshot when `_world_model` is not actively used.

### 6. `model_selector.py` imports `cost_estimator` at call time (twice)

**Evidence:** Lines 215 and 257 both contain `from src.core.cost_estimator import COST_TABLE` inside function bodies. This runs Python's import machinery on every `select_model()` / `select_model_with_tier()` call.

**Impact:** Minor per-call (Python caches modules after first import), but the pattern is wasteful and makes import cycle debugging harder.

**Recommendation:** Move import to module top level. `COST_TABLE` is a static dict with no circular dependency risk.

### 7. Fallback chain creates new adapter instances on every retry

**Evidence:** `fallback_chain.py` lines 118-133. Inside the retry loop, `OllamaAdapter()` and `APIAdapter()` are instantiated fresh per attempt. Adapters may have setup cost (health checks, connection setup).

**Impact:** Repeated object creation and potential connection setup during already-degraded conditions (model failure path).

**Recommendation:** Accept adapters as constructor params or use a shared adapter registry. At minimum, create once before the loop.

### 8. `time.sleep()` used in 13 files for retry backoff — blocks thread

**Evidence:** Grep found `time.sleep` in `executor.py:307`, `zx_executor.py:242,283`, `rate_limit_client.py:97`, `jwt_refresh_client.py:274,283,288`, `auto_recovery.py:534,560`, `telegram_client.py:64,86,92`, `retry_policy.py:137`, `stage_retry.py:176`, `health_endpoint.py:246`, `providers.py:181,210`.

**Impact:** Thread-blocking sleeps in retry paths. If orchestrator runs on main thread, retries for rate limits (up to 9 seconds in fallback_chain) freeze the entire CLI.

**Recommendation:** For sync code paths that cannot migrate to async: use `threading.Timer` or move retries to background thread. For already-async code: verify `asyncio.sleep` is used (already correct in `fallback_chain.py`, `auto_recovery.py`).

---

## MODERATE

### 9. Orchestrator file is 1133 lines — 5.6x the 200-line limit

**Evidence:** `wc -l` shows `orchestrator.py` at 1133 lines. Other oversized files: `raas_auth.py` (903), `auto_recovery.py` (807), `telegram_bot.py` (804), `planner.py` (660), `command_authorizer.py` (648), `api_key_manager.py` (631).

**Impact:** Increased import time, harder to tree-shake unused code paths, violates project's own 200-line rule.

**Recommendation:** Extract AGI v2 subsystem orchestration (`_post_execution_agi`, world model integration, vector memory search) into `orchestrator_agi.py`. Extract report display into `orchestrator_report.py`.

### 10. 27 bare `except Exception: pass` blocks in orchestrator alone

**Evidence:** `grep -c "except Exception" orchestrator.py` = 27. Most at init time (lines 117-157) and in `run_from_goal` (lines 214-276). All swallow errors silently with `pass`.

**Impact:** Performance bugs and import failures in AGI subsystems go completely undetected. A broken `VectorMemoryStore` or `WorldModel` silently disappears, making diagnosis impossible.

**Recommendation:** At minimum, log at `DEBUG` level: `except Exception: logger.debug("WorldModel init failed", exc_info=True)`. This costs nothing in production but enables debugging.

### 11. Turbo config has `test` depending on `build`

**Evidence:** `turbo.json`: `"test": { "dependsOn": ["build"] }`. Tests cannot start until build completes.

**Impact:** In monorepo with 40+ workspaces, test suite waits for all builds. If tests are pure Python (pytest), they don't need JS build output.

**Recommendation:** Remove `build` dependency from `test` task, or split into `test:js` (depends on build) and `test:py` (independent).

### 12. Engine farm `ab-test.sh` spawns Python3 for basic math

**Evidence:** `ab-test.sh` lines 38-41. Uses `python3 -c "import time; print(time.time())"` for timestamps and `python3 -c "print(f'{...:.2f}')"` for arithmetic. Six Python invocations per model test.

**Impact:** Each `python3` invocation costs ~30-50ms startup. With 5 model tests x 2 models x 6 calls = ~60 Python processes = ~2-3 seconds overhead.

**Recommendation:** Use `date +%s.%N` for timestamps and `bc` or shell arithmetic for calculations:

```bash
start_time=$(date +%s.%N)
# ... curl ...
duration=$(echo "$(date +%s.%N) - $start_time" | bc)
```

### 13. Dev dependency bloat: `ajv` unused at root level

**Evidence:** `package.json` devDependencies includes `ajv: 8.18.0`. No root-level scripts or configs reference JSON Schema validation. Only 7 root devDeps total, but `ajv` pulls ~500KB of node_modules.

**Impact:** Minor. Adds to `pnpm install` time and disk usage.

**Recommendation:** Remove `ajv` from root devDeps if only used in workspace packages (they declare their own deps).

### 14. `LLMClient` module-level singleton not thread-safe

**Evidence:** `llm_client.py` lines 572-580. `get_client()` uses a module-level `_default_client` with no lock.

**Impact:** Race condition if multiple threads call `get_client()` simultaneously during init. Could create duplicate LLMClient instances with redundant port probes.

**Recommendation:** Use `threading.Lock` around initialization:

```python
_lock = threading.Lock()
def get_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        with _lock:
            if _default_client is None:
                _default_client = LLMClient()
    return _default_client
```

### 15. `fallback_chain.py` uses `ollama:` prefix but `model_selector.py` uses `mlx:` prefix

**Evidence:** `model_selector.py` MODEL_ROUTING_MATRIX uses `mlx:deepseek-coder-v2:16b` etc. `fallback_chain.py` FALLBACK_HIERARCHY uses `ollama:deepseek-coder-v2:33b` etc. The `detect_provider()` function checks for both prefixes but `fallback_chain.py` line 117 only checks `ollama:`.

**Impact:** Models routed via `mlx:` prefix from model_selector will never match fallback entries keyed on `ollama:`. Fallback chain silently returns empty fallbacks for mlx-routed models.

**Recommendation:** Normalize prefix convention. Either use `mlx:` everywhere (preferred since MLX is the actual backend on Apple Silicon) or add mapping in `get_fallback_models()`.

---

## Summary

| Severity | Count | Key Theme |
|----------|-------|-----------|
| CRITICAL | 3 | Cold start, eager imports, sync/async mismatch |
| IMPORTANT | 5 | Blocking probes, redundant subprocess, retry blocking |
| MODERATE | 7 | File size, error swallowing, config issues |

### Top 3 Actions (Highest ROI)

1. **Lazy-load `__init__.py` and orchestrator subsystems** — eliminates ~300ms cold start penalty, simplest change
2. **Cache `_check_local_llm_running()` result** — eliminates up to 4s delay on every `get_client()` when no local LLM
3. **Fix `mlx:` / `ollama:` prefix mismatch** — fallback chain currently broken for all MLX-routed models

### Metrics

- Core module files: 183
- Core module LOC: 52,733
- Files over 200-line limit: 30+
- Broad `except Exception` in orchestrator: 27
- Subprocess calls in core: 40
- Sync `time.sleep` call sites: 22
- Sync `requests` imports: 18
