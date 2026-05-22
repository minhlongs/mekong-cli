# Go-Live 100/100 Scorecard — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6
**Method:** Code-verified via grep, file reads, and execution path tracing. No assumptions.

---

## GO-LIVE SCORECARD

| Category | Score | Grade | Rationale |
|----------|-------|-------|-----------|
| **Architecture** | 72/100 | B- | PEV engine is well-designed (retry, timeout, circuit breaker). But 16GB monorepo with 28+ scaffold apps, dual AI config, and embedded cleo-new creates complexity. RaaS (20K LOC) should be its own service. |
| **Reliability** | 78/100 | B+ | Retry with exponential backoff ✅, circuit breakers ✅, idempotency (billing, webhooks, payments) ✅, timeouts (global+per-step) ✅. Rollback is command-based/best-effort, not transactional. |
| **Scalability** | 35/100 | F | **CRITICAL BLOCKER.** MCUBilling is an in-memory singleton. Task queue is in-memory. No Redis. No distributed cache. Global singletons prevent horizontal scaling. ThreadPool DAG capped at 4 workers. |
| **Security** | 68/100 | C+ | Parameterized SQL ✅, Pydantic validation ✅, no hardcoded secrets ✅, 4-layer CI scanning ✅. BUT: rate limiting is in-memory only (bypass on multi-instance), CORS allows `*` methods/headers, Swagger UI public, license gate conditional on env var. |
| **Observability** | 71/100 | B- | Structured JSON logging ✅, OTel metrics (5 instruments) ✅, OTel tracing ✅, multi-channel alerting (Telegram, Jidoka, billing) ✅. BUT: no Prometheus `/metrics` endpoint, no Grafana dashboard, no external log aggregation configured, health check missing DB/LLM probes. |
| **Documentation** | 55/100 | D+ | README and CLAUDE.md are excellent. But system-architecture.md stale (36 days), no QUICKSTART, no CONTRIBUTING, no TROUBLESHOOTING, no RUNBOOKS, no INCIDENT_RESPONSE. Audit backfill (this session) raises this from ~30 to 55. |
| **Testing** | 52/100 | D | 6,160 pytest + 5,843 vitest tests exist ✅. BUT: coverage excludes billing (20K LOC), LLM client (23K LOC), CLI commands, config. No E2E tests. No load tests. No contract tests between Python↔TypeScript. Coverage threshold only 40%. |
| **Deployment** | 65/100 | C | 15 CI/CD workflows ✅, CF Pages + Workers deploy ✅, 3-layer infra scaffold ✅, LaunchDaemon for gateway ✅. BUT: no load balancer, single gateway instance, no blue/green deploy, no rollback automation, no canary releases. |
| **DevEx** | 74/100 | B | One-command setup (setup-dev.sh) ✅, Docker Compose ✅, Makefile (40+ targets) ✅, pip+pnpm caching in CI ✅. BUT: no VSCode debug config, no Turbo remote cache, 16GB monorepo slow to clone, 28+ scaffold apps pollute workspace. |
| **Maintainability** | 58/100 | D+ | PEV engine well-structured. Retry/circuit-breaker reusable. BUT: oversized files (planner 667 LOC, executor 445), duplicated auth (4 locations), duplicated billing (3 locations), duplicated command definitions (3 formats), 567 factory contracts with unclear sync mechanism. |

### **OVERALL: 628/1000 = 62.8/100**

**Verdict: NOT PRODUCTION READY for 1M users. Suitable for single-instance pilot (current VN Hub use case).**

---

## BLOCKERS — Must Fix Before Go-Live

### B1: In-Memory Billing Singleton (Scalability)
**Location:** `src/gateway.py:54-56`, `src/core/mcu_billing.py:112-123`
**Problem:** MCUBilling uses `dict` storage. Each gateway instance has its own billing state. Inconsistent balances across instances. Data lost on restart.
**Impact:** Revenue loss, double-charging, or free usage.
**Fix:** Migrate MCUBilling to PostgreSQL (connection pool already exists at `src/db/database.py:56-62`).
**Effort:** Medium (2-3 days).

