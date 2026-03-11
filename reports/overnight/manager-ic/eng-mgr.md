# Engineering Manager Report — Mekong CLI
*Role: Engineering Manager | Date: 2026-03-11*

---

## Team Overview

Current engineering capacity: 1 founder/CTO + AI agent workforce (17+ agent types).
The OpenClaw constitution explicitly delegates execution to CC CLI subagents — humans
own architecture decisions, approval gates, and novel problem-solving only.

Engineering velocity is measured in MCU consumed + successful deliveries, not story points.

---

## Codebase Health Snapshot

| Metric | Status | Target |
|--------|--------|--------|
| Test count | 62 tests | >100 |
| Test runtime | ~2.5 min | <2 min |
| File size compliance (<200 lines) | Partial | 100% |
| Type hints coverage | Partial | 100% |
| `any` type usage | Unknown | 0 |
| TODO/FIXME count | Unknown | 0 |
| Console.log leakage | N/A (Python) | 0 print() in prod |

**Action:** Run `grep -r "TODO\|FIXME\|print(" src/ | wc -l` to baseline tech debt.

---

## Module Ownership Map

| Module | Owner | Status |
|--------|-------|--------|
| `src/core/planner.py` | CTO | Stable |
| `src/core/executor.py` | CTO | Stable |
| `src/core/verifier.py` | CTO | Stable |
| `src/core/orchestrator.py` | CTO | Stable |
| `src/core/llm_client.py` | CTO | Active (provider routing) |
| `src/agents/` | CTO + OSS contributors | Growing |
| `src/raas/` | CTO | Active (billing) |
| `apps/openclaw-worker/` | CTO | Active (Tôm Hùm daemon) |
| `apps/raas-gateway/` | CTO | Stable (CF Worker auth) |
| `.agencyos/commands/` | CTO + agents | 289 commands, needs audit |
| `factory/contracts/` | Agents | 176 contracts |

---

## Sprint Planning Framework

**Sprint length:** 2 weeks
**Ceremony overhead:** Minimal (async, no daily standups — use `mekong status` instead)

### Current Sprint Priorities (inferred from git log)
1. Cloudflare migration (D1 + KV + Queues + R2) — in progress
2. AI core engine (Anthropic SDK injection) — recently merged
3. OCOP agricultural export commands — recently merged
4. Sophia proposal migration to CF Pages — recently merged

### Next Sprint Candidates
- Fix `file_stats` test slowness (scans entire repo → mock or scope)
- Add `mekong init --wizard` for LLM env var setup reduction
- Instrument activation funnel (first cook event → PostHog)
- Type hint audit across `src/core/`

---

## Tech Debt Tracking

### Known Issues
1. `test_file_stats` scans entire repo → 2.5min test suite (should be <30s)
2. `python` binary not available on macOS → all scripts must use `python3`
3. CF D1 migrations directory exists (`src/db/migrations/`) but migration tooling unclear
4. Untracked Cloudflare adapter files (`src/jobs/cloudflare-*.ts`) need integration

### Tech Debt Priority Matrix
| Item | Impact | Effort | Priority |
|------|--------|--------|----------|
| Test suite speed | High | Low | P0 |
| Type hints 100% | Medium | Medium | P1 |
| Command audit (289 commands) | High | High | P1 |
| File size compliance | Low | Medium | P2 |
| Print statement cleanup | Medium | Low | P1 |

---

## Engineering Processes

### Pre-commit (enforced)
- Linting check
- Type check (`npx tsc --noEmit` for TS, mypy for Python)

### Pre-push (enforced)
- `python3 -m pytest tests/` must pass — no exceptions
- No secrets in diff (`API_KEY`, `SECRET`, `.env` patterns)

### Commit convention
```
feat: add new command
fix: resolve billing edge case
refactor: simplify PEV orchestrator
test: add executor rollback tests
chore: update deps
```

### Branch strategy
- `main` = always deployable
- Feature branches via git worktrees for parallel agent sessions
- No force-push to main

---

## Dependency Health

| Dependency | Type | Risk |
|------------|------|------|
| Typer | Python CLI | Low (MIT, stable) |
| Rich | Terminal UI | Low (MIT, stable) |
| FastAPI | API server | Low (MIT, stable) |
| pytest | Testing | Low |
| Cloudflare Workers SDK | Infra | Medium (CF vendor lock) |
| Polar.sh SDK | Payments | Medium (single payment provider) |
| Anthropic SDK | AI core | Medium (version sensitivity) |

Run `pip-audit` and `npm audit` quarterly.

---

## Hiring Trigger

First engineering hire justified when:
- MRR > $10K AND
- CTO is spending >30% time on support/bug fixes (not architecture)

First hire profile: Python + TypeScript full-stack, Cloudflare Workers experience preferred.

---

## Q2 Engineering OKRs

**Objective:** Harden core engine for first 1,000 users
- KR1: Test suite < 60 seconds (currently ~2.5 min)
- KR2: 100% type hint coverage in `src/core/`
- KR3: Zero P0 bugs open at sprint end
- KR4: `mekong init --wizard` reduces setup time from 10 min → 2 min
