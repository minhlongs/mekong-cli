# Mekong CLI — Codebase Summary

**Version:** 5.0.0 | **Status:** Production | **Last Updated:** 2026-03-23

> AI-operated business platform. Open source. Universal LLM. 319 commands, 542 skills, 410 contracts.

---

## Executive Overview

**Mekong CLI** is an orchestrated AI platform built on the Plan→Execute→Verify (PEV) engine. It enables automated business operations across 5 layers (Founder, Business, Product, Engineering, Ops) with 319+ commands and 542 skills.

**Key Stats:**
- **4,002 files** | 5.8M tokens | 23M characters
- **Python 3.9+** | TypeScript/Node.js 18+ | Cloudflare Workers + local LLM
- **Monorepo structure:** Core SDK + 8 applications + 542 reusable skills
- **Deployment:** 100% Cloudflare (Pages, Workers, D1, R2, KV) + M1 Max LLM (192.168.11.111:11434)
- **License:** MIT | Open source with commercial licensing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  CLI: mekong cook/fix/plan/deploy/... (319 commands)  │
│  Dashboard: agencyos.network → /v1/missions            │
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
- **Messaging:** Stripe/Polar webhooks + email

---

## Directory Structure

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
│   │   └── tests/
│   └── pyproject.toml
└── openclaw-engine/               # Autonomous daemon
    ├── src/
    │   ├── daemon.ts
    │   ├── task-queue.ts
    │   └── webhook-handler.ts
    └── package.json
```

### Applications

```
apps/
├── algo-trader/          # Trading bot
├── sophia-ai-factory/    # Content factory
├── well/                 # Wellness
├── 84tea/               # E-commerce
├── raas-platform/       # Marketplace
├── landing-page/        # Next.js 16
└── ... (8+ apps)
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

---

## API Gateway

**FastAPI + Hono** with 15+ route groups:

| Route | Purpose |
|-------|---------|
| `POST /billing/tenants` | Tenant creation |
| `POST /v1/tasks` | Execute command |
| `POST /v1/agents/spawn` | Spawn agent |
| `POST /v1/chat/completions` | Chat API |
| `POST /payment/webhook` | NOWPayments webhook |
| `GET /v1/reports` | Analytics |

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
| Free | $0 | 10 | 3/day |
| Starter | $79 | 150 | 15/day |
| Pro | $249 | 750 | 50/day |
| Enterprise | $599 | Unlimited* | Unlimited |

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
curl -X POST https://api.agencyos.network/v1/tasks \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"command": "cook", "goal": "Build landing page"}'
```

**Contributing:**
```bash
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
pip install -e ".[dev]"
pytest tests/
```

---

## Dependencies

**Python:** `fastapi`, `anthropic`, `langchain`, `pydantic`, `sqlalchemy`, `httpx`

**Node.js:** `hono`, `wrangler`, `next.js`, `react`, `typescript`

**CLI Tools:** `git`, `docker`, `claude`, `gemini-cli`

---

## Next Steps

- **Getting Started:** `/docs/getting-started.md`
- **API Reference:** `/docs/api-reference.md`
- **Deployment:** `/docs/DEPLOYMENT_GUIDE.md`
- **Contributing:** `/CONTRIBUTING.md`
