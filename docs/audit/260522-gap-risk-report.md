# Gap & Risk Report — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6 | **Confidence:** Varies (noted per item)

Legend: **[C]** = Confirmed fact | **[I]** = Inferred behavior | **[?]** = Open question

---

## 1. Missing Information

| # | Gap | Severity | Status |
|---|-----|----------|--------|
| G1 | No load balancer / scaling config for api.cashclaw.cc | HIGH | [?] May exist outside repo |
| G2 | PostgreSQL hosting details — no connection string pattern, no migration runner | HIGH | [?] Possibly Supabase |
| G3 | No disaster recovery plan for ~/.mekong/ JSONL files | HIGH | [C] No backup mechanism found |
| G4 | No API rate limiting configuration | MEDIUM | [I] Not found in gateway.py middleware |
| G5 | No monitoring/alerting setup documented | MEDIUM | [I] Sentry SDK present but dashboard config unknown |
| G6 | 28+ scaffold apps — no documentation on which are active vs abandoned | MEDIUM | [C] Package.json exists but minimal code |
| G7 | No runbook for daemon (src/daemon/) operations | MEDIUM | [?] May exist in gitignored plans/ |
| G8 | LLM provider cost tracking — no budget alerts or spend monitoring | MEDIUM | [I] Not found in code |
| G9 | No documented SLA or uptime targets | LOW | [?] |
| G10 | No changelog or migration guide for v5→v6 upgrade | LOW | [C] Not found in docs/ |

---

## 2. Unclear Flows

### 2.1 PEV Orchestrator Recursion Depth — [?]

The orchestrator (`src/core/orchestrator/`, 1,243 LOC) manages Plan→Execute→Verify loops. A planner can decompose a task into subtasks, each of which could trigger its own PEV loop. No explicit `max_depth` or recursion guard found.

**Impact:** Potentially unbounded resource consumption.
**Recommendation:** Verify max_depth in orchestrator code. If absent, add one.

### 2.2 Factory Contract Sync — [?]

567 JSON contracts in `factory/contracts/` should mirror 342+ commands in `.claude/commands/`. The sync mechanism is unclear:
- Are contracts auto-generated? (No generation script found)
- Are they manually maintained? (567 > 342 suggests extras or drift)
- Does CI validate consistency? (`factory-validate.yml` exists but scope unclear)

**Impact:** Stale contracts could mis-route commands via PEV classifier.
**Recommendation:** Run `factory-validate.yml` locally and check what it validates.

### 2.3 Daemon Production Status — [?]

`src/daemon/` is a complete system (5,254 LOC) with worker pool, circuit breaker, DLQ, and heartbeat. But it's unclear if it runs in production:
- LaunchDaemon plist mentioned in CLAUDE.md
- But `com.mekong.daemon.plist` not found in repo
- README says "OpenClaw daemon — not live yet"

**Impact:** If not running, 5K+ LOC is dead code. If running, it needs monitoring.
**Recommendation:** Check `/Library/LaunchDaemons/com.mekong.daemon.plist` on production machine.

### 2.4 cleo-new Embedding — [I]

`packages/cleo-new/` is a full agent framework (v2026.5.87) with 30+ internal packages nested inside the monorepo. It's unclear if this is:
- Intentionally embedded (mono-monorepo pattern)
- A temporary arrangement pending extraction
- A fork that should track upstream

**Impact:** Build complexity, potential version conflicts.

---

## 3. Blocking Unknowns

| # | Unknown | Blocks | Priority |
|---|---------|--------|----------|
| B1 | PostgreSQL connection details | Database migration, schema audit | HIGH |
| B2 | Production server topology (single instance? container? VM?) | Scaling assessment, DR planning | HIGH |
| B3 | Which apps are deployed to Cloudflare Pages | Frontend audit, cleanup decisions | MEDIUM |
| B4 | npm publish status of 58 packages | Package cleanup, versioning strategy | MEDIUM |
| B5 | Actual CI/CD pass rate (do all 15 workflows pass?) | Quality baseline | MEDIUM |

