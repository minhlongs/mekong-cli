# Phase 03 — Gateway: FastAPI routes + Redis producer

## Context Links

- Upstream: `phase-02-gateway-auth-and-models.md`
- DeepSeek doc: "BƯỚC 2.2.2 — Gateway main.py" + Phase 3's auth glue.
- agent-core path-traversal guard: `packages/agent-core/src/agent_core/tools/file_system.py`.

## Overview

- Priority: P0
- Status: pending
- Wire Phase 02 primitives into a FastAPI app. Expose login, task submission, job polling, listing, health. Push job envelopes to Redis (via `fakeredis` in tests). This is the only phase that touches FastAPI + slowapi integration.

## Key Insights

- Gateway is synchronous-wrapping-async: use `async def` for routes, call blocking `redis` client via `asyncio.to_thread` OR use `redis.asyncio.Redis` — pick **`redis.asyncio`** to avoid thread pool cost and to mirror worker's async loop.
- fakeredis ships `FakeAsyncRedis` that drops into `redis.asyncio` interface — keeps tests hermetic.
- `app_factory.create_app(settings, redis_client)` pattern so tests inject `fakeredis.aioredis.FakeRedis`.
- Per-user job enumeration via sorted set `user_jobs:{user_id}` scored by `created_at` ts. GET /tasks pops newest N.
- Job state keys: `job:{user_id}:{job_id}` — HSET. Cross-user enumeration impossible without user_id prefix.
- Queue key: `task_queue` (global, items = `"{user_id}:{job_id}"`). Worker parses and re-reads user-scoped hash.

## Requirements

### Functional

- R1: `POST /auth/login` — form body (OAuth2PasswordRequestForm) → `TokenResponse`. 401 on bad creds.
- R2: `GET /auth/me` — requires bearer → `MeResponse`.
- R3: `POST /task` — requires bearer + JSON `TaskRequest` → `TaskResponse` (201). Writes job HSET + LPUSH + ZADD. Rate-limited 60/min/user.
- R4: `GET /task/{job_id}` — requires bearer → `JobStatus`. 404 if missing, 403 if owner ≠ caller.
- R5: `GET /tasks?limit=50` — requires bearer → `list[JobSummary]` for caller only.
- R6: `GET /healthz` — no auth → `{status: "ok", redis: "up"|"down"}` (ping Redis with 1s timeout).
- R7: CORS enabled for `http://localhost:3000` by default; configurable via `FOREST_CORS_ORIGINS`.

### Non-functional

- N1: p50 latency for `/task` <30ms excluding Redis hop.
- N2: All 5 endpoints integration-tested in Phase 05.
- N3: No endpoint file >200 LOC — split routers.

## Architecture

```
gateway/
├── app_factory.py       # create_app(settings, redis_client, users_store) -> FastAPI
├── deps.py              # current_user dependency (JWT → User)
├── routes_auth.py       # /auth/login, /auth/me
├── routes_tasks.py      # /task, /task/{id}, /tasks
├── routes_health.py     # /healthz
└── redis_jobs.py        # push_job, get_job, list_user_jobs — pure Redis adapter
```

Request flow:

```
client
  │ POST /auth/login (form)
  ▼
routes_auth.login
  └> users_store.authenticate → auth_jwt.create_access_token → TokenResponse

client
  │ POST /task  Authorization: Bearer <jwt>
  ▼
deps.current_user (decode jwt → users_store.get_by_id)
  │
  ▼
routes_tasks.create_task
  │ slowapi limit 60/min (user key)
  │ validate_webhook_url (if provided)
  │ redis_jobs.push_job(user_id, job_id, envelope)
  │   ├─> HSET job:{user_id}:{job_id}
  │   ├─> ZADD user_jobs:{user_id} ts job_id
  │   └─> LPUSH task_queue "{user_id}:{job_id}"
  ▼
TaskResponse(job_id, status=queued)
```

## Related Code Files

### Create

- `packages/agent-forest/src/agent_forest/gateway/app_factory.py` (~120 LOC)
- `packages/agent-forest/src/agent_forest/gateway/deps.py` (~60 LOC)
- `packages/agent-forest/src/agent_forest/gateway/routes_auth.py` (~70 LOC)
- `packages/agent-forest/src/agent_forest/gateway/routes_tasks.py` (~140 LOC)
- `packages/agent-forest/src/agent_forest/gateway/routes_health.py` (~40 LOC)
- `packages/agent-forest/src/agent_forest/gateway/redis_jobs.py` (~120 LOC)
- `packages/agent-forest/tests/test_routes_auth.py` (~70 LOC)
- `packages/agent-forest/tests/test_routes_tasks.py` (~180 LOC)
- `packages/agent-forest/tests/test_routes_health.py` (~40 LOC)
- `packages/agent-forest/tests/test_redis_jobs.py` (~100 LOC)

### Modify

