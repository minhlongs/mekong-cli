# Architecture Understanding — Mekong CLI v6.0.0

**Date:** 2026-05-22 | **Auditor:** Claude Opus 4.6 | **Confidence:** High (code-verified)

---

## 1. System Entry Points

### 1.1 CLI Entry (`src/main.py` → `src/cli/app_setup.py`)

**Runtime:** `python3 src/main.py` or `mekong` alias (via `scripts/mekong-wrapper.sh`)

Flow:
```
User types `mekong cook "build feature X"`
  → scripts/mekong-wrapper.sh routes to CC CLI binary
  → CC CLI discovers .claude/commands/cook.md
  → cook.md instructs CC CLI to invoke PEV engine
  → src/main.py (Typer) → src/cli/app_setup.py → build_app()
  → Registers 5 sub-apps: bmad, binh-phap, agi, swarm, schedule, memory,
    telegram, autonomous, tools, browse, collab, spec, design, code, deploy
  → Registers flat commands: cook, workflow, recipe, system, metrics, eval_agent
  → Total: 342+ commands across 6 business layers
```

**Confidence:** High — verified via `src/cli/app_setup.py` line-by-line.

### 1.2 API Gateway (`src/gateway.py`)

**Runtime:** `uvicorn src.gateway:app --port 8000`

FastAPI v3.3.0 server. 13+ routers mounted:

| Router | Prefix | Source |
|--------|--------|--------|
| mission_router | /v1/missions | src/api/mission_routes.py |
| webhook_mcu_router | /v1/webhooks | src/api/webhook_routes.py |
| coupon_router | /v1/coupons | src/api/coupon_routes.py |
| polar_webhook_router | /v1/polar | src/api/polar_webhook_routes.py |
| auth_router | /v1/auth | src/api/auth_routes.py |
| vn_auth_router | /v1/auth/vn | src/api/vn_auth_routes.py |
| raas_router | /v1/raas | src/raas/ |
| revenue_router | /v1/revenue | src/api/revenue_routes.py |
| checkout_router | /v1/checkout | src/api/checkout_routes.py |
| tenant_router | /v1/tenants | src/api/tenant_routes.py |
| reports_router | /v1/reports | src/api/report_routes.py |
| vn_pricing_router | /v1/pricing/vn | src/api/vn_pricing_routes.py |
| vn_pilot_router | /v1/pilot | src/api/vn_pilot_routes.py |
| vn_payments_router | /v1/payments | src/api/vn_payment_routes.py |
| org_router | /v1/orgs | src/api/org_routes.py |
| billing_router | /v1/billing | src/api/billing_routes.py |
| autopilot_router | /v1/autopilot | src/api/autopilot_routes.py |
| marketplace_router | /v1/marketplace | src/api/marketplace_routes.py |

CORS origins: localhost:3000, localhost:8080, mekongmind.com, api.cashclaw.cc, ide.mekongmind.com

Health endpoints:
- `GET /healthz` — liveness (200 OK)
- `GET /health` — enhanced (uptime, memory, component status)

**Confidence:** High — router list verified from `src/gateway.py` imports.

### 1.3 Daemon (`src/daemon/__main__.py`)

**Runtime:** `python3 -m src.daemon`

Autonomous dispatch system ("Tôm Hùm"). Entry: `__main__.py` → Sentry init → `heartbeat_scheduler.main()`.

Components (5,254 LOC total):
- `worker_pool.py` — Async worker pool for parallel task execution
- `jidoka.py` — Toyota-style "stop the line" quality check
- `circuit_breaker.py` — Failure isolation (3 failures → 15s cooldown)
- `heartbeat.py` — Periodic health pings
- `dlq.py` — Dead letter queue for failed tasks
- `dispatcher.py` — Task routing to appropriate workers

**Confidence:** High — file list verified, LOC counted.

### 1.4 IDE Entry (`ide-core/`)

**Runtime:** Embedded Rust/Axum orchestrator + 3 MLX model servers

