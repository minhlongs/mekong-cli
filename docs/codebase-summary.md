# Mekong CLI v6.0 — Codebase Summary

**Version:** 6.0.0 | **Status:** Phase 01-04 (Seed Layer COMPLETE) | **Last Updated:** 2026-04-25

> AI-operated business platform. 4-phase Seed→Tree→Forest→Land architecture. Phase 01 (Seed) complete: 319 commands, 542 skills, Ollama-native Python stdlib agents.

---

## Executive Overview

**Mekong CLI v6.0** restructures around a 4-phase growth architecture. Phase 01 (Seed) is production-ready with a local Python CLI + ChromaDB memory + Ollama integration. The platform enables autonomous agent orchestration with Plan-Execute-Verify (PEV) across 5 business layers (Founder, Business, Product, Engineering, Ops).

**Key Stats:**
- **4,500+ files** | Phase 01-04 complete on main
- **Python 3.9+** stdlib-first design (no requests/httpx) | TypeScript/Node.js 18+
- **Monorepo:** Seed runtime + Tools + Apps + Integrations + Observability
- **Deployment:** M1 Max local (Phase 01) → Telegram+Web (Phase 02) → Multi-tenant (Phase 03) → Temporal+CI/CD (Phase 04)
- **License:** MIT | Open source infrastructure

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  CLI: mekong cook/fix/plan/deploy/... (319 commands)  │
│  Dashboard: mekongmind.com → /v1/missions            │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌─────────▼──────────┐
        │  API Gateway       │  FastAPI + auth + MCU metering
        │  src/api/          │  HTTP 402 on zero balance
        │  Hono/CF Workers   │
        └─────────┬──────────┘
                   │
        ┌─────────▼──────────┐
        │  PEV Engine        │  src/core/
        │  planner.py        │  LLM task decomposition
        │  executor.py       │  shell/LLM/API execution
        │  verifier.py       │  quality gates + rollback
        │  orchestrator.py   │  Plan→Execute→Verify loop
        └─────────┬──────────┘
                   │
    ┌──────────────▼──────────────────┐
    │  Agent Layer   src/agents/      │
    │  GitAgent  FileAgent  ShellAgent│
    │  LeadHunter  ContentWriter      │
    └──────────────┬──────────────────┘
                   │
        ┌─────────▼──────────┐
        │  LLM Router        │  src/core/llm_client.py
        │  3 vars, any       │  Opus/Sonnet/Qwen/Ollama
        │  provider          │
        └────────────────────┘
```

**Data Plane:**
- **Database:** Cloudflare D1 (SQLite) + PostgreSQL (optional)
- **Cache:** Cloudflare KV + Redis (optional)
- **Storage:** Cloudflare R2 (S3-compatible)
- **Messaging:** Polar.sh webhooks + email

---

## Directory Structure

### Phase 01: Seed Layer (COMPLETE 2026-04-25)

```
seed/                                 # Local Python CLI runtime (stdlib-only)
├── main.py                          # Entry: python3 seed/main.py "task"
├── agents/
│   ├── base.py                      # BaseAgent protocol + @timed decorator
│   ├── ceo.py                       # Planning agent (LLM task decomposition)
│   ├── developer.py                 # Code execution agent
│   └── tester.py                    # Verification agent
├── llm_client.py                    # Ollama urllib client (no SDK)
├── memory.py                        # ChromaDB + SQLite hybrid store
└── config.py                        # ENV-based configuration

tests/seed/                           # Unit tests (69 tests, no Ollama needed)
├── test_seed_config.py              # Config validation
├── test_seed_llm_client.py          # LLM client + fallback
├── test_seed_agents_base.py         # Base agent + decorators
├── test_seed_memory.py              # Memory hybrid store
├── test_seed_agents_ceo.py          # CEO agent planning
├── test_seed_agents_dev_tester.py   # Developer + Tester agents
├── test_seed_main_pipeline.py       # Main pipeline integration
└── conftest.py                      # pytest fixtures + mocks

tools/                                # Capability tools
├── file_system.py                   # File operations
└── browser.py                       # Browser automation