- `packages/agent-forest/src/agent_forest/cli.py`: flesh out `gateway` subcommand to `uvicorn.run(app_factory.create_app(...))`.
- `packages/agent-forest/src/agent_forest/gateway/__init__.py`: export `create_app`.

## Implementation Steps

1. `redis_jobs.py`:
   - Constants: `QUEUE_KEY = "task_queue"`, helpers for `job_key(user_id, job_id)` and `user_zset(user_id)`.
   - `async push_job(r, user_id, job_id, envelope: dict)` — pipeline HSET + ZADD + LPUSH atomically.
   - `async get_job(r, user_id, job_id) -> dict | None`.
   - `async list_user_jobs(r, user_id, limit=50) -> list[dict]`.
   - `async update_job_status(r, user_id, job_id, status, result=None, error=None)` — used by worker but colocated here for DRY.
2. `deps.py`:
   - `async get_settings()` / `get_redis()` / `get_users_store()` — bound via `app.state` in factory.
   - `async current_user(token: str = Depends(OAuth2PasswordBearer(...))) -> User`.
3. `routes_auth.py`:
   - `POST /auth/login` (form) with slowapi 10/min per-IP limit (prevents brute force).
   - `GET /auth/me`.
4. `routes_tasks.py`:
   - `POST /task` with 60/min per-user limit. Generate `job_id = f"job_{uuid4().hex[:12]}"`. Envelope: `{job_id, user_id, prompt, webhook_url, status:"queued", created_at, updated_at, result:None, error:None}`.
   - `GET /task/{job_id}` — owner check.
   - `GET /tasks?limit=N` (N in 1..200).
5. `routes_health.py`: PING Redis with 1s timeout; return downgraded status but 200.
6. `app_factory.create_app(settings, redis_client=None, users_store=None, limiter=None)`:
   - Lazy-init defaults if None.
   - `app.state.settings = settings`; same for redis/users.
   - Register `SlowAPIMiddleware`, `CORSMiddleware`, mount routers.
   - Attach `app.state.limiter` so routers can reference.
7. `cli.gateway(port: int = None, host: str = None)`: build settings, build deps, run uvicorn.
8. Tests — use `fastapi.testclient.TestClient(create_app(settings, redis_client=FakeRedis(), users_store=UsersStore.default()))`:
   - login happy + wrong password + missing user
   - /auth/me happy + missing token + expired token
   - POST /task happy (verify HSET + LPUSH + ZADD state in fakeredis), rejects http:// webhook, rejects 8001-char prompt, rejects no auth, rejects rate-limit after 60 posts
   - GET /task/{id} happy + 404 + cross-user 403
   - GET /tasks returns only own + respects limit
   - /healthz with live redis + with broken redis (monkeypatch PING to raise)
   - redis_jobs unit tests directly against FakeRedis

## Todo List

- [x] `redis_jobs.py` + 4 unit tests.
- [x] `deps.py`.
- [x] `routes_auth.py` + 3 tests.
- [x] `routes_tasks.py` + 7 tests (incl. rate limit + cross-user).
- [x] `routes_health.py` + 2 tests.
- [x] `app_factory.py` with CORS + slowapi wiring.
- [x] `cli.py` gateway subcommand implementation.
- [x] `ruff check` clean.
- [x] All Phase 03 tests green.

## Success Criteria

- `poetry run agent-forest gateway --port 8765` boots and `/healthz` returns 200.
- All Phase 03 tests pass.
- Manual curl login → store token → POST /task → GET /task/{id} yields `status: "queued"`.
- Cross-user GET returns 403.
- 61st POST within 60s returns 429.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| slowapi + async middleware version skew | High | Pin `slowapi==0.1.9`, integration-test rate-limit path. |
| `redis.asyncio` vs `fakeredis.aioredis.FakeRedis` API drift | Medium | Test surface against fakeredis in CI; document pinned `fakeredis>=2.23`. |
| uvicorn reload mode breaks DI | Low | Disable reload by default; document `--reload` as dev-only. |
| Rate limiter pre-auth (login) vs post-auth (task) config mix-up | Medium | Two decorators; integration test both. |

## Security Considerations

- Every authenticated route uses `Depends(current_user)` — no token bypass path.
- OAuth2PasswordRequestForm requires `python-multipart` (already in agent-core style deps).
- `TaskRequest.webhook_url` validated via `security_webhook.validate_webhook_url` BEFORE Redis write; failure → HTTP 400.
- Redis key namespacing per-user guarantees enumeration resistance.
- Login rate limit 10/min/IP deters credential stuffing.
- CORS origins from env — default deny if misconfigured.
- Logs MUST NOT include prompt contents (may contain secrets) — log only `{job_id, user_id}`.

## Next Steps

- Phase 04 worker consumes queue items produced here.
- Phase 05 writes end-to-end tests spanning gateway+worker via shared FakeRedis.