---

## 4. Risky Dependencies

### 4.1 External Service Dependencies — [C]

| Dependency | Risk | Mitigation |
|------------|------|------------|
| **Polar.sh** (billing) | Vendor lock-in, API changes | Webhook-based; migration to another provider = significant work |
| **Sepay** (VN banking) | Single VN banking provider; no fallback | VietQR is standard; could swap provider |
| **OpenRouter** (LLM aggregator) | Primary LLM path; outage = degraded AI | 9 fallback providers in chain |
| **Cloudflare** (infra) | Full stack on one vendor: Pages + Workers + D1 + KV + R2 | CF has strong SLA; but migration = full rewrite |
| **Sentry** (error tracking) | Low risk; standard tool | Easy to swap |
| **GitHub Actions** (CI/CD) | Moderate lock-in with 15 workflows | Standard YAML; portable to GitLab CI |

### 4.2 Internal Dependency Risks — [C]

| Dependency | Risk | Impact |
|------------|------|--------|
| `src/core/llm_client.py` (23K LOC) | Largest single module; complex provider chain | Bug here affects all AI features |
| `src/raas/` (20K LOC) | Billing engine size; hard to refactor | Revenue impact if broken |
| `factory/contracts/` (567 files) | Manual sync with commands | Silent routing errors |
| `~/.mekong/*.jsonl` (file-based state) | No ACID, no backup | Pilot data loss |

### 4.3 Python Dependency Risks — [C]

From `pyproject.toml`:
- `python-jose[cryptography]` — JWT library, known CVE history
- `stripe` — Still present despite Polar-only policy (needed for RaaS?)
- `anthropic` — SDK version pins may lag behind API changes
- `asyncpg` — PostgreSQL driver; needs matching server version

---

## 5. Infrastructure Assumptions

| # | Assumption | Verified? | Risk if Wrong |
|---|------------|-----------|---------------|
| A1 | api.cashclaw.cc runs on a single server | [I] No scaling config found | Single point of failure |
| A2 | PostgreSQL is accessible from gateway server | [I] asyncpg in deps | Connection failures = full outage |
| A3 | ~/.mekong/ directory exists on production machine | [I] Code reads/writes without fallback | First-run crash |
| A4 | Ollama available at localhost:11434 for local inference | [I] Fallback provider | Graceful degradation (falls to OfflineProvider) |
| A5 | LaunchDaemons configured on macOS production | [I] Referenced in CLAUDE.md | Services don't auto-start |
| A6 | CF Workers have D1 database bound | [I] Wrangler config | Edge API fails without binding |

---

## 6. Secrets / Config Concerns

### 6.1 Sensitive Files — [C]

| File | Content | Protection |
|------|---------|------------|
| `~/.mekong/admin-token.txt` | Admin API token | mode 600 (file permission only) |
| `.env` | 133+ env vars including API keys | .gitignore (never committed) |
| `~/.mekong/pilots.jsonl` | Pilot PII (name, phone, city) | No encryption |
| `~/.mekong/pilot_credits.json` | Credit balances | No encryption, no integrity check |

### 6.2 Concerns

1. **Pilot PII in plaintext JSONL** — Names, Zalo numbers, cities stored unencrypted. If machine is compromised, PII is exposed. [C]
2. **Admin token as plaintext file** — Single token controls pilot conversion endpoint. No rotation mechanism beyond manual replacement. [C]
3. **No secret rotation policy** — API keys in .env have no documented rotation schedule. [C]
4. **HMAC secret for VietQR** — Stored in LaunchDaemon plist (root-readable). Compromise = fake payment webhooks. [I]
5. **JWT secret in env var** — Standard practice but no documented rotation procedure. [C]

---

## 7. Testing Weaknesses

### 7.1 Coverage Exclusions — [C]

The following critical paths are EXCLUDED from coverage reporting:

| Excluded Path | Importance | Risk |
|---------------|------------|------|
| `src/raas/` | Billing engine (20K LOC) | Revenue-critical code untested |
| `src/core/llm_client.py` | LLM provider chain | AI feature regressions |
| `src/commands/` | CLI implementations | User-facing command failures |
| `src/cli/` | CLI app wiring | Command routing bugs |
| `src/config.py` | Configuration | Startup failures |
| `src/main.py` | Entry point | Bootstrap failures |

### 7.2 Test Infrastructure Gaps — [I]

- No E2E tests for API gateway endpoints (Playwright/httpx)
- No integration tests for LLM provider chain (would need mock servers)
- No load testing for gateway (no k6/locust config found)
- No contract tests between Python backend and TypeScript SDK
- VN pilot tests exist (100+) but unclear if they test against real file state

### 7.3 TypeScript Test Coverage — [I]

5,843 vitest tests across packages. But:
- No coverage threshold enforced in turbo.json
- Many packages have zero tests (scaffold packages)
- No cross-package integration tests

---

## 8. Operational Risks

### 8.1 CRITICAL

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| JSONL file corruption loses pilot data | Medium | HIGH — no backup, no recovery | Implement daily backup to cloud storage |
| Gateway single instance failure | Low-Medium | HIGH — all API down | Add health check + auto-restart, consider redundancy |
| LLM provider cost spike | Medium | HIGH — unexpected bills | Add spend monitoring and budget alerts |

### 8.2 HIGH

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stale factory contracts mis-route commands | Medium | MEDIUM — wrong MCU charged | Automate contract generation from commands |
| Coverage gaps hide billing bugs | Medium | HIGH — revenue loss | Add RaaS and billing to coverage requirements |
| Admin token compromise | Low | HIGH — full pilot access | Implement token rotation, add IP allowlist |

### 8.3 MEDIUM

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| 16GB monorepo slows CI/CD | High | LOW — developer friction | Prune scaffold apps/packages |
| Dual AI config (.claude/ + .agent/) drifts | Medium | LOW — inconsistent behavior | Document which is source of truth |
| Stale docs mislead developers | High | MEDIUM — wrong assumptions | This audit; schedule quarterly review |
| pnpm workspace includes 28+ unused apps | High | LOW — build time waste | Move scaffolds to separate repo or archive |

---

## 9. Recommended Priority Actions

### Immediate (Week 1)

1. **Implement ~/.mekong/ backup** — Daily cron to copy JSONL files to cloud storage
2. **Add rate limiting to gateway** — Prevent abuse of public endpoints
3. **Verify daemon production status** — Is it running? Should it be?

### Short-term (Month 1)

4. **Expand test coverage** — Remove at minimum `src/raas/` and `src/core/llm_client.py` from exclusion list
5. **Automate factory contract validation** — CI check that contracts match commands
6. **Encrypt pilot PII** — At minimum, encrypt JSONL files at rest
7. **Document PostgreSQL setup** — Connection details, backup schedule, migration process

### Medium-term (Quarter 1)

8. **Prune scaffold apps/packages** — Archive or delete 28+ unused apps, 20+ scaffold packages
9. **Extract RaaS engine** — 20K LOC billing engine should be its own service
10. **Add E2E tests for gateway** — Cover all 13+ router endpoints
11. **Implement monitoring dashboard** — Sentry + Prometheus + uptime checks

---

## Unresolved Questions

1. What is the actual PostgreSQL hosting setup? (Supabase? Self-hosted? CF D1 proxy?)
2. Is the daemon running in production? If so, what's its resource consumption?
3. What's the monthly LLM provider spend? Any budget alerts?
4. How many pilot users are active? What's the JSONL file size?
5. Are there any SLAs promised to pilot users?
6. Which 15 CI/CD workflows currently pass on main?
7. Is `cleo-new` tracking an upstream repo or is this the source of truth?
8. What's the actual npm publish status of the 58 packages?