### B2: In-Memory Task Queue (Scalability)
**Location:** `src/core/task_queue.py:67-71`
**Problem:** PriorityTaskQueue uses in-memory heap. Tasks lost on restart. Cannot share across instances.
**Impact:** Lost work, silent task drops.
**Fix:** Implement Redis-backed queue or adopt Temporal server.
**Effort:** Medium-High (3-5 days).

### B3: In-Memory Rate Limiting (Security)
**Location:** `core/security/auth_middleware.py:36-40`
**Problem:** Rate limiter uses in-memory dict. State lost on restart. Attackers bypass by distributing across instances.
**Impact:** API abuse, DDoS vulnerability.
**Fix:** Swap to Redis-backed rate limiter (e.g., `slowapi` with Redis backend).
**Effort:** Low (1 day).

### B4: No Backup for Pilot Data (Reliability)
**Location:** `~/.mekong/*.jsonl`
**Problem:** All pilot user data (PII, credits, usage events) stored in append-only JSONL files. No backup mechanism. No encryption at rest.
**Impact:** Complete data loss on disk failure. GDPR/PDPA risk for PII.
**Fix:** Daily backup to cloud storage (S3/R2). Encrypt JSONL files at rest.
**Effort:** Low-Medium (1-2 days).

### B5: Coverage Excludes Revenue-Critical Code (Testing)
**Location:** `pyproject.toml` `[tool.coverage.run]` `omit` section
**Problem:** `src/raas/` (20K LOC billing engine), `src/core/llm_client.py` (23K LOC), `src/commands/`, `src/cli/` all excluded from coverage. Threshold is only 40%.
**Impact:** Billing bugs, LLM regressions, CLI breakage go undetected.
**Fix:** Remove `src/raas/` and `src/core/llm_client.py` from exclusion list. Raise threshold to 60%.
**Effort:** Medium (3-5 days to add missing tests).

---

## HIGH PRIORITY FIXES — Instability at Scale

### H1: CORS Allows Wildcard Methods/Headers
**Location:** `src/gateway.py:106-107`
**Problem:** `allow_methods=["*"]`, `allow_headers=["*"]`
**Fix:** Explicitly list: `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` and `["Authorization", "Content-Type"]`
**Effort:** Trivial (5 min).

### H2: Swagger UI Publicly Accessible
**Location:** `src/gateway.py` (FastAPI default)
**Problem:** `/api-docs` exposes all API endpoints, models, and schemas to unauthenticated users.
**Fix:** Disable in production: `app = FastAPI(docs_url=None, redoc_url=None)` or gate behind auth.
**Effort:** Trivial (5 min).

### H3: License Gate Conditional on Env Var
**Location:** `src/api/gateway_mission_routes.py:53`
**Problem:** `LICENSE_GATE_ENFORCE=1` must be set for billing enforcement. If unset, missions run without billing check.
**Fix:** Default to enforced. Require explicit `LICENSE_GATE_ENFORCE=0` to disable (fail-closed).
**Effort:** Trivial (10 min).

### H4: No Database Connectivity Health Check
**Location:** `src/gateway.py:128-160`
**Problem:** `/health` checks billing, auth, Sentry, OTel — but not PostgreSQL connectivity.
**Fix:** Add `check_database()` component that runs `SELECT 1` against asyncpg pool.
**Effort:** Low (30 min).

### H5: No Prometheus /metrics Endpoint
**Location:** Missing from `src/gateway.py`
**Problem:** OTel metrics are instrumented (5 meters) but no scrape endpoint exists.
**Fix:** Add `prometheus_fastapi_instrumentator` or manual `/metrics` endpoint.
**Effort:** Low (1 hour).

### H6: Bare Except in Gateway
**Location:** `src/gateway.py:124`
**Problem:** `except Exception:` (bare, no variable) catches and silently ignores all errors.
**Fix:** Catch specific exceptions or at minimum log the exception.
**Effort:** Trivial (5 min).

### H7: Circuit Breaker Only on LLM
**Location:** `src/daemon/circuit_breaker.py`, `src/core/llm_client.py`
**Problem:** Circuit breaker pattern only applied to LLM provider calls. External HTTP APIs (Polar, Sepay, Telegram) have no circuit breaker.
**Fix:** Wrap external API calls with circuit breaker. Reuse existing `CircuitBreaker` class.
**Effort:** Medium (1-2 days).

