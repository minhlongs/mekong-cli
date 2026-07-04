# Handoff Report: Daemon Orchestration & Core Execution Bug Fixes

## 1. Observation
- **Event Loop Blocks (R1)**:
  - In `src/daemon/dispatcher.py`, `dispatch_loop` was calling `self.dispatch()` synchronously on the event loop thread:
    ```python
    result = self.dispatch()
    ```
    This blocked the event loop thread when retrieving worker statuses.
  - In `src/daemon/worker_pool.py`, PM2 commands were run synchronously on every worker status refresh:
    ```python
    return subprocess.run(["pm2"] + args, ...)
    ```
    This occurred on every status retrieval query.
  - In `src/daemon/mission_control.py`, PM2 command execution blocked the main thread.
  - In `src/core/executor.py`, synchronous `time.sleep` and `subprocess.run` calls were executed inside `_execute_shell_step`.
  - In `src/core/verifier.py`, custom check execution used `subprocess.run` synchronously.
- **Mission Control Optimization & Lock Racing (R2 & R3)**:
  - `missions.json` was parsed up to 5 times during status summaries.
  - Concurrent writes and reads to `missions.json` from `task_router.py`, `mission_control.py`, and `mission_dispatch.py` did not serialize access, causing potential race conditions or JSON corruption.
- **LLM Tool Call IDs (R4)**:
  - `src/daemon/agent_loop.py` accessed `tc["id"]` directly, throwing a `KeyError` if the ID was missing or `None`.
- **Upstream Dependencies (R5)**:
  - In `src/core/planner.py`, `replan_failed_branch` generated new steps but discarded original prerequisites, causing steps to execute out of order.

---

## 2. Logic Chain
1. **R1 offloading**: Offloading synchronous PM2 subprocess runs and sleep calls to a thread pool via `concurrent.futures.ThreadPoolExecutor` and calling dispatcher loop's `self.dispatch()` via `asyncio.to_thread(self.dispatch)` prevents blocks on the asyncio event loop.
2. **TTL Caching**: Caching PM2 status checks in `WorkerPool.refresh_status` with a 5.0-second TTL limits expensive PM2 system calls.
3. **R2 Optimization**: Single-pass reading and parsing of `missions.json` in `get_status_summary()` and passing it to individual helper functions eliminates redundant I/O operations.
4. **R3 Locking**: Advisory locking context managers (`locked_read` and `locked_read_write`) implemented in `src/core/file_lock.py` using standard Unix `fcntl.flock` serialize all reads and writes to `missions.json`, preventing JSON data corruption.
5. **R4 Safe Get**: Safe `.get("id")` and random UUID fallback in `agent_loop.py` avoids `KeyError` crashes.
6. **R5 DAG Preservation**: Copying preceding successful step dependencies onto the root steps of the newly decomposed plan maintains DAG execution order.

---

## 3. Caveats
- Advisory locking via `fcntl` is native to macOS/Unix platforms; on Windows, flock fallbacks will fail gracefully without locking.

---

## 4. Conclusion
All specified daemon orchestration and core execution bugs have been successfully resolved following the minimal change principle. Verification via mock and integration tests has succeeded with 100% pass rates.

---

## 5. Verification Method
1. **Full pytest Execution**:
   Verify everything passes by running the project test command:
   ```bash
   poetry run pytest
   ```
   *Result:* `6347 passed, 46 skipped, 67 warnings in 304.71s`
2. **Targeted Tests**:
   Verify our specific changes and new test files:
   ```bash
   poetry run pytest tests/test_file_lock.py tests/test_planner.py tests/daemon/test_agent_loop.py
   ```
   *Result:* `98 passed in 0.54s`
3. **Files to inspect**:
   - `src/core/file_lock.py` (Advisory locks context managers)
   - `tests/test_file_lock.py` (Multi-threaded concurrency simulation)
   - `src/daemon/task_router.py` (Task router locks)
   - `src/daemon/mission_dispatch.py` (Dispatch updater locks)
   - `src/daemon/mission_control.py` (Optimized parsing and lock support)
   - `src/daemon/dispatcher.py` (Async dispatch offloading)
   - `src/daemon/worker_pool.py` (PM2 thread pool and status caching)
   - `src/core/executor.py` & `src/core/verifier.py` (Thread pool offloaded executions)
   - `src/daemon/agent_loop.py` (Fallback tool call IDs)
   - `src/core/planner.py` (Dependency preservation)
