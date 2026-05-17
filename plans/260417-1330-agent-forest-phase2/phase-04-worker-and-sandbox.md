# Phase 04 — Worker: async queue consumer + per-user sandbox + webhook

## Context Links

- Upstream: `phase-03-gateway-task-endpoints.md` (queue producer).
- DeepSeek doc: "BƯỚC 2.3 — Worker" (we diverge from Docker-in-Docker).
- agent-core: `packages/agent-core/src/agent_core/agents/{ceo,developer}.py` + `tools/file_system.py`.

## Overview

- Priority: P0
- Status: pending
- Implement the queue consumer. For each dequeued job: (1) mark running, (2) run agent-core CEO→Developer flow with `AGENT_CORE_OUTPUTS=outputs/{user_id}/`, (3) persist result, (4) POST webhook if set. Must shut down cleanly on SIGTERM.

## Key Insights

- DeepSeek doc spawns Docker container per job — we DO NOT. Deviation justified: keeps package pip-installable and testable without Docker daemon. Path-based sandbox (`outputs/{user_id}/` with traversal guard) provides tenant isolation adequate for Phase 2 dogfood. Container isolation belongs in a future infra PR.
- `AGENT_CORE_OUTPUTS` is process-global env var → worker MUST run each agent invocation in a subprocess to switch it per user, OR monkeypatch by reloading `agent_core.tools.file_system`. Subprocess is cleaner + survives agent crashes. We use `multiprocessing.Process` with a worker fn that `os.environ["AGENT_CORE_OUTPUTS"] = user_dir` before importing agent-core.
- Concurrency: configurable `WORKER_CONCURRENCY` (default 2). Use `asyncio.Semaphore` + `asyncio.to_thread` wrapping `multiprocessing.Process.join(timeout)`.
- Hard timeout per job: `WORKER_JOB_TIMEOUT_SECONDS` default 300. Kill the subprocess on timeout, mark job failed.
- Webhook: POST the final job envelope JSON. 5s timeout, 2 retries exponential. Never raise — log and continue.
- Graceful shutdown: install SIGTERM/SIGINT handler setting `stop_event`; drain in-flight jobs before exit.

## Requirements

### Functional

- R1: `async run_worker(settings, redis_client)` — main loop; BRPOP `task_queue` with 5s timeout; returns on stop_event.
- R2: `per_user_sandbox(user_id, outputs_base) -> Path` — creates `outputs/{user_id}/`, enforces relative_to() check, returns absolute path.
- R3: `execute_job_in_subprocess(job_envelope, sandbox_dir, timeout) -> (ok, output_text, error)` — spawns multiprocessing.Process running agent-core CEO+Developer flow, captures stdout/stderr + file artifacts list.
- R4: `post_webhook(url, payload, settings)` — httpx POST with 5s timeout, revalidates URL via `security_webhook.validate_webhook_url` (defense-in-depth), swallows errors.
- R5: CLI `agent-forest worker` boots an event loop and awaits `run_worker`.
- R6: Job status transitions: `queued → running → (completed | failed)`. Timestamps updated on each transition via `redis_jobs.update_job_status`.

### Non-functional

- N1: Clean SIGTERM within 10s.
- N2: Worker unit tests run without real Redis (FakeRedis) AND without real LLM (respx-mocked mekongd).
- N3: Worker loop file <200 LOC; subprocess launcher separate file <120 LOC.

## Architecture

```
worker/
├── __init__.py
├── agent_runner.py       # subprocess-targeted function: CEO.plan → Developer.execute
├── sandbox.py            # per_user_sandbox + path traversal guard
├── subprocess_launcher.py # spawn multiprocessing.Process, join with timeout
├── webhook_notifier.py   # post_webhook with retry + SSRF re-check
└── loop.py               # run_worker async main loop
```

Job lifecycle:

