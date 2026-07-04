## 2026-05-31T05:09:26Z
You are a worker agent. Your working directory is: /Users/macbook/mekong-cli/.agents/teamwork_preview_worker_fixes.

Your task is to implement the code changes for the Daemon Orchestration and Core Execution bugs in mekong-cli as outlined in the explorer report at `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_fixes_3/handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please implement the following:
1. R1: Event Loop Blocks
- In `src/daemon/dispatcher.py`, convert synchronous PM2/dispatch calls to async (e.g., using `asyncio.to_thread` or running in a thread pool).
- In `src/daemon/worker_pool.py`, convert PM2 synchronous subprocess runs to async or run in a thread pool using `asyncio.to_thread` or similar. Add caching to status checks (like `refresh_status`) to prevent event loop blocks from frequent PM2 calls.
- In `src/daemon/mission_control.py`, convert synchronous PM2 runs to run in a thread pool (`asyncio.to_thread`) or use async equivalents.
- In `src/core/executor.py`, convert synchronous `time.sleep` and command subprocess runs (`subprocess.run`) to async equivalents (`asyncio.sleep`, `asyncio.create_subprocess_exec` or run them in a thread pool / run_in_executor if needed).
- In `src/core/verifier.py`, convert synchronous custom check subprocess runs to async equivalents or run in a thread pool.

2. R2: Optimize PM2 Queries & File I/O
- In `src/daemon/mission_control.py`, optimize `get_status_summary()` to parse `missions.json` (or `JOURNAL_FILE`) once and pass the parsed data to helpers (such as `_calculate_throughput`, `_calculate_success_rate`, `_get_queue_depth`, `_calculate_avg_response_time`, `get_dispatch_queue`, `get_metrics`). Ensure we do not fetch worker status multiple times.

3. R3: Implement File Locking
- In `src/daemon/task_router.py` and `src/daemon/mission_control.py`, implement file locking (using `portalocker` or `filelock` or standard `fcntl` advisory locks) for read/write access to `missions.json` to prevent concurrency conflicts and `json.JSONDecodeError`.

4. R4: Safe Tool Call ID Access
- In `src/daemon/agent_loop.py`, replace direct access to `tc["id"]` with a safe `.get("id")` and fallback to a generated random UUID or dummy string.

5. R5: Preserve Upstream Dependencies
- In `src/core/planner.py`, update `replan_failed_branch()` to preserve the original upstream dependencies pointing to preceding successful steps.

Verification:
- Run the full test suite with `poetry run pytest` and verify that all tests pass.
- Write a report detailing all files modified and verification results to `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_fixes/handoff.md`.
- Once done, send a message to the orchestrator (conversation ID: 72c7f082-eb98-419f-8326-1da0aa46d452) with your completion report.