apps/
├── web/mission-control.html         # htmx Mission Control UI
├── api/
│   ├── server.py                    # FastAPI single-tenant (port 8765)
│   └── gateway.py                   # Multi-tenant JWT gateway (port 8766)

worker/
└── main.py                          # Redis queue worker + Docker isolation

integrations/
└── telegram_bot.py                  # Telegram bot (set TELEGRAM_TOKEN)

observability/
└── agent_metrics.py                 # @timed decorator + Prometheus metrics

feedback/
└── signals_loop.py                  # Weekly LLM evals + analysis

clipmart/
└── marketplace_api.py               # Agent template marketplace

.github/workflows/
└── ai-native-ci.yml                 # 5-gate CI/CD pipeline (Gate 5: pytest)

docker-compose.seed.yml              # Container stack
Dockerfile.seed                       # Build image (copies seed/ tools/ worker/ apps/ integrations/ clipmart/ observability/ feedback/)
requirements.seed.txt                # chromadb, fastapi, uvicorn, redis, pytest
```

### Core Packages

```
packages/
├── mekong-cli-core/              # Main CLI binary
│   ├── src/
│   │   ├── core/
│   │   │   ├── pev-engine/
│   │   │   │   ├── planner.py
│   │   │   │   ├── executor.py
│   │   │   │   ├── verifier.py
│   │   │   │   └── orchestrator.py
│   │   │   ├── telemetry/        # Layer 2: OpenTelemetry SDK
│   │   │   │   ├── observe.py    # @observe_agent decorator + metrics
│   │   │   │   └── otel_setup.py
│   │   │   ├── signals/          # Layer 2: Signals loop (SQLite evals)
│   │   │   │   ├── evals.py
│   │   │   │   └── emit.py
│   │   │   ├── llm_client.py      # Router (3 env vars)
│   │   │   ├── llm_providers.yaml
│   │   │   ├── skill_loader.py
│   │   │   └── config.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── billing.py
│   │   │   │   ├── payment.py
│   │   │   │   ├── tasks.py
│   │   │   │   └── ... (10+ route groups)
│   │   ├── agents/
│   │   ├── cli/
│   │   │   ├── commands/
│   │   │   │   ├── metrics.py     # Layer 2: mekong metrics
│   │   │   │   ├── eval_agent.py  # Layer 2: mekong eval-agent
│   │   │   │   └── ... (sdlc commands in phase-04)
│   │   │   └── sdlc/              # Layer 2: SDLC scaffold (phase-04)
│   │   │       ├── spec_command.py
│   │   │       ├── design_command.py
│   │   │       ├── code_command.py
│   │   │       └── deploy_command.py
│   │   └── tests/
│   └── pyproject.toml
├── agent-core/                    # Phase 1 (Seed): Agent kernel
│   ├── src/agent_core/
│   │   ├── base_agent.py          # Think→Act→Observe loop
│   │   ├── llm_client.py          # LLMClient (routes to mekongd:8765)
│   │   ├── memory.py              # SeedMemory (SQLite + ChromaDB)
│   │   ├── tools/                 # Sandboxed tools (browser, file_system, execute)
│   │   ├── agents/                # CEO, Developer, ToolAgent roles
│   │   ├── experiments.py         # A/B bucket (SHA-256 deterministic variant assignment)
│   │   ├── evals.py               # Offline-eval harness (regression gate)
│   │   └── cli.py                 # 11 commands: run/orchestrate/report/signal/history/prune/status/forest-status/eval/experiment/doctor
│   └── tests/                     # 196/196 tests pass, 1 skipped
├── agents/
│   └── hubs/                      # Department-scoped command catalogs (17 total)
│       ├── cto-hub.md             # Chief Technology Officer commands
│       ├── cfo-hub.md             # Chief Financial Officer commands
│       ├── cro-hub.md             # Chief Revenue Officer commands
│       ├── cmo-hub.md             # Chief Marketing Officer commands
│       ├── engineering-hub.md
│       ├── sales-hub.md
│       ├── marketing-hub.md
│       ├── growth-hub.md
│       ├── ops-hub.md
│       ├── finance-hub.md
│       ├── hr-hub.md
│       ├── design-hub.md
│       ├── data-hub.md
│       ├── venture-hub.md
│       ├── security-hub.md
│       ├── legal-hub.md
│       └── it-hub.md
└── openclaw-engine/               # Autonomous daemon
    ├── src/
    │   ├── daemon.ts
    │   ├── task-queue.ts
    │   └── webhook-handler.ts
    └── package.json
