# Phase 05 — Integration tests, conftest, docs, polish

## Context Links

- Upstream: all prior phases.
- Sibling conftest: `packages/agent-core/tests/conftest.py` (fixture pattern to mirror).
- DeepSeek doc 2.5: "KIỂM TRA HỆ THỐNG MULTI-TENANT" (two-user curl flow).

## Overview

- Priority: P0
- Status: pending
- Final phase: shared fixtures, cross-component integration tests (gateway → FakeRedis → worker stubbed runner), README v2, migration notes for Phase 3, CI notes. Verify the full two-user isolation story.

## Key Insights

- Full stack runs in a single process for tests: FakeRedis + TestClient for gateway + stubbed `runner` injected into `run_worker`. No sockets, no Docker, no mekongd.
- End-to-end test idiom: in one test, push a job via TestClient → run `run_worker` for ~1 second with `stop_event` auto-set after job completion → poll GET /task/{id}.
- Shared fixtures: `settings` (test defaults incl. short expiry, low bcrypt rounds, small rate limit), `fake_redis`, `users_store`, `api_client`, `tmp_outputs`.
- Document mekongd dependency and the Docker-deferred decision prominently in README so nobody files bug reports expecting container isolation.

## Requirements

### Functional

- R1: `conftest.py` exposes 6+ fixtures reused across tests.
- R2: `test_integration_end_to_end.py` covers full login → submit → worker processes → poll result.
- R3: `test_integration_multi_tenant.py` verifies user_001 cannot see user_002's jobs (list, get, file writes).
- R4: README updated: install, env table, quickstart (two terminals), deviations, security notes, link to Phase 3 plan.
- R5: `MIGRATION-PHASE3.md` listing exact swap points (UsersStore→UserRepo, config→pydantic-settings, local limiter→Redis limiter, subprocess sandbox→docker sandbox).

### Non-functional

- N1: Total test suite runs in <15s.
- N2: `pytest -q` prints ≥40 passed.
- N3: 0 ruff issues, 0 mypy-light issues (if mypy enabled — OPTIONAL, skip if extra scope).

## Architecture

```
tests/
├── conftest.py                      # settings, fake_redis, users_store, api_client, tmp_outputs, stub_runner
├── test_integration_end_to_end.py   # full happy path
├── test_integration_multi_tenant.py # isolation matrix
└── (all Phase 02–04 tests already in place)
```

## Related Code Files

### Create

- `packages/agent-forest/tests/test_integration_end_to_end.py` (~140 LOC)
- `packages/agent-forest/tests/test_integration_multi_tenant.py` (~120 LOC)
- `packages/agent-forest/MIGRATION-PHASE3.md` (~60 LOC)

### Modify

- `packages/agent-forest/tests/conftest.py`: add all shared fixtures listed above.
- `packages/agent-forest/README.md`: v2 with quickstart + deviations + security section.
- `packages/agent-forest/src/agent_forest/__init__.py`: export `create_app` and `run_worker` at package top level for ergonomic import.

## Implementation Steps

1. Expand `conftest.py`:
   - `settings` fixture with test overrides (`FOREST_TESTING=1`, bcrypt rounds=4, rate limit=10/min, expiry=60s, outputs_dir=tmp_path).
   - `fake_redis` — `fakeredis.aioredis.FakeRedis(decode_responses=True)`.
   - `users_store` — `UsersStore.default()` wrapped with test-speed bcrypt.
   - `api_client` — `TestClient(create_app(settings, fake_redis, users_store))`.
   - `tmp_outputs` — tmp path + monkeypatch env.
   - `stub_runner` — callable returning `{ok: True, result: "done", files_written: [...]}` synchronously; tests override.
2. `test_integration_end_to_end.py`:
   - Login as founder1 → bearer token.
   - POST /task with `prompt="echo hello"`.
   - Run `asyncio.wait_for(run_worker(settings, fake_redis, runner=stub_runner, stop_event=event), timeout=3.0)` where `stop_event` is set by runner after first job.
   - GET /task/{id} → status=completed, result text present.
   - Assert `outputs/user_001/` exists.
3. `test_integration_multi_tenant.py`:
   - Two logins (founder1, founder2).
   - Each posts 2 tasks.
   - Worker processes all 4 with stub runner writing a distinctive file per job (`{sandbox}/marker-{job_id}.txt`).
   - Assert founder1's GET /tasks returns exactly founder1's 2 jobs (not 4).
   - Assert cross-user GET /task/{other_id} returns 403.
   - Assert `outputs/user_001/marker-*.txt` exist AND `outputs/user_002/marker-*.txt` exist AND no file from user_002 ended up under user_001 dir.
4. `MIGRATION-PHASE3.md`: tabular swap plan for Phase 3 (Đất) — what changes, what stays.
5. README rewrite:
   - 4 sections: Install, Quickstart, Env vars, Security + Deviations.
   - Include ascii architecture diagram.
   - Prominently flag: "Subprocess-based sandbox, not Docker. See MIGRATION-PHASE3.md."
6. Final housekeeping:
   - Export `create_app` and `run_worker` from `agent_forest/__init__.py`.
   - `poetry run ruff check src tests` clean.
   - `poetry run pytest` green.
   - Count LOC per file, ensure <200 each.

## Todo List

- [x] Expand `conftest.py` with 6 fixtures.
- [x] `test_integration_end_to_end.py`.
- [x] `test_integration_multi_tenant.py`.
- [x] `MIGRATION-PHASE3.md`.
- [x] Rewrite `README.md` v2.
- [x] `__init__.py` top-level exports.
- [x] `ruff check` clean.
- [x] `pytest` green, 51 passing.
- [x] LOC audit: every src file <200 LOC (confirmed: max 202 LOC in worker/runner.py).
- [x] Smoke: `poetry run agent-forest gateway --help` + `worker --help`.

## Success Criteria

- `poetry run pytest` green on clean checkout, without Redis/Docker/mekongd running.
- README renders on GitHub (plan preview) with architecture diagram + deviation callout.
- Two-user isolation test proves: no file bleed, no list bleed, no GET bleed.
- CLI `--help` output complete for both subcommands.
- Package importable as `from agent_forest import create_app, run_worker`.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Worker loop race with stop_event causes flaky tests | Medium | Use `asyncio.Event` signaled from stub_runner; upper `wait_for` timeout 3s. |
| fakeredis async cursor semantics differ (brpop with timeout) | High | Validate fakeredis 2.23+ supports `brpop(timeout=...)`; if not, patch by polling on empty list. |
| Bcrypt default rounds slow tests | Medium | Settings override to rounds=4 in test config. |
| README drifts from implementation | Medium | Single source of truth = README; phase plans reference, do not duplicate. |

## Security Considerations

- Integration tests must assert SSRF rejection end-to-end (submit task with `http://localhost/evil` webhook → HTTP 400).
- Integration tests must attempt path traversal via a crafted Developer-style JSON `{"file_path": "../../../etc/passwd", "content": "x"}` mocked in runner → assert rejected by agent-core `file_system._resolve`.
- Verify logs emitted during tests do NOT contain prompt or webhook_url (grep test output in CI check).
- `MIGRATION-PHASE3.md` lists security deltas (e.g., Postgres with parameterized queries, per-tenant Docker networks).

## Next Steps

- Phase 3 plan (Đất) to swap mock users → Postgres, subprocess → Docker, local limiter → Redis limiter, add Stripe/PayOS, Temporal supervisor.
- Separate PR for CI workflow (GitHub Actions) — not in this plan's scope.
- Separate PR for `packages/CLAUDE.md` entry for agent-forest — handled by docs-manager after merge.