---

## MEDIUM PRIORITY FIXES — Operational Improvement

### M1: Prune 28+ Scaffold Apps
**Problem:** `apps/` contains 28+ scaffolds consuming build resources.
**Fix:** Archive to separate repo or delete.

### M2: Add VSCode Debug Configuration
**Problem:** No `.vscode/launch.json` for local debugging.
**Fix:** Add FastAPI + pytest debug configs.

### M3: Enable Turbo Remote Cache in CI
**Problem:** Turbo caching is local-only. CI rebuilds from scratch each time.
**Fix:** Add `vercel/turbo-action` to CI workflows.

### M4: Add E2E Tests for Gateway Endpoints
**Problem:** No end-to-end tests for the 13+ router endpoints.
**Fix:** Add httpx-based E2E test suite.

### M5: Automate Factory Contract Validation
**Problem:** 567 JSON contracts may drift from 342+ commands.
**Fix:** CI job that verifies 1:1 mapping between commands and contracts.

### M6: Encrypt Pilot PII at Rest
**Problem:** Names, phone numbers, cities in plaintext JSONL.
**Fix:** Encrypt JSONL files using age/sops or application-level encryption.

### M7: Document Secret Rotation Procedures
**Problem:** No documented rotation for admin token, JWT secret, webhook secrets.
**Fix:** Create runbook with rotation commands and timeline.

### M8: Add Load Testing
**Problem:** No k6/locust/artillery configuration.
**Fix:** Create load test targeting `/v1/missions` and `/v1/pilot/signup`.

---

## LOW PRIORITY FIXES — Polish

### L1: Extract RaaS Engine to Separate Service
**Problem:** 20K LOC billing engine embedded in monorepo.

### L2: Consolidate Auth Implementations
**Problem:** Auth logic in 4 locations (src/auth, middleware, vibe-auth, vibe-supabase).

### L3: Unify Command Definition Format
**Problem:** Commands defined in 3 formats (.md, .json, .py) with manual sync.

### L4: Update Stale Documentation
**Problem:** system-architecture.md is 36 days old.

### L5: Prune Scaffold Packages
**Problem:** 20+ vibe-* packages at version 0.0.1 with no consumers.

### L6: Add ThreadPool DAG Async Support
**Problem:** DAG scheduler capped at 4 threads.

---

## SUBSYSTEM DEEP-DIVE SUMMARIES

### PEV Engine (src/core/)
| Aspect | Status | Detail |
|--------|--------|--------|
| Purpose | Core orchestration loop | Plan→Execute→Verify |
| Entry Points | orchestrator.py, planner.py | CLI + API invoke |
| Failure Modes | LLM unavailable, step timeout, verification fail | All handled |
| Recovery | Retry (3x, exponential backoff), rule-based fallback, rollback (command-based) | Good |
| Scaling | Single-process, ThreadPool DAG (4 workers) | Bottleneck |
| Security | CommandSanitizer on rollback commands | Good |
| Confidence | HIGH |

### API Gateway (src/gateway.py)
| Aspect | Status | Detail |
|--------|--------|--------|
| Purpose | HTTP API server | FastAPI v3.3.0 |
| Entry Points | 13+ router prefixes, /healthz, /health | Comprehensive |
| Failure Modes | All LLM down, DB unreachable, billing singleton lost | Mixed |
| Recovery | OfflineProvider fallback, health check | Partial |
| Scaling | **Single instance only** due to in-memory singletons | BLOCKER |
| Security | CORS permissive, rate limit in-memory, Swagger public | Weak |
| Confidence | HIGH |

### Billing Engine (src/raas/)
| Aspect | Status | Detail |
|--------|--------|--------|
| Purpose | MCU credit system + RaaS marketplace | 20K LOC |
| Entry Points | webhook routes, checkout routes, billing routes | Comprehensive |
| Failure Modes | Idempotency collision, webhook replay, credit underflow | Mostly handled |
| Recovery | Idempotency keys, DLQ for webhooks, audit trail | Good |
| Scaling | SQLite for persistence (no concurrent write safety) | Concern |
| Security | HMAC webhook verification, parameterized SQL | Good |
| Confidence | HIGH |