```

### Applications & Company Templates

```
apps/
├── algo-trader/          # Trading bot
├── sophia-ai-factory/    # Content factory
├── well/                 # Wellness
├── 84tea/               # E-commerce
├── raas-platform/       # Marketplace
├── landing-page/        # Next.js 16
├── nhipdieuxanh-landing/ # Next.js Smart Landing Page & Lead Ingestion Platform
└── ... (8+ apps)

clipmart/                 # Paperclip AI company templates
├── mekong-saas-startup/  # 22-agent full SaaS company (founders & scale-ups)
├── mekong-dev-shop/      # 8-agent engineering agency (dev teams)
└── mekong-solo-founder/  # 5-agent lean template (solopreneurs)
```

### Commands & Skills

```
.claude/
├── commands/             # 319 command definitions
│   ├── founder/ (46 cmds)
│   ├── business/ (32 cmds)
│   ├── product/ (17 cmds)
│   ├── engineering/ (47 cmds)
│   └── ops/ (27 cmds)
├── skills/              # 542 reusable skills
└── agents/              # 32 role definitions
```

---

## 5 Business Layers

| Layer | Commands | Purpose |
|-------|----------|---------|
| 👑 Founder | 46 | Strategy, fundraising, IPO |
| 💼 Business | 32 | Revenue, operations, HR |
| 🎯 Product | 17 | Planning, roadmap, sprints |
| ⚙️ Engineering | 47 | Build, test, deploy, review |
| 🔧 Ops | 27 | Monitoring, security, health |

**Total:** 319 root commands

---

## LLM Configuration

**3 environment variables, any OpenAI-compatible provider:**

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

**Supported Providers:**
- OpenRouter (Claude, Qwen, DeepSeek)
- Anthropic (Claude native)
- OpenAI (GPT-4)
- DashScope (Qwen)
- Ollama (local free)
- Google (Gemini)

**Aliases:**
- `mekong` — Default (Opus)
- `mekong-sonnet` — Claude Sonnet 4
- `mekong-qwen` — DashScope Qwen 3.5
- `mekong-cto` — Daemon mode

### Agent Workforce Layer (agent-core)

`packages/agent-core/` provides the **Phase 1 (Seed) agent kernel** — primitives for building autonomous workforce systems. It pairs with `mekongd` (Phase 0 cost-saving LLM proxy) to enable distributed agent execution via LLMClient routing to `http://127.0.0.1:8765` with Prometheus metrics at `GET /metrics`. Includes BaseAgent (think→act→observe), SeedMemory (SQLite + optional ChromaDB), pre-built CEO/Developer/ToolAgent roles with sandboxed tools (browser, file_system, execute), and A/B experiment bucketing (SHA-256 deterministic variant assignment via Statsig-style 3-step gate: offline eval ✓ / online signals ✓ / exposure ✓). Operator-facing CLI covers 11 commands with `--json` parity on non-interactive subcommands (forest-status/eval/history/report/status/experiment/doctor); `doctor` gives holistic triage (env + memory + connectivity + package). Seed phase completes Phase 2 (Forest multi-tenant) on demand.

#### Forest Layer (Multi-Tenant Runtime)

`packages/agent-forest/` — **Phase 2 (Forest)** multi-tenant agent orchestration platform. FastAPI gateway (JWT HS256 auth, rate limiting), Redis-backed task queue, async worker pool, per-user sandbox (subprocess-based). 142/142 tests pass. Routes task submission → queued for async execution → result callback via webhook. Pillar 4 security tier-1 active: `prompt_guard` (24 regex patterns + sanitize_input) rejects injection/dangerous-code on POST /task, with Prometheus counter `agent_forest_prompt_guard_rejections_total{reason}` + `AgentForestPromptGuardSurge` alert. Foundation for Phase 3 (Postgres user persistence) and Phase 4 (multi-cloud deployment).

---

## API Gateway

**FastAPI + Hono** with 15+ route groups:

