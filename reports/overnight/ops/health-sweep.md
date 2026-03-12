# Health Sweep — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** health, ops-health-sweep, sre-morning-check, status, smoke

---

## System Overview

| Component | Status | Notes |
|-----------|--------|-------|
| Python version | 3.9.6 (system) / 3.12 (CI) | mismatch — local dev older |
| Node.js | present | required for frontend/landing + mekong-engine |
| pnpm | required | monorepo package manager |
| Version | 5.0.0 | per `VERSION` and `pyproject.toml` |
| Primary CLI entry | `mekong` | Typer-based, `src/main.py` |
| DB | SQLite (`/data/tenants.db`) | fly.toml mount, local migrations in `src/db/migrations/` |

---

## Build / Compile Check

### Python Backend
- `ruff check src/ tests/` — configured in CI (`.github/workflows/ci.yml`)
- `ruff format --check` — format enforcement via CI (`continue-on-error: true`)
- No compile errors in core modules confirmed by import scan
- `pyproject.toml` → `name = mekong-cli`, `version = 5.0.0`, Python 3.12 in CI

### Frontend (Landing)
- `cd frontend/landing && npm run build` — triggered in CI `frontend` job
- Uses Node 22 in CI pipeline

### Mekong Engine (TypeScript / Cloudflare Workers)
- `packages/mekong-engine` — TypeScript, vitest tests, wrangler deploy
- `npx tsc --noEmit` in CI (`continue-on-error: true`)

---

## Test Suite Status

**CI config (`.github/workflows/ci.yml`):**
```
pytest tests/ --ignore=tests/backend --ignore=tests/e2e \
  --ignore=tests/integration --ignore=tests/unit \
  --ignore=tests/benchmarks --cov=src --cov-fail-under=80
```
- `continue-on-error: true` on pytest step → CI won't fail on test failure
- 3,638 tests collected total (full suite)
- **Health-specific tests (run locally):** `test_health_monitoring.py` + `test_subsystem_health.py`
  → **95 passed, 7 warnings in 14.45s**

### Key Test Areas
| Test File | Scope |
|-----------|-------|
| `test_health_monitoring.py` | subsystem health checks |
| `test_subsystem_health.py` | component status |
| `test_gateway_api.py` | API gateway health |
| `test_executor.py` | PEV executor pipeline |
| `test_planner.py` | task decomposition |
| `test_orchestrator_integration.py` | full orchestration loop |

---

## File Structure Integrity

```
src/
├── core/          # planner, executor, verifier, orchestrator, llm_client
├── agents/        # LeadHunter, ContentWriter, GitAgent, FileAgent, ShellAgent
├── api/           # FastAPI routes
├── security/      # command_sanitizer, attestation_generator
├── telemetry/     # rate_limit_metrics
├── db/            # migrations (8 total), schema, queries
├── config.py      # env var loader via dotenv
└── main.py        # Typer CLI entry point

tests/             # 100+ test files, 3638 tests collected
mekong/            # infra templates, daemon, adapters
.github/workflows/ # 24 workflow files
```

**Migrations count:** 8 files (`001_` → `008_billing_system.sql`) — sequential, no gaps

---

## Health Check Script (`scripts/health-check.sh`)

Checks the following (run with `make health`):
1. Python 3.9+
2. Node.js 18+
3. pnpm
4. Git
5. `.env` file existence
6. CC CLI (`claude`) installed
7. `mekong` command available
8. pytest installed
9. `~/.claude/settings.json` configured

---

## SRE Morning Checklist

- [ ] `make health` — local env ready
- [ ] `gh run list -L 5` — latest CI runs status
- [ ] `python3 -m pytest tests/test_health_monitoring.py -q` — subsystem health
- [ ] Check `logs/api.error.log` for overnight errors
- [ ] Check `logs/audit/` for anomalies
- [ ] Verify Fly.io app status: `fly status -a agencyos-gateway`
- [ ] Verify CF Workers deployment: `wrangler deployments list`

---

## Smoke Test Targets

| Endpoint | Expected | Source |
|----------|----------|--------|
| `GET /health` | HTTP 200 | Dockerfile HEALTHCHECK |
| `GET /v1/missions` | HTTP 200/401 | API gateway |
| `mekong --help` | exit 0 | CI `Verify CLI Entry Point` |
| `mekong version` | prints v5.0.0 | VERSION file |

---

## Issues Identified

1. **Local Python 3.9.6 vs CI Python 3.12** — potential version-specific behavior differences; recommend upgrading local to 3.12
2. **`continue-on-error: true` on pytest** — CI won't fail on test regression; masking failures
3. **E2E tests disabled** — `e2e-tests.yml` disabled pending webServer infrastructure (`workflow_dispatch` only)
4. **Coverage threshold 80%** — but `continue-on-error: true` means it won't block merge
5. **`pytest-timeout` not installed** — per MEMORY.md, `--timeout` flag not available locally

---

## Verdict

**Overall Health: AMBER**
- Core test suite (health/subsystem): 95/95 passing
- Full suite: not verified locally (3638 tests, ~2.5min)
- CI pipeline: runs but soft-failures on test/lint steps
- E2E: disabled
