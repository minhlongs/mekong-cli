# Phase 01 — Setup: pyproject, layout, README, settings

## Context Links

- Sibling package: `/Users/macbookprom1/mekong-cli/packages/agent-core/pyproject.toml`
- Monorepo root: `/Users/macbookprom1/mekong-cli/packages/CLAUDE.md`
- DeepSeek doc section: "CẤU TRÚC THƯ MỤC MỞ RỘNG" + "BƯỚC 2.1 + 2.2.1"
- Phase 1 (Seed) PR: #88 (commit b8a16878f)

## Overview

- Priority: P0 (gate for all later phases)
- Status: pending
- Bootstrap the `agent-forest` Python package in `packages/agent-forest/`. Lay out pyproject, package skeleton, settings module, and README. No business logic yet.

## Key Insights

- Follow `agent-core/pyproject.toml` style exactly: Poetry, `packages = [{ include = "<pkg>", from = "src" }]`, `pythonpath = ["src"]`, ruff line-length 100.
- agent-core reused as path dep (`develop = true`) — dogfood LLMClient + SeedMemory + tools.
- Settings via pydantic-settings (`BaseSettings`) is over-engineered for KISS; use `os.getenv` with typed defaults in a single `config.py`. Matches agent-core.
- fakeredis pinned in dev group so `pytest` stays hermetic.

## Requirements

### Functional

- R1: `poetry install` succeeds on Python 3.11.
- R2: `agent_forest` package importable; exposes `__version__`.
- R3: Two Typer entry points: `agent-forest gateway` and `agent-forest worker`.
- R4: `config.py` reads 8 env vars with safe defaults (documented in README).

### Non-functional

- N1: pyproject < 60 LOC.
- N2: Each src file <200 LOC.
- N3: ruff clean.

## Architecture

```
packages/agent-forest/
├── pyproject.toml
├── README.md
├── src/agent_forest/
│   ├── __init__.py           # __version__
│   ├── config.py             # env-driven settings dataclass
│   ├── cli.py                # typer: gateway / worker subcommands (stubs only Phase 1)
│   ├── gateway/              # populated in Phase 02/03
│   │   └── __init__.py
│   └── worker/               # populated in Phase 04
│       └── __init__.py
└── tests/
    ├── __init__.py
    ├── conftest.py           # shared fixtures (populated Phase 05)
    └── test_config.py        # smoke test settings
```

## Related Code Files

### Create

- `packages/agent-forest/pyproject.toml`
- `packages/agent-forest/README.md`
- `packages/agent-forest/src/agent_forest/__init__.py`
- `packages/agent-forest/src/agent_forest/config.py` (~80 LOC)
- `packages/agent-forest/src/agent_forest/cli.py` (~50 LOC stub)
- `packages/agent-forest/src/agent_forest/gateway/__init__.py` (empty)
- `packages/agent-forest/src/agent_forest/worker/__init__.py` (empty)
- `packages/agent-forest/tests/__init__.py` (empty)
- `packages/agent-forest/tests/conftest.py` (stub; extended Phase 05)
- `packages/agent-forest/tests/test_config.py` (~40 LOC)

### Modify

- None.

## Implementation Steps

1. `mkdir -p packages/agent-forest/src/agent_forest/{gateway,worker}` and `packages/agent-forest/tests/`.
2. Author `pyproject.toml`:
   - `name = "agent-forest"`, `version = "0.1.0"`, `packages = [{ include = "agent_forest", from = "src" }]`.
   - deps: `python = "^3.11"`, `fastapi = "^0.111"`, `uvicorn = {version = "^0.30", extras = ["standard"]}`, `redis = "^5.0"`, `python-jose = {version = "^3.3", extras = ["cryptography"]}`, `passlib = {version = "^1.7", extras = ["bcrypt"]}`, `pydantic = "^2.6"`, `httpx = "^0.27"`, `slowapi = "^0.1.9"`, `pyyaml = "^6.0"`, `typer = "^0.12"`, `agent-core = { path = "../agent-core", develop = true }`.
   - dev group: `pytest = "^8.1"`, `pytest-asyncio = "^0.23"`, `fakeredis = "^2.23"`, `respx = "^0.21"`, `ruff = "^0.4"`.
   - scripts: `agent-forest = "agent_forest.cli:app"`.
   - ruff + pytest ini mirroring agent-core.
3. `config.py`: single `@dataclass ForestSettings` with classmethod `from_env()`. Fields: `redis_url`, `jwt_secret_key`, `jwt_algorithm="HS256"`, `jwt_expire_minutes=10080`, `users_yaml`, `outputs_dir`, `gateway_host="0.0.0.0"`, `gateway_port=8000`, `rate_limit_per_minute=60`, `webhook_timeout_seconds=5`, `worker_poll_seconds=5`. Validate `jwt_secret_key` non-empty when `not testing`.
4. `cli.py`: Typer app with two commands (`gateway`, `worker`) whose bodies do `raise typer.Exit("not yet implemented (see Phase 03/04)")`. Wire in Phase 03/04.
5. `__init__.py`: export `__version__ = "0.1.0"`.
6. `test_config.py`: verify defaults, env override, missing-secret failure when `FOREST_TESTING` unset.
7. `README.md` ≤70 lines: install, env vars table, quickstart with two terminals (gateway + worker), mention mekongd dependency.
8. `poetry install && poetry run ruff check src tests && poetry run pytest`.

## Todo List

- [x] Create directory tree.
- [x] Write `pyproject.toml`.
- [x] Write `config.py` with dataclass + `from_env()`.
- [x] Write `cli.py` stubs.
- [x] Write `__init__.py` with `__version__`.
- [x] Write `test_config.py` (3 cases).
- [x] Write `README.md`.
- [x] Verify `poetry install` succeeds.
- [x] `poetry run ruff check` clean.
- [x] `poetry run pytest` green.

## Success Criteria

- `poetry install` exits 0.
- `poetry run agent-forest --help` lists `gateway` and `worker`.
- `poetry run pytest tests/test_config.py` — 3 passing.
- `poetry run ruff check src tests` — 0 issues.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| agent-core path dep resolution fails on CI | High | Keep `develop = true`; verify via `poetry show agent-core` after install. |
| passlib[bcrypt] binary wheel missing on M1 | Medium | bcrypt 4.x ships arm64 wheels; fall back to building. |
| slowapi incompatibility with FastAPI 0.111 | Low | Pin both; integration-test in Phase 03. |

## Security Considerations

- `jwt_secret_key` MUST come from env; `config.from_env()` raises if empty and `FOREST_TESTING` not set. Never hardcode.
- `users_yaml` path resolved before load; reject if outside project root — defer full check to Phase 02 loader.
- README must document `JWT_SECRET=REDACTED_KEY` as required and warn never to commit `.env`.

## Next Steps

- Phase 02 consumes `config.ForestSettings` for JWT + users.
- Phase 04 consumes same for Redis URL + outputs dir.