Structure:
- `ide-core/src/` — TypeScript CLI compiler
- `ide-core/engine-farm/` — Multi-model A/B testing framework
  - 3 MLX model servers for local inference
  - Orchestrator routes requests across models
  - A/B comparison for response quality

**Confidence:** Medium — scaffolded, not fully deployed.

### 1.5 Seed Runtime (`seed/`)

**Runtime:** `python3 seed/main.py` — standalone, stdlib-only

Minimal agent runtime for Phase 01. No external deps (no FastAPI, no Pydantic). Uses Ollama for local LLM. Self-contained execution loop.

**Confidence:** High — verified standalone.

---

## 2. Request / Data Flow

### 2.1 CLI Command Flow

```
User input
  → mekong-wrapper.sh (provider routing: claude|gemini|qwen)
  → CC CLI binary with --dangerously-skip-permissions
  → .claude/commands/*.md matched by command name
  → Command frontmatter specifies: tools, arguments, description
  → CC CLI executes command body (may invoke Python via src/main.py)
  → Python CLI: Typer app → command handler → PEV engine
  → PEV: planner.py (LLM decomposition) → executor.py (shell/LLM/API)
       → verifier.py (quality gates) → orchestrator.py (loop control)
  → Result returned to CC CLI → displayed to user
```

### 2.2 API Mission Flow

```
Client POST /v1/missions {goal, tier}
  → auth middleware (JWT validation)
  → MCU billing check (HTTP 402 if zero balance)
  → task_classifier.py → TaskProfile (complexity, domain, mcu_cost)
  → PEV engine:
    1. planner.py: LLM decomposes goal → subtask DAG
    2. executor.py: Runs each subtask (shell, LLM, API calls)
    3. verifier.py: Validates output quality, rollback on failure
    4. orchestrator.py: Loop until all subtasks pass or max retries
  → MCU deducted on success only
  → Response: {mission_id, status, result, mcu_spent}
```

### 2.3 VN Pilot Signup Flow

```
POST /v1/pilot/signup {name, zalo, business_type, city}
  → Validate input
  → Generate user_id: opc_NNN_xxxxxx
  → Allocate 50 free credits
  → Write to ~/.mekong/pilots.jsonl (append-only)
  → If is_new=True AND MEKONG_SIGNUP_WEBHOOK_URL set:
    → Fire-and-forget webhook to Zapier/Pipedream (BackgroundTasks)
  → Return {user_id, credits: 50}
```

### 2.4 VietQR Payment Flow

```
Bank transfer received by Sepay
  → Sepay forwards to POST /v1/payments/vietqr/webhook
  → HMAC signature validation (401 on fail)
  → Parse memo: "MEKONG-{user_id}"
  → Match amount to tier: 199K/299K/499K VND
  → _record_conversion(user_id, tier, bank_tx_ref) — idempotent
  → Return 200 (always, even on app errors — prevents bank retry-storm)
  → Errors logged to ~/.mekong/vietqr_webhook.log
```

### 2.5 Polar Webhook Flow (SaaS Billing)

```
Polar.sh sends webhook event (subscription.created, etc.)
  → POST /v1/polar/webhook
  → Signature validation
  → Event type routing:
    - subscription.created → provision license + allocate MCU credits
    - subscription.updated → adjust tier
    - subscription.canceled → revoke access
  → Write to PostgreSQL (licenses, usage_records tables)
```

**Confidence:** High for all flows — verified through actual route files and handler code.

---

## 3. Background Jobs & Schedulers

### 3.1 Daemon Heartbeat Scheduler

**Location:** `src/daemon/heartbeat_scheduler.py`

Runs as persistent process. Periodically:
- Dispatches queued tasks from pending pool
- Checks worker health
- Retries failed tasks from DLQ
- Reports metrics

### 3.2 DAG Recipes

**Location:** `recipes/` (82 YAML files)

