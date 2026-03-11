# PR Summary — Self-Dogfood Phase 2
Generated: 2026-03-11

## PR Title
`docs(engineering): self-dogfood phase 2 — 17 engineering reports + fix VERSION mismatch`

## Branch
`main` (direct, no separate branch — self-dogfood session)

---

## Changes

### VERSION fix
- `VERSION`: `3.0.0` → `5.0.0` (aligned with `pyproject.toml`)

### New Reports: `reports/self-dogfood/engineering/`

| File | Description | Data Source |
|------|-------------|-------------|
| `deploy.md` | Deployment targets: Fly.io, CF Workers, Vercel, PyPI | `fly.toml`, `docs/deployment-guide.md` |
| `security.md` | Secret scan results, P0 patches, dep audit | `grep` scan of `src/`, commit history |
| `refactor-plan.md` | Top 10 files >200 lines + split strategies | `find src -exec wc -l` |
| `self-test-debug.md` | Test coverage gaps, 86→100 path | `pytest --co`, coverage output |
| `fix-report.md` | Test run results, known issues | `pytest tests/unit -q` — 112 passed |
| `kanban.md` | v5.1 task board: recipe runner, plugins, white-label, marketplace | roadmap + CLAUDE.md |
| `schema.md` | RaaS DB schema: tenants, credits, missions, invoices, webhooks | `src/api/raas_task_models.py`, DB migrations |
| `docs-status.md` | 145 docs audited: current/stale/missing | `ls docs/`, `stat` dates |
| `readme-audit.md` | Claims vs reality: 289 cmds, 245 skills, 176 contracts | `ls .claude/commands/`, `ls .claude/skills/` |
| `api-docs.md` | All 7 RaaS API endpoints with request/response examples | `src/api/raas_router.py`, `billing_endpoints.py` |
| `arch-docs.md` | 6 ADRs: PEV, DAG, LLM router, SQLite, 5-layer, Polar.sh | Architecture analysis |
| `onboard-guide.md` | Clone → setup → test → first change → PR | `Makefile`, `pyproject.toml`, src structure |
| `perf-report.md` | 408 files, 108K LOC, 1.13s import, 3637 tests in 4.3s | `wc`, `python3 -c "import time..."` |
| `code-review.md` | Last 20 commits assessed for quality | `git log --oneline -20` |
| `api-spec.md` | Full OpenAPI 3.1 YAML for `/v1/*` endpoints | `src/api/raas_router.py`, Pydantic models |
| `adr.md` | 10 ADRs for v5.0 key decisions | Architecture analysis |
| `pr-summary.md` | This file | — |

---

## Test Status

```
Unit tests: 112/112 passed (3.14s)
Full collection: 3637 tests collected
Lint: 0 errors (from prior session)
Type check: 0 errors (from prior session)
```

---

## Key Findings

1. **VERSION mismatch fixed** — `3.0.0` → `5.0.0`
2. **README stats wrong** — "289 commands, 245 skills, 176 contracts" vs actual 273/542/9
3. **PAYPAL_TESTING_GUIDE.md** in docs/ — PayPal removed from code but guide remains
4. **`codebase-summary.md`** still shows v3.0.0 and "62+ tests" — needs update
5. **`usage_metering_service.py`** (754 lines) has 0% test coverage — highest risk gap
6. **`deployment-guide.md`** references Stripe env vars — should be Polar.sh only
7. **4 algotrader commits** in mekong-cli repo — potential scope separation needed
8. **`pytest-timeout`** not installed — `--timeout` flag fails
9. **`psutil`** not in deps — system metrics silently unavailable

---

## Docs Impact: major

`docs/codebase-summary.md` and `docs/project-roadmap.md` need version bump updates.
`docs/PAYPAL_TESTING_GUIDE.md` should be archived or deleted.
`docs/deployment-guide.md` Stripe references need replacing with Polar.sh.
