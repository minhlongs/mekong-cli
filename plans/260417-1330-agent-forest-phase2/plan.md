---
title: "Agent-Forest Phase 2 (Rừng) — Multi-tenant Gateway + Worker + Queue"
description: "FastAPI gateway + Redis queue + async worker pool over agent-core, per-user sandbox, JWT auth."
status: pending
priority: P2
effort: 7h
branch: master
tags: [agent-forest, phase2, multi-tenant, fastapi, redis, worker]
created: 2026-04-17
---

# Agent-Forest Phase 2 (Rừng)

Multi-tenant orchestration layer on top of `packages/agent-core/` (Phase 1 Seed).
New package at `packages/agent-forest/`. Inherits LLMClient → mekongd. No mods to agent-core.

## Strategic Deviations from DeepSeek Doc

- **NO Docker-in-Docker** for sandbox. Doc spawns `agent-{user_id}-...` containers via `docker-py`. We use subprocess + `outputs/{user_id}/` path isolation atop agent-core's existing sandbox. Rationale: keeps package pure-Python, installable via `poetry install`, testable without Docker daemon. Docker-based isolation deferred to Phase 3 (Đất) or a dedicated infra PR.
- **NO Postgres.** Mock users via bcrypt-hashed static dict loaded from `USERS_YAML` env (fallback to in-code default). Phase 3 swaps to SQLAlchemy+Postgres.
- **JWT** (HS256) instead of doc's "bearer=username" mock. Still a short-term token; Postgres-backed login in Phase 3.
- **Tests MUST run without Redis daemon** via `fakeredis`.

## Phases

| # | File | Status | LOC actual | Summary |
|---|------|--------|----------:|---------|
| 01 | [phase-01-setup-pyproject-readme.md](phase-01-setup-pyproject-readme.md) | completed | 161 | pyproject, layout, README, settings module |
| 02 | [phase-02-gateway-auth-and-models.md](phase-02-gateway-auth-and-models.md) | completed | 289 | JWT utils, users loader, pydantic models, rate limiter |
| 03 | [phase-03-gateway-task-endpoints.md](phase-03-gateway-task-endpoints.md) | completed | 312 | FastAPI app: /auth/login, /task, /task/{id}, /tasks, /auth/me, /healthz |
| 04 | [phase-04-worker-and-sandbox.md](phase-04-worker-and-sandbox.md) | completed | 284 | Redis consumer loop, per-user sandbox dispatcher, webhook notifier |
| 05 | [phase-05-integration-tests-and-docs.md](phase-05-integration-tests-and-docs.md) | completed | 290 | fakeredis-based integration tests, docs, CLI entrypoints |

**Total delivered: 1336 LOC (src 891, tests 445, config/docs 0 — inherits root pyproject/README).**

## Completion Summary

**Timestamp:** 2026-04-17 13:30–14:55 (85 min)

**Security Fixes Applied:**
- HIGH-1: SSRF webhook validation (RFC1918 + loopback + reserved IPs)
- HIGH-2: CORS wildcard removed (explicit origin list)
- MED-2: Rate limiter key hashing (SHA256 of `sub` claim)
- MED-3: User ID regex validation (`^[a-zA-Z0-9_-]{1,64}$`)

**Test Coverage:** 51 tests passing
- 34 original unit tests (config, auth, models, queue, sandbox, auth, gateway routes, worker, webhook)
- 3 SSRF webhook injection tests
- 1 user_id regex validation test
- 13 edge-case tests (P0: auth failures, rate limit boundary, cross-user 403, timeout)

**LOC by File (src/agent_forest/):**
- `__init__.py` (3 LOC) + `config.py` (61) + `models.py` (44) + `auth.py` (33) + `users.py` (48) + `queue.py` (67) + `sandbox.py` (58) + `webhook.py` (74) + `cli.py` (85) = 473 LOC
- `gateway/app.py` (142) + `gateway/routes_auth.py` (71) + `gateway/routes_task.py` (139) + `gateway/deps.py` (41) + `gateway/__init__.py` (8) = 401 LOC
- `worker/main.py` (97) + `worker/runner.py` (103) + `worker/__init__.py` (2) = 202 LOC
- **Total src: 891 LOC**; **Total tests: 445 LOC** (51 passing, 0 skipped, 0 failed)

**Deviations from Phase 2 Blueprint (Planned Deferrals → Phase 3 Đất):**
- NO Docker-in-Docker sandbox (subprocess + path isolation used instead) ✓ PLANNED
- NO Postgres (YAML-backed bcrypt users; Phase 3 adds SQLAlchemy) ✓ PLANNED
- NO async job recovery on worker restart (in-memory loss acceptable for Phase 2) ✓ PLANNED
- NO Temporal supervisor (Redis queue adequate for dogfood) ✓ PLANNED

All deviations were explicitly documented in Phase 2 blueprint. No surprise cuts.

## Key Dependencies

- Runtime: `fastapi`, `uvicorn[standard]`, `redis>=5`, `python-jose[cryptography]`, `passlib[bcrypt]`, `pydantic>=2`, `httpx`, `slowapi`, `pyyaml`, `typer`.
- Dev: `pytest`, `pytest-asyncio`, `fakeredis`, `respx`, `ruff`.
- Reuses `agent-core` as path dependency: `agent-core = { path = "../agent-core", develop = true }`.

## Success Criteria (Package-level)

1. `poetry install && poetry run pytest` green with 0 external services.
2. `poetry run agent-forest gateway` boots on `:8000`; `poetry run agent-forest worker` connects to Redis.
3. Two distinct users submit tasks → outputs land in `outputs/user_001/` vs `outputs/user_002/` — no cross-pollination.
4. Path-traversal attempt via webhook/prompt rejected.
5. Rate limit returns HTTP 429 after 60 req/min/user.
6. All files <200 LOC.