Multi-step workflow definitions. Each recipe = directed acyclic graph of commands.
Executed by `src/cli/` recipe runner. Examples:
- Content pipeline: research → write → review → publish
- Deploy pipeline: test → build → deploy → verify

### 3.3 Autonomous Dispatch

**Location:** `src/daemon/dispatcher.py` + `src/daemon/worker_pool.py`

CTO daemon mode (`mekong-cto`): Plan→Dispatch→Verify→Sleep loop.
Workers pick tasks from queue, execute via PEV engine, report back.

### 3.4 Cron / Scheduled Scripts

**Location:** Various LaunchDaemons + scripts/

- `com.mekong.gateway.plist` — LaunchDaemon for API gateway
- `scripts/pilot-weekly-poll.py` — Monday send / Thursday report (manual cron)
- `scripts/pilot-metrics.py` — Usage aggregation (on-demand)

**Confidence:** High for daemon; Medium for cron (some scripts may be stale).

---

## 4. External Integrations

| Integration | Location | Protocol | Purpose |
|-------------|----------|----------|---------|
| **Polar.sh** | src/api/polar_webhook_routes.py | Webhook + API | SaaS billing, license provisioning |
| **Stripe** | src/raas/checkout/ | API | Legacy payment (being migrated to Polar) |
| **Sepay (VietQR)** | src/api/vn_payment_routes.py | Webhook | VN bank transfer auto-conversion |
| **Zalo OA** | src/commands/zalo_oa.py | API | Vietnamese business messaging |
| **Telegram** | src/cli/ (telegram sub-app) | Bot API | Notifications, admin commands |
| **OpenRouter** | src/core/llm_client.py | REST | Primary LLM provider (10-provider chain) |
| **Anthropic** | src/core/llm_client.py | REST | Claude API (fallback #4) |
| **OpenAI** | src/core/llm_client.py | REST | GPT API (fallback #5) |
| **Google Gemini** | src/core/llm_client.py | REST | Gemini API (fallback #6) |
| **DeepSeek** | src/core/llm_client.py | REST | DeepSeek API (fallback #3) |
| **DashScope (Qwen)** | src/core/llm_client.py | REST | Alibaba Qwen (fallback #2) |
| **Ollama** | src/core/llm_client.py | REST | Local inference (fallback #7) |
| **Sentry** | src/daemon/__main__.py, src/telemetry/ | SDK | Error tracking |
| **Prometheus** | pyproject.toml (prometheus-client) | Metrics | Usage metering |
| **OpenTelemetry** | src/telemetry/ | SDK | Distributed tracing |
| **Supabase** | packages/vibe-supabase/ | SDK | Auth + DB for frontend apps |
| **MISA** | src/commands/ (ke_toan integration) | API | Vietnamese accounting software |
| **Cloudflare** | mekong/infra/, infra/ | Workers/Pages/D1/KV/R2 | Deploy target |
| **GitHub Actions** | .github/workflows/ (15 files) | CI/CD | Build, test, deploy pipeline |

**Confidence:** High — all verified from imports and config files.

---

## 5. State Management

### 5.1 Server-Side State

| Store | Location | Purpose | Persistence |
|-------|----------|---------|-------------|
| PostgreSQL | src/db/schema.py | Licenses, usage records, revocations | Durable |
| Cloudflare D1 | packages/mekong-engine/ | Edge API data | Durable |
| Cloudflare KV | mekong/infra/ | Key-value cache | Durable |
| Cloudflare R2 | mekong/infra/ | Object storage | Durable |
| JSONL files | ~/.mekong/*.jsonl | Pilot records, usage events, poll responses | File-based, append-only |
| JSON files | ~/.mekong/*.json | Config, credit balances | File-based |
| In-memory | src/core/llm_client.py | LRU cache, circuit breaker state | Volatile |

### 5.2 Client-Side State (Frontend Apps)

| App | State Manager | Store |
|-----|---------------|-------|
| well (WellNexus) | Zustand | In-memory + localStorage |
| dashboard | React state + server | Next.js RSC |
| mekong-ide | React state | In-memory |
| algo-trader-remote | Prisma ORM | PostgreSQL |

### 5.3 AI Agent State

| Layer | State | Location |
|-------|-------|----------|
| CC CLI sessions | Conversation history | ~/.claude/projects/ |
| Gemini sessions | Conversation history | .agent/ context |
| Factory contracts | 567 JSON machine contracts | factory/contracts/ |
| Command definitions | 342+ markdown files | .claude/commands/ |
| Skill definitions | 542 SKILL.md files | .claude/skills/ |

**Confidence:** High for server-side; Medium for frontend (many apps are scaffolds).

---

## 6. Persistence Layer

### 6.1 PostgreSQL Schema (`src/db/schema.py`)

Tables:
```sql
licenses (
  id SERIAL PRIMARY KEY,
  key_id VARCHAR UNIQUE NOT NULL,    -- license key
  tier VARCHAR NOT NULL,              -- starter/growth/pro
  email VARCHAR NOT NULL,
  subscription_id VARCHAR,            -- Polar subscription ref
  daily_limit INTEGER DEFAULT 200,
  status VARCHAR DEFAULT 'active',    -- active/suspended/revoked
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
)
-- Indexes: key_id, email, status

usage_records (
  id SERIAL PRIMARY KEY,
  license_id INTEGER REFERENCES licenses(id),
  date DATE NOT NULL,
  commands_count INTEGER DEFAULT 0,
  mcu_spent INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
)

revocations (
  id SERIAL PRIMARY KEY,
  key_id VARCHAR NOT NULL,
  reason TEXT,
  revoked_by VARCHAR,
  revoked_at TIMESTAMP DEFAULT NOW()
)
```

### 6.2 Cloudflare D1 (Edge)

Used by `packages/mekong-engine/` (Hono + D1). Schema managed via wrangler migrations.

### 6.3 File-Based Persistence

| File | Format | Usage |
|------|--------|-------|
| `~/.mekong/vn_config.json` | JSON | User wizard output |
| `~/.mekong/pilots.jsonl` | JSONL | Pilot user records (append-only) |
| `~/.mekong/pilot_credits.json` | JSON | Credit balances |
| `~/.mekong/usage_events.jsonl` | JSONL | Every command call logged |
| `~/.mekong/poll_responses.jsonl` | JSONL | Weekly NPS poll data |
| `~/.mekong/vietqr_webhook.log` | Log | VietQR webhook errors |
| `~/.mekong/admin-token.txt` | Text | Admin token (mode 600) |
| `~/.mekong/company.json` | JSON | Company config (session bootstrap) |
| `~/.mekong/tasks/` | JSON | Active task queue |

**Confidence:** High — all paths verified from code and CLAUDE.md.

---

## 7. Auth / AuthZ Flow

### 7.1 API Gateway Auth

```
Request → src/middleware/auth_middleware.py
  → Extract JWT from Authorization header
  → Validate signature (python-jose)
  → Extract claims: user_id, tier, features
  → src/core/feature_gates.py: check FEATURE_REGISTRY
    - cli_commands, advanced_agents, gateway_integration, enterprise_features
  → @require_feature decorator on protected endpoints
  → Pass to route handler with auth context
```

### 7.2 MCU Billing Gate

```
Authenticated request
  → src/core/mcu_billing.py: MCUBilling.check_balance(user_id)
  → If balance == 0 → HTTP 402 Payment Required
  → If balance < LOW_BALANCE_THRESHOLD (10) → warning header
  → On success: deduct MCU_COSTS[complexity] from balance
  → MCUTransaction logged to audit trail
```

### 7.3 VN Pilot Auth

```
Separate auth flow for Vietnamese pilot users:
  → src/api/vn_auth_routes.py (/v1/auth/vn)
  → User identified by MEKONG_USER_ID env var (opc_NNN_xxxxxx)
  → Admin endpoints require Bearer $MEKONG_ADMIN_TOKEN
  → Token stored in ~/.mekong/admin-token.txt (mode 600)
  → No password — pilot phase uses invite-only + credit system
```

### 7.4 License System

```
Polar webhook → subscription.created
  → src/api/polar_webhook_routes.py
  → Generate license key → store in PostgreSQL (licenses table)
  → Allocate MCU credits per tier (starter=200, growth=1000, pro=5000)
  → License includes: key_id, tier, email, subscription_id, daily_limit, expires_at
```

### 7.5 Frontend Auth

- **Supabase Auth:** Used by `packages/vibe-auth/`, `packages/vibe-supabase/`
- **Better Auth:** Referenced in some packages as alternative
- **No unified SSO** across all 38 apps — each app handles auth independently

**Confidence:** High for API auth; Medium for frontend (fragmented).

---

## 8. Deployment Topology

### 8.1 Production Infrastructure (Cloudflare-only)

```
┌──────────────────────────────────────────────────────────┐
│  CLOUDFLARE PAGES                                        │
│  ├── well (WellNexus portal)                             │
│  ├── mekong-ide (Web IDE)                                │
│  ├── admin (Control panel)                               │
│  └── landing (Marketing)                                 │
└──────────────┬───────────────────────────────────────────┘
               │ HTTPS
┌──────────────▼───────────────────────────────────────────┐
│  CLOUDFLARE WORKERS (Edge API)                           │
│  ├── mekong-engine (Hono + D1)    packages/mekong-engine │
│  ├── zalo-parser (Zalo OA)        packages/zalo-parser   │
│  └── openclaw-worker               apps/openclaw-worker  │
└──────────────┬───────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│  CLOUDFLARE DATA                                         │
│  ├── D1 (SQLite at edge)                                 │
│  ├── KV (key-value cache)                                │
│  └── R2 (object storage)                                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  SELF-HOSTED (api.cashclaw.cc)                           │
│  └── FastAPI Gateway (src/gateway.py)                    │
│      └── PostgreSQL (licenses, usage)                    │
│      └── Daemon (src/daemon/) — background worker        │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Local Development

```
MacBook M1 Max (16GB)
  ├── Ollama (localhost:11434) — Qwen 3.6 35B-A3B local inference
  ├── rapid-mlx (localhost:11437) — MLX model server
  ├── uvicorn (localhost:8000) — FastAPI gateway
  ├── pnpm dev (localhost:3000) — Frontend apps (Turbo)
  ├── ide-core engine-farm — 3 MLX model servers (A/B testing)
  └── LaunchDaemons:
      ├── com.mekong.gateway — API gateway
      └── com.mekong.daemon — Background worker
```

### 8.3 CI/CD Pipeline

```
git push → GitHub Actions
  ├── ci.yml (main trigger)
  │   ├── Python 3.11 + 3.12 matrix
  │   ├── gates.yml (lint, typecheck, tests, coverage)
  │   └── TS packages build (pnpm + Turbo)
  ├── deploy.yml → CF Pages + Workers
  ├── security-hardening.yml → scheduled scans
  └── test.yml → PR validation

15 workflows total. 5 quality gates.
```

**Confidence:** High — verified from workflow files, CLAUDE.md, and infra/.

---

## 9. Feature Flags

### 9.1 JWT-Based Feature Gates (`src/core/feature_gates.py`)

```python
FEATURE_REGISTRY = {
    "cli_commands": True,        # Base CLI access
    "advanced_agents": True,     # AI agent capabilities
    "gateway_integration": True, # API gateway access
    "enterprise_features": False # Enterprise-only features
}

@require_feature("advanced_agents")
async def run_agent(request):
    ...
```

Features are embedded in JWT claims. No external feature flag service (LaunchDarkly, etc.).

### 9.2 Environment-Based Toggles

| Env Var | Effect |
|---------|--------|
| `MEKONG_VIETQR_PROVIDER` + `_WEBHOOK_SECRET` | Enables VietQR webhook (absent → 503) |
| `MEKONG_SIGNUP_WEBHOOK_URL` | Enables signup notification webhook |
| `MEKONG_ADMIN_TOKEN` | Enables admin endpoints |
| `MEKONG_USER_ID` | Enables credit-gated mode (absent → anonymous) |
| `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL` | Configures LLM provider |

**Confidence:** High — verified from feature_gates.py and CLAUDE.md.

---

## 10. Environment Handling

### 10.1 Environment Variables (133 documented in .env.example)

Categories:
- **LLM Providers** (20+): `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `OPENROUTER_API_KEY`, `DASHSCOPE_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `OLLAMA_BASE_URL`
- **Billing** (5+): `POLAR_ACCESS_TOKEN`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- **Auth** (5+): `JWT_SECRET=REDACTED_KEY`, `MEKONG_ADMIN_TOKEN`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- **VN Hub** (5+): `MEKONG_VIETQR_PROVIDER`, `MEKONG_VIETQR_WEBHOOK_SECRET`, `MEKONG_SIGNUP_WEBHOOK_URL`
- **Infrastructure** (10+): `DATABASE_URL`, `SENTRY_DSN`, `CF_ACCOUNT_ID`, `CF_API_TOKEN`
- **Telemetry** (5+): `OTEL_EXPORTER_ENDPOINT`, `PROMETHEUS_PORT`

### 10.2 Config Files

| File | Purpose | Location |
|------|---------|----------|
| `.env.example` | Template (133 vars) | repo root |
| `mekong/adapters/llm-providers.yaml` | LLM provider presets | repo |
| `~/.mekong/vn_config.json` | VN user config | per-machine |
| `~/.mekong/company.json` | Company config | per-machine |
| `wrangler.toml` | CF Workers config | per-worker project |
| `pyproject.toml` | Python project config | repo root |
| `turbo.json` | Turborepo config | repo root |
| `.claude/settings.json` | Claude Code permissions | repo |

**Confidence:** High — .env.example verified with 133 entries.

---

## 11. Module Interaction Diagram

### Core Dependencies

```
src/gateway.py
  ├── src/api/* (13+ route modules)
  │   ├── src/core/mcu_billing.py (billing gate)
  │   ├── src/core/task_classifier.py (complexity routing)
  │   └── src/auth/* (JWT middleware)
  ├── src/core/orchestrator.py (PEV loop)
  │   ├── src/core/planner.py (LLM decomposition)
  │   │   └── src/core/llm_client.py (10-provider chain)
  │   ├── src/core/executor.py (task execution)
  │   │   └── src/agents/* (15 specialized agents)
  │   └── src/core/verifier.py (quality gates)
  └── src/raas/* (billing engine, 20K LOC)
      ├── credits, checkout, marketplace
      ├── webhooks, tenants, A/B testing
      └── src/db/schema.py (PostgreSQL)

src/daemon/
  ├── dispatcher.py → worker_pool.py → PEV engine
  ├── circuit_breaker.py (failure isolation)
  ├── jidoka.py (quality stop)
  ├── dlq.py (dead letter queue)
  └── heartbeat.py (health monitoring)

.claude/commands/ (342+)
  → src/core/command_loader.py (YAML frontmatter parser)
  → factory/contracts/ (567 JSON machine contracts)
  → Consumed by CC CLI, Gemini CLI, PEV engine classifier
```

### TypeScript Package Dependencies

```
packages/mekong-cli-core (CLI entry)
  └── packages/openclaw-engine (mission orchestration)
      └── packages/mekong-engine (CF Workers edge runtime)

packages/vibe (core)
  ├── packages/vibe-ui (components)
  ├── packages/vibe-auth (auth)
  ├── packages/vibe-payment (Polar/Stripe)
  ├── packages/vibe-supabase (DB)
  └── packages/vibe-* (32 domain packages)

packages/cleo-new (CleoCode framework, v2026.5.87)
  └── 30+ internal packages (self-contained monorepo)
```

---

## 12. Key Architectural Patterns

### 12.1 PEV (Plan-Execute-Verify)

Core orchestration loop in `src/core/`:
1. **Plan** (planner.py, 667 LOC): LLM decomposes goal into subtask DAG
2. **Execute** (executor.py, 445 LOC): Runs subtasks (shell, LLM, API calls)
3. **Verify** (verifier.py, 482 LOC): Quality gates, rollback on failure
4. **Orchestrate** (orchestrator/, 1,243 LOC): Loop control, retry logic

### 12.2 Universal LLM Client

10-provider fallback chain with circuit breaker:
- 3 failures in 60s → provider marked unhealthy for 15s cooldown
- LRU cache for repeated queries
- Provider-specific adapters: GeminiProvider, OpenAICompatibleProvider, OfflineProvider
- Hooks pipeline for request/response transformation

### 12.3 MCU Credit System

Mission Credit Units — consumption-based billing:
- simple=1 MCU, standard=3, complex=5
- Deduct AFTER successful delivery only
- HTTP 402 on zero balance
- Audit trail for every transaction

### 12.4 Dual AI Framework

Two parallel AI configuration layers:
- `.claude/` — 413 commands, 6 agents, 23 hooks, 542 skills → Claude Code CLI
- `.agent/` — 271 skills, 50 workflows, 106 subagents → Gemini/Antigravity CLI

Both consume the same codebase but use different dispatch mechanisms.

### 12.5 Factory Contract System

567 JSON machine contracts in `factory/contracts/`:
- Generated from `.claude/commands/` YAML frontmatter
- Consumed by PEV engine task classifier
- Cascade system: contracts reference other contracts
- Pricing metadata: MCU cost per command

---

## 13. Risk Assessment

### HIGH Risk

| Risk | Location | Impact |
|------|----------|--------|
| LLM provider chain failure | src/core/llm_client.py | All AI features down if all 10 providers fail |
| MCU billing bypass | src/core/mcu_billing.py | Revenue loss if gate can be circumvented |
| Admin token exposure | ~/.mekong/admin-token.txt | Full pilot system access |
| JSONL corruption | ~/.mekong/*.jsonl | Data loss for pilot users (no backup) |
| Gateway single point | api.cashclaw.cc | All API traffic routes through one server |

### MEDIUM Risk

| Risk | Location | Impact |
|------|----------|--------|
| File-based state | ~/.mekong/ | No ACID guarantees, no concurrent write safety |
| Coverage gaps | pyproject.toml exclusions | Critical paths (llm_client, cli, commands) untested |
| Stale factory contracts | factory/contracts/ | 567 contracts may drift from actual commands |
| Frontend fragmentation | 38 apps, no unified auth | Inconsistent UX, auth gaps |
| Daemon autonomy | src/daemon/ | Unattended execution could cause resource waste |

### LOW Risk

| Risk | Location | Impact |
|------|----------|--------|
| Stale docs | docs/ (88 files) | Developer confusion, but code is source of truth |
| Scaffold apps | apps/ (28+ unused) | Disk space, no runtime impact |
| Dual AI config | .claude/ + .agent/ | Maintenance overhead but no functional conflict |

---

## Unresolved Questions

1. Is the FastAPI gateway (api.cashclaw.cc) behind a load balancer or running on a single instance?
2. What's the actual PostgreSQL hosting — Supabase, self-hosted, or CF D1 via proxy?
3. How are JSONL files (~/.mekong/) backed up? Any disaster recovery plan?
4. Is the daemon (`src/daemon/`) running in production or development-only?
5. What's the actual deployment cadence? The 15 CI/CD workflows suggest automation, but manual deploy scripts also exist.
6. How does the seed/ runtime relate to the main PEV engine? Are they parallel implementations or sequential evolution?
7. What's the actual test pass rate? 6,160 pytest tests collected but coverage excludes many critical paths.
8. Are the 567 factory contracts auto-generated or manually maintained? Drift risk unclear.