```
[Redis LPUSH: "user_001:job_abc"]
        │
        ▼
loop.run_worker — BRPOP
        │
        ▼
  parse "user_id:job_id" → redis_jobs.get_job → envelope
        │
        ▼
  redis_jobs.update_job_status(..., "running")
        │
        ▼
  sandbox.per_user_sandbox(user_id) → Path
        │
        ▼
  subprocess_launcher.run(agent_runner.execute,
                          args=(envelope.prompt, sandbox_dir, mekongd_url),
                          timeout=300)
        │
        ▼
  ┌─────────────┬───────────────┐
  │ ok=True     │ ok=False      │
  │ result=text │ error=text    │
  ▼             ▼
update status=completed / failed + updated_at
        │
        ▼
  if webhook_url: webhook_notifier.post_webhook(envelope)
```

## Related Code Files

### Create

- `packages/agent-forest/src/agent_forest/worker/agent_runner.py` (~100 LOC)
- `packages/agent-forest/src/agent_forest/worker/sandbox.py` (~60 LOC)
- `packages/agent-forest/src/agent_forest/worker/subprocess_launcher.py` (~120 LOC)
- `packages/agent-forest/src/agent_forest/worker/webhook_notifier.py` (~90 LOC)
- `packages/agent-forest/src/agent_forest/worker/loop.py` (~150 LOC)
- `packages/agent-forest/tests/test_worker_sandbox.py` (~60 LOC)
- `packages/agent-forest/tests/test_worker_webhook.py` (~100 LOC)
- `packages/agent-forest/tests/test_worker_agent_runner.py` (~80 LOC, respx-mocked)
- `packages/agent-forest/tests/test_worker_loop.py` (~140 LOC, FakeRedis + stubbed runner)

### Modify

- `packages/agent-forest/src/agent_forest/cli.py`: implement `worker` subcommand.
- `packages/agent-forest/src/agent_forest/worker/__init__.py`: export `run_worker`.

## Implementation Steps

1. `sandbox.py`:
   - `per_user_sandbox(user_id: str, outputs_base: Path) -> Path`: sanitize user_id (regex `^[a-zA-Z0-9_-]{1,64}$`; raise `ValueError` otherwise), mkdir, assert `(outputs_base/user_id).resolve().relative_to(outputs_base.resolve())`.
2. `agent_runner.py` — runs in subprocess:
   - Signature: `def execute(prompt: str, sandbox_dir: str, mekongd_url: str, result_path: str) -> None`.
   - Set `os.environ["AGENT_CORE_OUTPUTS"] = sandbox_dir` + `os.environ["MEKONGD_URL"] = mekongd_url`.
   - Import agent-core **inside** the function (after env set).
   - Build `LLMClient` + `SeedMemory(root=sandbox_dir/".memory")` so each user has isolated memory too.
   - CEO plan → Developer execute first step → write artifact if JSON present (reuse `_maybe_write_artifact` from `agent_core.cli`).
   - Persist structured result `{plan, dev_output, artifact_path, files_written: [...]}` to `result_path` as JSON.
   - Catch all exceptions; write `{error: str}` instead.
3. `subprocess_launcher.py`:
   - `def run(target, args, timeout_seconds) -> dict` using `multiprocessing.get_context("spawn").Process`.
   - Temp file for result JSON; reads back on success.
   - On timeout: `proc.terminate()` then `proc.kill()` after 2s; returns `{ok: False, error: "timeout"}`.
4. `webhook_notifier.py`:
   - `async post_webhook(url, payload, settings)`: re-validate URL; httpx AsyncClient timeout=5s; 2 retries with `[0.5, 2.0]` backoff; log error but never raise.
5. `loop.py`:
   - `async def run_worker(settings, redis_client, *, runner=None, now=None, stop_event=None)`:
     - Default runner = `agent_runner.execute` via `subprocess_launcher.run`; tests inject stub.
     - Semaphore = `asyncio.Semaphore(settings.worker_concurrency)`.
     - SIGTERM/SIGINT → `stop_event.set()` (skip if stop_event injected by caller — test path).
     - Main: `while not stop_event.is_set(): item = await redis.brpop("task_queue", timeout=5); if item: asyncio.create_task(_handle(item))`.
     - `_handle` acquires semaphore, parses, updates status running→completed/failed, posts webhook.
     - On shutdown, `await asyncio.gather(*pending, return_exceptions=True)`.
