# DevOps Lead Report — Mekong CLI
*Role: DevOps Lead | Date: 2026-03-11*

---

## Infrastructure Overview

Mekong CLI uses a Cloudflare-only infrastructure strategy — zero multi-cloud complexity,
zero egress fees, and $0 cost at current scale. All deployment targets are CF primitives.

```
┌─────────────────────────────────────────────────────────┐
│  Cloudflare Ecosystem                                   │
│                                                         │
│  Pages        → Static frontends (landing, dashboard)  │
│  Workers      → Edge API (raas-gateway, openclaw)      │
│  D1           → SQLite-compatible database              │
│  KV           → Key-value cache (sessions, credits)    │
│  R2           → Object storage (reports, artifacts)    │
│  Queues       → Async job dispatch (Tôm Hùm daemon)   │
└─────────────────────────────────────────────────────────┘
```

---

## Deployment Pipeline

### Current Flow
```
git push origin main
    │
    ▼
GitHub Actions (CI)
    │── python3 -m pytest tests/    (must pass)
    │── npm run typecheck            (TS files)
    │── wrangler deploy              (CF Workers)
    └── CF Pages auto-deploy        (on push)
```

### Known CI Issues (from git log)
- `cc-cli` workflow had import name errors — fixed in commit `41aef0504`
- Backend tests ignored in cc-cli workflow — needs revisit
- CF D1 migrations directory exists but migration execution not automated

---

## Wrangler Configuration

Key workers and their expected `wrangler.toml` bindings:

| Worker | D1 | KV | R2 | Queues |
|--------|----|----|-----|--------|
| `apps/raas-gateway` | credits_db | sessions | — | — |
| `apps/openclaw-worker` (Tôm Hùm) | — | job_cache | artifacts | mission_queue |
| `apps/algo-trader` | trades_db | — | reports | — |

**Gap:** Verify all `wrangler.toml` files have correct binding names matching
the TypeScript adapter files in `src/jobs/cloudflare-*.ts`.

---

## Monitoring Gaps (Critical)

Current monitoring: **none confirmed**. This is the highest-risk gap.

| Layer | What to Monitor | Tool | Status |
|-------|----------------|------|--------|
| CF Workers | Error rate, CPU time, request count | CF Analytics | Available free |
| CF D1 | Query latency, row count | CF Analytics | Available free |
| Application errors | Uncaught exceptions, 5xx | Sentry | Not configured |
| Uptime | HTTP 200 on production URLs | Better Uptime / UptimeRobot | Not configured |
| LLM latency | P50/P95 per provider | Custom CF Worker log | Not configured |
| Credit balance | Users at 0 MCU | D1 query + alert | Not configured |

**Immediate action:** Configure Sentry for `apps/openclaw-worker/` and
`apps/raas-gateway/`. Free tier handles ~5K errors/month.

---

## CI/CD Pipeline Health

### GitHub Actions Workflows
```
.github/workflows/
├── cc-cli.yml          — CC CLI agent tests (backend excluded currently)
├── (assumed) deploy.yml — CF Workers wrangler deploy
```

**Missing workflows:**
- `security-scan.yml` — `npm audit --audit-level=high` + `pip-audit`
- `smoke-test.yml` — post-deploy curl check on production URLs
- `migration.yml` — auto-run D1 migrations on deploy

---

## Infrastructure as Code

Current scaffold tool: `mekong/infra/scaffold.sh`

```bash
bash mekong/infra/scaffold.sh myproject startup  # CF Pages + Worker
bash mekong/infra/scaffold.sh myproject scale     # all 3 layers
```

This is the right approach — declarative scaffolding via CLI, not manual console clicks.
Ensure scaffold outputs include:
- `wrangler.toml` with all required bindings
- `.github/workflows/deploy.yml` pre-configured
- `D1` migration directory with `001_initial.sql`

---

## Secret Management

| Secret | Storage | Rotation Policy |
|--------|---------|----------------|
| `LLM_API_KEY` | GitHub Actions secrets | On provider rotation |
| `POLAR_*` webhook secret | CF Worker environment | On Polar.sh rotation |
| `CF_API_TOKEN` | GitHub Actions secrets | Annually |
| Database credentials | None (D1 = CF-managed) | N/A |

**Rule:** Never commit `.env` files. Validate with `grep -r "API_KEY\|SECRET" src/` in CI.

---

## Disaster Recovery

| Scenario | Recovery Path | RTO | RPO |
|----------|--------------|-----|-----|
| CF Worker down | CF auto-routes to edge replica | <1 min | 0 |
| D1 database corruption | CF point-in-time restore | <4 hr | <24 hr |
| Bad deploy | `wrangler rollback` to previous version | <5 min | 0 |
| GitHub repo deleted | Mirror to Gitlab (not configured) | Manual | Last push |

**Gap:** No automated backup export from D1 to R2. Add daily `D1 export → R2` job.

---

## Performance Targets

| Metric | Current | Target |
|--------|---------|--------|
| CF Worker cold start | ~5ms (V8 isolate) | <10ms |
| API p99 latency | Unknown | <200ms |
| CI pipeline duration | Unknown | <3 min |
| `mekong cook` e2e time | LLM-bound (~10-30s) | <30s |

---

## Q2 DevOps Actions

- [ ] Configure Sentry on all CF Workers
- [ ] Add `smoke-test.yml` GitHub Action post-deploy
- [ ] Add `security-scan.yml` (npm audit + pip-audit)
- [ ] Automate D1 migration execution in deploy pipeline
- [ ] Set up UptimeRobot for production URL monitoring
- [ ] Add daily D1 → R2 backup export job
- [ ] Document `wrangler rollback` runbook in `docs/deployment-guide.md`