| Route | Purpose |
|-------|---------|
| `POST /billing/tenants` | Tenant creation |
| `POST /v1/tasks` | Execute command |
| `POST /v1/agents/spawn` | Spawn agent |
| `POST /v1/chat/completions` | Chat API |
| `POST /webhook/polar` | Polar.sh subscription/order events |
| `GET /v1/reports` | Analytics |
| `GET /metrics` | Prometheus metrics (mekongd observability) |

**Middleware:**
- `authMiddleware` — API key validation
- `creditMeteringMiddleware` — MCU deduction
- `errorHandler` — HTTP 402 on zero balance

---

## Database Schema

**Cloudflare D1 (SQLite):**

**Status:** All 279 migrations applied | 524 total tables | Last run: 2026-03-23

**Core Tables:**

```sql
CREATE TABLE tenants (
  id TEXT PRIMARY KEY,
  api_key TEXT UNIQUE,
  name TEXT,
  tier VARCHAR(20),
  created_at TIMESTAMP
);

CREATE TABLE credits (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  balance INT,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE TABLE tasks (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  command VARCHAR(100),
  status VARCHAR(20),
  mcu_cost INT,
  created_at TIMESTAMP,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

---

## MCU Billing

**1 MCU = 1 credit. Consumption-based + subscription.**

| Tier | Price/mo | Credits | Daily Limit |
|------|----------|---------|-------------|
| Starter | $49 | 200 | All departments |
| Growth | $149 | 1,000 | + priority execution |
| Pro | $499 | 5,000 | + dedicated support |

**Command Costs:**
```
/cook = 1 MCU (×1-3 for scope)
/fix = 1 MCU (×1-2)
/plan = 2 MCU (×1-5)
/deploy = 2 MCU
/audit = 1 MCU
/help = 0 MCU
```

**COGS per MCU:**
- LLM (Opus/Sonnet routing): $0.18
- Caching (50% hit): $0.09
- Infra + Support: $0.06
- **Total: $0.15/MCU**

---

## Deployment

**100% Cloudflare — 3 layers:**

| Layer | Service | Cost |
|-------|---------|------|
| Frontend | Pages | $0 |
| Edge API | Workers | $0 |
| Backend | D1 + KV + R2 | Pay-per-use |

**Deploy:**
```bash
bash mekong/infra/scaffold.sh myproject startup
bash mekong/infra/scaffold.sh myproject scale
```

**CI/CD:**
- GitHub Actions (`.github/workflows/`)
- Pre-commit linting + type checks
- Pre-push tests
- Auto-deploy on merge

---

## Skills Catalog (542 Total)

| Domain | Count |
|--------|-------|
| Code Review | 28 |
| Testing | 35 |
| Debugging | 22 |
| Documentation | 18 |
| DevOps | 42 |
| AI/ML | 31 |
| Data | 25 |
| Web3 | 15 |
| Compliance | 12 |
| Business | 78 |
| Other | 242 |

---

## Code Standards

- **File Size:** < 200 lines per file
- **Type Hints:** Required for all functions
- **Docstrings:** Required for classes/methods
- **Naming:** `snake_case` (Python), `kebab-case` (files)
- **Secrets:** Never in code — use `.env`
- **Testing:** `pytest` must pass before push

---

## Key Entry Points

**CLI:**
```bash
source ~/mekong-cli/scripts/shell-init.sh
mekong cook "Build a REST API"
mekong-opus
mekong-qwen
```

**API:**
```bash
curl -X POST https://api.mekongmind.com/v1/tasks \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"command": "cook", "goal": "Build landing page"}'
```

**Contributing:**
```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
pip install -e ".[dev]"