6. `cli.worker(...)`: build settings, `redis_client = redis.asyncio.from_url(settings.redis_url)`, `asyncio.run(run_worker(settings, redis_client))`.
7. Tests:
   - `test_worker_sandbox.py`: creates dir, rejects `../evil`, rejects `foo/bar`, rejects empty id.
   - `test_worker_webhook.py` (respx-mocked): happy POST, 500 retries then gives up, SSRF URL rejected before request, timeout swallowed.
   - `test_worker_agent_runner.py` (respx-mocked mekongd): runs the subprocess function **in-process** with monkeypatched env; asserts result JSON written and files land under sandbox only. Verify path-traversal attempt from the LLM's JSON response is rejected by agent-core's `file_system._resolve`.
   - `test_worker_loop.py`: FakeRedis preloaded with 2 jobs from different users; stub runner returns fixed result; assert statuses transition and outputs are written to correct user dirs; assert loop exits on stop_event within 6s.

## Todo List

- [x] `sandbox.py` + 4 tests.
- [x] `agent_runner.py` + 3 tests (respx-mocked).
- [x] `subprocess_launcher.py` + timeout test.
- [x] `webhook_notifier.py` + 4 tests (respx).
- [x] `loop.py` with graceful shutdown.
- [x] `test_worker_loop.py` covering 2-user happy path + shutdown.
- [x] `cli.worker` wire-up.
- [x] `ruff check` clean.
- [x] All Phase 04 tests green.

## Success Criteria

- `poetry run agent-forest worker` connects to Redis, logs "Worker ready (concurrency=2)".
- Injecting a queue item yields a `completed` job with artifact at `outputs/{user_id}/...`.
- SIGTERM causes shutdown within 10s with in-flight job finalization (or failure) recorded.
- No cross-user file writes detected in tests.
- Subprocess timeout test marks job `failed` with `error: "timeout"`.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| agent-core's `AGENT_CORE_OUTPUTS` is module-level const | High | Enforce subprocess model; document that in-process sandbox switching is unsupported. |
| multiprocessing "spawn" slow (~500ms) on macOS | Medium | Acceptable for task latency; document; consider forkserver pool in Phase 3. |
| Agent takes >300s on first task due to model cold-start | Medium | Configurable timeout; README notes first run can need 600s. |
| Webhook loop causes DoS via slow endpoint | Medium | httpx 5s timeout + max 2 retries; no connection reuse to slow host. |
| Redis BRPOP blocking coro preventing shutdown | Medium | 5s timeout; outer `while not stop_event.is_set()` checks between polls. |
| subprocess writes outside sandbox via symlink | High | `per_user_sandbox` resolves real path; agent-core's `_resolve` also rejects traversal inside worker process. |

## Security Considerations

- `per_user_sandbox` enforces user_id charset AND resolves symlinks before `relative_to()` check.
- `agent_runner` runs in subprocess with ONLY env `AGENT_CORE_OUTPUTS`, `MEKONGD_URL`, `PATH` set — drops other env (especially `JWT_SECRET=REDACTED_KEY`, `ANTHROPIC_API_KEY` unless explicitly needed by mekongd).
- Webhook re-validates URL in worker because envelope came from Redis (defense-in-depth; a compromised Redis doesn't bypass SSRF guard).
- Result persisted to Redis is bounded (truncate to 64KB before HSET) to prevent memory bomb.
- Logs exclude prompt text; include only `{user_id, job_id, duration_ms, status}`.
- Subprocess stdout/stderr captured and truncated to 8KB in error result; prevents log-based exfil abuse.

## Next Steps

- Phase 05 runs end-to-end integration tests that span gateway → FakeRedis → worker (all in-process) via stubbed runner.