### Daemon (src/daemon/)
| Aspect | Status | Detail |
|--------|--------|--------|
| Purpose | Autonomous task dispatch ("Tôm Hùm") | 5,254 LOC |
| Entry Points | __main__.py → heartbeat_scheduler | Single |
| Failure Modes | Worker crash, DLQ overflow, circuit breaker stuck open | Handled |
| Recovery | Jidoka stop-the-line, DLQ retry, heartbeat restart | Good |
| Scaling | Single-process worker pool | Not scalable |
| Security | No external API surface | Low risk |
| Confidence | MEDIUM (unclear if running in production) |

### LLM Client (src/core/llm_client.py)
| Aspect | Status | Detail |
|--------|--------|--------|
| Purpose | Universal LLM provider chain | 10 providers, 23K LOC |
| Entry Points | llm_client.send() | Single |
| Failure Modes | All providers down, circuit breaker cascade, rate limits | Handled |
| Recovery | 10-step fallback → OfflineProvider, in-flight dedup, LRU cache | Excellent |
| Scaling | Per-instance cache, no shared state | Scalable per instance |
| Security | API keys from env only, no logging of responses | Good |
| Confidence | HIGH |

---

## WHAT BREAKS FIRST AT 1M USERS?

1. **MCUBilling singleton** — inconsistent credit balances across instances → revenue loss
2. **In-memory rate limiter** — attackers bypass limits → API abuse
3. **In-memory task queue** — tasks lost on restart → user frustration
4. **Single gateway instance** — no failover → complete outage
5. **JSONL file-based state** — concurrent writes corrupt data → pilot data loss
6. **ThreadPool DAG (4 workers)** — recipe execution bottleneck → queue buildup

## IF PRIMARY ENGINEER DISAPPEARS?

1. ✅ CLAUDE.md is comprehensive (constitution)
2. ✅ Audit documents now provide architecture + risks
3. ⚠️ No CONTRIBUTING.md, no TROUBLESHOOTING, no RUNBOOKS
4. ⚠️ No incident response procedures
5. ❌ No documented secret rotation
6. ❌ No disaster recovery plan
7. ❌ Daemon operational status unclear

## IF PRODUCTION FAILS AT 3AM?

1. ✅ Telegram alerts for critical errors (Jidoka)
2. ✅ Health endpoint for monitoring tools
3. ⚠️ No PagerDuty/OpsGenie integration
4. ⚠️ No runbook for common failure scenarios
5. ❌ No automatic rollback (manual LaunchDaemon restart)
6. ❌ No incident response playbook

---

## RECOMMENDED ROADMAP

### Week 1 (Immediate)
- [ ] B1: Migrate MCUBilling to PostgreSQL
- [ ] B3: Redis-backed rate limiting
- [ ] H1: Fix CORS wildcard
- [ ] H2: Disable public Swagger
- [ ] H3: Fail-closed license gate
- [ ] H6: Fix bare except in gateway

### Week 2-3 (Short-term)
- [ ] B2: Redis-backed task queue
- [ ] B4: JSONL backup + encryption
- [ ] B5: Expand test coverage (raas, llm_client)
- [ ] H4: DB health check
- [ ] H5: Prometheus /metrics endpoint
- [ ] H7: Circuit breaker on external APIs

### Month 2 (Medium-term)
- [ ] M1-M8: All medium priority fixes
- [ ] Create CONTRIBUTING.md, TROUBLESHOOTING, RUNBOOKS
- [ ] Add load testing suite
- [ ] Add E2E test suite
- [ ] Implement blue/green deployment

### Quarter 2 (Long-term)
- [ ] L1-L6: All low priority fixes
- [ ] Extract RaaS to separate service
- [ ] Implement Temporal for job orchestration
- [ ] Add Grafana dashboards
- [ ] Implement canary releases

---

## Unresolved Questions

1. Is the daemon running in production? Resource consumption unknown.
2. What is the actual PostgreSQL hosting? (connection details needed for B1 fix)
3. Monthly LLM provider spend? Budget alerts needed.
4. How many active pilot users? JSONL file sizes?
5. Are any of the 15 CI/CD workflows currently failing on main?
6. Is cleo-new tracking an upstream repo?
7. Which packages are published to npm?
8. What's the actual response time of `/v1/missions` under load?