# Run seed layer tests (69 tests, no Ollama needed)
make test-seed    # Recommended
# OR: pytest tests/seed/ -v
```

---

## Dependencies

**Python:** `fastapi`, `anthropic`, `langchain`, `pydantic`, `sqlalchemy`, `httpx`

**Node.js:** `hono`, `wrangler`, `next.js`, `react`, `typescript`

**CLI Tools:** `git`, `docker`, `claude`, `gemini-cli`

---

## Company Templates (Clipmart)

**Paperclip AI company templates** — Pre-built agent teams for different business models:

| Template | Agents | Use Case | Budget |
|----------|--------|----------|--------|
| **mekong-saas-startup** | 22 | Funded SaaS founders building full org | Scalable |
| **mekong-dev-shop** | 8 | Solo developers running a full agency | 2,100 MCU/mo |
| **mekong-solo-founder** | 5 | Solopreneurs shipping fast | 1,550 MCU/mo |

**Features per template:**
- Pre-configured agent org charts
- Skills aligned to roles (Binh Pháp governance)
- Escalation matrices and approval workflows
- Integration with Mekong CLI commands
- MIT licensed, ready to fork

**Quick start:**
```bash
cd mekong-cli/clipmart/mekong-solo-founder
paperclip company init .
mekong company/start
```

---

## Nhịp Điệu Xanh Cần Thơ Smart Landing Page (`apps/nhipdieuxanh-landing`)

A Next.js 15+ & Tailwind CSS project implementing the smart landing page and lead ingestion gateway.

### File Structure
```
apps/nhipdieuxanh-landing/
├── app/
│   ├── api/
│   │   └── leads/
│   │       └── route.ts             # Lead ingestion API (validation, masking, scoring)
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx                     # Main interactive landing page UI
├── lib/
│   └── prisma.ts                    # Prisma Client singleton
├── prisma/
│   └── schema.prisma                # PostgreSQL schema (Lead, LeadProfile)
├── scripts/
│   └── check-leads.ts               # Verification script for database query tests
├── package.json
└── tailwind.config.ts
```

### Component Layout & Core Implementations

1. **`app/page.tsx` (Interactive UI)**:
   - Uses `use client` with React hooks for reactive state management.
   - **Dynamic Localization**: Updates promotion banners based on a selected dropdown (e.g. Cần Thơ, An Giang, Cà Mau, Sóc Trăng).
   - **Mortgage Calculator**: Reactive calculation of monthly principal & interest payments using a standard amortization formula:
     $$M = \frac{P \cdot r \cdot (1 + r)^n}{(1 + r)^n - 1}$$
   - **Gated Blueprint Lock**: Intercepts blueprints download. Verifies user email and phone validation states client-side.
   - **Floating Chatbot Mockup**: Employs client-side regex matching to reply to user FAQs (pricing, location, legal status, loan criteria).
   - **Ingestion Lead Form**: Sends validated input data (with consent choice) to `POST /api/leads`.

2. **`app/api/leads/route.ts` (API Processing & Ingestion)**:
   - **Input Validation**: Uses regex validation for Vietnamese phone numbers (`/^(0|84|\+84)(3|5|7|8|9)[0-9]{8}$/`) and standard emails.
   - **Decree 13 Privacy Compliance Boundary**: Checks the user `consent` flag. If false, executes masking of PII (Name, Phone, Email) prior to database write.
   - **Uniqueness & Deduplication**: Generates a SHA-256 hash (`leadHash`) based on phone/email to avoid duplicate submissions using a database-level `upsert`.
   - **Lead Scoring System**: Computes interest score:
     - Valid Phone: `+20` points.
     - Valid Email: `+10` points.
     - Location Cần Thơ: `+30` points (Mekong provinces: `+20`).
     - Intent Investment: `+10` points.
     - Budget $\ge 2$B VND: `+10` points.
     - Maps to category `COLD` (<40), `WARM` (40-69), or `HOT` ($\ge$ 70).
   - **Persona Classification**: Parses the intent string to map user to a persona: `Phụ huynh học sinh`, `Nhà đầu tư`, or `Người mua nhà định cư`.

3. **`prisma/schema.prisma` (PostgreSQL Database Schema)**:
   - Sets the database provider to `postgresql`.
   - Models the `Lead` model mapped to the `leads` table and a 1-to-1 relationship with the `LeadProfile` model mapped to the `lead_profiles` table.

---

## Next Steps

- **Getting Started:** `/docs/getting-started.md`
- **API Reference:** `/docs/api-reference.md`
- **Deployment:** `/docs/DEPLOYMENT_GUIDE.md`
- **Company Templates:** `/clipmart/`
- **Contributing:** `/CONTRIBUTING.md`
