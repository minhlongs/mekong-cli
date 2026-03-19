# Mekong Engine — Cloudflare Worker RaaS API

Serverless PEV (Plan-Execute-Verify) engine on Cloudflare Workers with multi-tenant credit billing, BYOK LLM support, and progressive decentralization.

## Stack

| Component | Tech |
|-----------|------|
| Runtime | Cloudflare Workers (TypeScript) |
| Framework | Hono.js |
| Database | Cloudflare D1 (SQLite) |
| Cache | Cloudflare KV |
| LLM | Workers AI (Llama 3.1 8B) + BYOK (OpenAI/Google/Anthropic) |

**Production:** `https://mekong-engine.agencyos-openclaw.workers.dev`

## Quick Start

```bash
cd packages/mekong-engine

# Install deps
pnpm install

# Local dev (auto-creates local D1)
pnpm exec wrangler dev

# Deploy
pnpm exec wrangler deploy

# Health check
curl https://mekong-engine.agencyos-openclaw.workers.dev/health
```

## Route Groups Overview

| # | Route Group | Prefix | Auth | Purpose |
|---|-------------|--------|------|---------|
| 1 | **Tasks** | `/v1/tasks` | Bearer | Mission CRUD with credit deduction |
| 2 | **Agents** | `/v1/agents` | Bearer | Agent execution (git, file, shell, etc.) |
| 3 | **Settings** | `/v1/settings` | Bearer | BYOK LLM configuration |
| 4 | **Billing** | `/billing` | Partial | Tenants, credits, Polar.sh webhooks |
| 5 | **Chat** | `/v1/chat` | Webhook | Zalo/Facebook Messenger webhooks |
| 6 | **Content** | `/v1/content` | Bearer | AI content generation (batch) |
| 7 | **CRM** | `/v1/crm` | Bearer | Contacts, companies, campaigns |
| 8 | **Reports** | `/v1/reports` | Bearer | Analytics with AI summaries |
| 9 | **Onboarding** | `/v1/onboard` | Bearer | 4-step tenant onboarding |
| 10 | **Payment VN** | `/payment` | Webhook | MoMo/VNPAY payment webhooks |
| 11 | **Governance** | `/v1/governance` | Bearer | Stakeholders, proposals, quadratic voting |
| 12 | **Ledger** | `/v1/ledger` | Bearer | Double-entry ledger, transfers |
| 13 | **Equity** | `/v1/equity` | Bearer | Cap table, SAFE notes, conversions |
| 14 | **Revenue** | `/v1/revenue` | Bearer | Revenue tracking, MRR/ARR |
| 15 | **Funding** | `/v1/funding` | Bearer | Quadratic funding rounds |
| 16 | **Matching** | `/v1/matching` | Bearer | Skill profile matching |
| 17 | **Conflicts** | `/v1/conflicts` | Bearer | 5-level conflict resolution |
| 18 | **Decentralization** | `/v1/decentralization` | Bearer | Progressive decentralization phases |
| 19 | **RBAC** | `/v1/rbac` | Bearer | Permission checking |
| 20 | **Constitution** | `/v1/constitution` | Bearer | 4-layer constitution enforcement |
| 21 | **Marketplace** | `/v1/marketplace` | Bearer | Plugin marketplace |

## Authentication

### Bearer Token Flow
```
Authorization: Bearer <API_KEY>
→ SHA-256 hash → tenets.api_key_hash lookup → tenant context
```

### Webhook Signature Verification
- **Zalo:** HMAC-SHA256 (`x-zalo-signature` header)
- **Facebook:** HMAC-SHA256 (`X-Hub-Signature-256` header)
- **Polar.sh:** HMAC-SHA256 (`webhook-signature` header)
- **MoMo/VNPAY:** SHA512 (`signature` in payload)

## Route Groups Detail

---

### 1. Tasks (`/v1/tasks`)

Mission management with automatic credit deduction.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/tasks` | ✓ | Create mission (deducts credits) |
| GET | `/v1/tasks` | ✓ | List missions |
| GET | `/v1/tasks/:id` | ✓ | Get mission status |
| GET | `/v1/tasks/:id/stream` | ✓ | SSE stream |
| POST | `/v1/tasks/:id/cancel` | ✓ | Cancel + refund |

**POST /v1/tasks** — Create Mission
```json
// Request
{
  "goal": "Analyze sales data and generate insights",
  "params": { "complexity": "standard" }
}

// Response (201 Created)
{
  "id": "msn_abc123",
  "tenant_id": "tnt_xyz",
  "goal": "Analyze sales data and generate insights",
  "status": "pending",
  "credits_deducted": 3,
  "created_at": "2026-03-19T10:00:00Z"
}
```

**Credit Complexity:**
- `simple`: 1 credit (single command)
- `standard`: 3 credits (multi-step)
- `complex`: 5 credits (orchestrated agents)

---

### 2. Agents (`/v1/agents`)

Specialized agent execution endpoints.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/agents` | ✓ | List available agents |
| POST | `/v1/agents/:name/run` | ✓ | Run agent |

**Available Agents:**
- `git` — Git operations (status, diff, log, commit, branch)
- `file` — File operations (find, read, tree, stats, grep)
- `shell` — Shell command execution
- `lead-hunter` — Company/CEO lead discovery
- `content-writer` — Content generation
- `recipe-crawler` — Recipe file discovery

**POST /v1/agents/git/run**
```json
// Request
{
  "command": "status",
  "params": { "repo_path": "/path/to/repo" }
}

// Response (202 Accepted)
{
  "agent": "git",
  "command": "status",
  "status": "accepted",
  "message": "Agent execution queued — use /v1/tasks to track progress"
}
```

---

### 3. Settings (`/v1/settings`)

BYOK LLM configuration with AES-256-GCM encryption.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/settings/llm` | ✓ | Get LLM config (masked key) |
| POST | `/v1/settings/llm` | ✓ | Save LLM config |
| DELETE | `/v1/settings/llm` | ✓ | Remove custom LLM |

**POST /v1/settings/llm**
```json
// Request (minimal — provider + api_key only)
{
  "provider": "openai",
  "api_key": "sk-proj-abc123..."
}

// OR (full configuration)
{
  "provider": "anthropic",
  "api_key": "sk-ant-...",
  "base_url": "https://api.anthropic.com/v1",
  "model": "claude-sonnet-4-20250514"
}

// Response
{
  "provider": "openai",
  "api_key": "sk-***abc",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini"
}
```

**Provider Presets:**

| Provider | Default Base URL | Default Model |
|----------|-----------------|---------------|
| `openai` | `https://api.openai.com/v1` | `gpt-4o-mini` |
| `google` | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.0-flash` |
| `anthropic` | `https://api.anthropic.com/v1` | `claude-sonnet-4-20250514` |
| `custom` | (required) | (required) |

---

### 4. Billing (`/billing`)

Tenant management, credit ledger, Polar.sh webhooks.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/billing/tenants` | ✗ | Create tenant → returns API key |
| POST | `/billing/tenants/regenerate-key` | Rate limited | Regenerate API key |
| POST | `/billing/webhook` | Signature | Polar.sh payment webhook |
| GET | `/billing/pricing` | ✗ | Public pricing info |
| GET | `/billing/credits` | ✓ | Credit balance |
| GET | `/billing/credits/history` | ✓ | Credit history |

**POST /billing/tenants**
```json
// Request
{
  "name": "my-company"
}

// Response (201 Created)
{
  "tenant_id": "tnt_abc123",
  "name": "my-company",
  "api_key": "mk_xxx_secret_key",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key - it cannot be recovered if lost!"
}
```

**Polar.sh Product Mapping:**

| Product | Credits | Tier |
|---------|---------|------|
| `agencyos-starter` | 50 | pro |
| `agencyos-pro` | 200 | pro |
| `agencyos-agency` | 500 | enterprise |
| `agencyos-master` | 1000 | enterprise |
| `credits-10` | 10 | — |
| `credits-50` | 50 | — |
| `credits-100` | 100 | — |

---

### 5. Chat (`/v1/chat`)

Zalo OA + Facebook Messenger webhook handlers.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/webhook/zalo` | Signature | Zalo OA webhook |
| GET | `/webhook/facebook` | Token | Facebook verification |
| POST | `/webhook/facebook` | Signature | Facebook Messenger webhook |

**Zalo Webhook Payload:**
```json
{
  "event_name": "user_send_text",
  "app_id": "123456",
  "sender": { "id": "user_zalo_id" },
  "recipient": { "id": "oa_id" },
  "message": {
    "text": "Xin chào",
    "msg_id": "msg_abc123"
  },
  "timestamp": "2026-03-19T10:00:00Z"
}
```

**Features:**
- Signature verification (HMAC-SHA256)
- Replay attack prevention (duplicate msg_id/mid check)
- Auto-conversation threading
- KB lookup → LLM fallback
- Auto-reply via platform API

---

### 6. Content (`/v1/content`)

AI content generation with batch operations.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/content/generate` | ✓ | Generate single content |
| POST | `/v1/content/batch` | ✓ | Batch content generation |
| GET | `/v1/content/:id` | ✓ | Get content status |

**POST /v1/content/generate**
```json
// Request
{
  "type": "blog_post",
  "topic": "AI-powered customer service",
  "tone": "professional",
  "length": "long",
  "keywords": ["AI", "customer service", "automation"]
}

// Response
{
  "id": "cnt_abc123",
  "status": "processing",
  "estimated_tokens": 2000
}
```

---

### 7. CRM (`/v1/crm`)

Contact and company management with campaigns.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/crm/contacts` | ✓ | List contacts |
| POST | `/v1/crm/contacts` | ✓ | Create contact |
| GET | `/v1/crm/companies` | ✓ | List companies |
| POST | `/v1/crm/companies` | ✓ | Create company |
| POST | `/v1/crm/campaigns` | ✓ | Create campaign |
| GET | `/v1/crm/campaigns/:id/stats` | ✓ | Campaign statistics |

**POST /v1/crm/contacts**
```json
{
  "name": "Nguyen Van A",
  "email": "a.nguyen@example.com",
  "phone": "+84901234567",
  "company_id": "cmp_xyz",
  "tags": ["lead", "enterprise"]
}
```

---

### 8. Reports (`/v1/reports`)

Analytics dashboards with AI-powered summaries.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/reports/analytics` | ✓ | Analytics dashboard |
| GET | `/v1/reports/summary` | ✓ | AI-generated summary |
| POST | `/v1/reports/generate` | ✓ | Generate custom report |

**Query Parameters:**
- `period` — `daily`, `weekly`, `monthly`, `quarterly`
- `metrics` — comma-separated metric names
- `group_by` — tenant, channel, campaign

---

### 9. Onboarding (`/v1/onboard`)

4-step tenant onboarding flow.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/onboard/step/:step` | ✓ | Complete onboarding step |
| GET | `/v1/onboard/status` | ✓ | Get onboarding progress |

**Steps:**
1. `profile` — Company profile setup
2. `channels` — Connect Zalo/Facebook
3. `llm` — Configure BYOK LLM
4. `first_mission` — Run first PEV mission

---

### 10. Payment VN (`/payment`)

Vietnam payment gateway webhooks (MoMo, VNPAY).

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/payment/momo/webhook` | Signature | MoMo payment webhook |
| POST | `/payment/vnpay/webhook` | Signature | VNPAY payment webhook |

**MoMo Webhook Payload:**
```json
{
  "partnerCode": "agencyos",
  "orderId": "order_123",
  "requestId": "req_abc",
  "amount": 100000,
  "message": "success",
  "signature": "sha512_signature_here"
}
```

---

### 11. Governance (`/v1/governance`)

Stakeholder management, proposals, quadratic voting.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/governance/stakeholders` | ✓ | List stakeholders |
| POST | `/v1/governance/stakeholders` | ✓ | Add stakeholder |
| POST | `/v1/governance/proposals` | ✓ | Create proposal |
| POST | `/v1/governance/proposals/:id/vote` | ✓ | Cast vote (QF) |
| GET | `/v1/governance/proposals/:id/results` | ✓ | Voting results |

**Quadratic Voting Formula:**
```
votes = (Σ√contribution_i)² - Σcontribution_i
```

---

### 12. Ledger (`/v1/ledger`)

Double-entry accounting ledger.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/ledger/entries` | ✓ | List ledger entries |
| POST | `/v1/ledger/transfers` | ✓ | Create transfer |
| POST | `/v1/ledger/topups` | ✓ | Record credit topup |
| GET | `/v1/ledger/balance` | ✓ | Current balance |

**POST /v1/ledger/transfers**
```json
{
  "from_account": "acc_revenue",
  "to_account": "acc_tenant_credits",
  "amount": 100,
  "description": "Credit purchase",
  "metadata": { "tenant_id": "tnt_xyz", "order_id": "ord_123" }
}
```

---

### 13. Equity (`/v1/equity`)

Cap table management, SAFE notes, conversions.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/equity/cap-table` | ✓ | Current cap table |
| POST | `/v1/equity/shares` | ✓ | Issue shares |
| POST | `/v1/equity/safe` | ✓ | Create SAFE note |
| POST | `/v1/equity/convert` | ✓ | Convert SAFE to equity |

---

### 14. Revenue (`/v1/revenue`)

Revenue tracking, MRR/ARR calculations.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/revenue/metrics` | ✓ | Revenue metrics |
| GET | `/v1/revenue/mrr` | ✓ | MRR breakdown |
| GET | `/v1/revenue/arr` | ✓ | ARR calculation |

---

### 15. Funding (`/v1/funding`)

Quadratic funding rounds with matching pool.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/funding/rounds` | ✓ | Create funding round |
| GET | `/v1/funding/rounds/:id` | ✓ | Round details |
| POST | `/v1/funding/rounds/:id/contribute` | ✓ | Contribute to pool |
| POST | `/v1/funding/rounds/:id/apply` | ✓ | Apply for funding |
| POST | `/v1/funding/rounds/:id/calculate` | ✓ | Calculate QF matching |

**Quadratic Funding Formula:**
```
matched = (Σ√contribution_i)² - Σcontribution_i
```

---

### 16. Matching (`/v1/matching`)

Skill profile matching algorithm.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/matching/profiles` | ✓ | Create skill profile |
| GET | `/v1/matching/profiles/:id` | ✓ | Get profile |
| POST | `/v1/matching/profiles/:id/find` | ✓ | Find matches |

---

### 17. Conflicts (`/v1/conflicts`)

5-level conflict resolution protocol.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v1/conflicts` | ✓ | File conflict |
| GET | `/v1/conflicts/:id` | ✓ | Conflict details |
| POST | `/v1/conflicts/:id/escalate` | ✓ | Escalate conflict |
| POST | `/v1/conflicts/:id/resolve` | ✓ | Resolve conflict |

**Conflict Levels:**
1. `L1` — Direct negotiation
2. `L2` — Mediator involvement
3. `L3` — Stakeholder vote
4. `L4` — Constitution review
5. `L5` — Final arbitration

---

### 18. Decentralization (`/v1/decentralization`)

Progressive decentralization phase management.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/decentralization/status` | ✓ | Current phase |
| POST | `/v1/decentralization/transition` | ✓ | Transition phase |

**Phases:**
- `P0` — Centralized (founder controls)
- `P1` — Delegation (team leads)
- `P2` — Distributed (stakeholder voting)
- `P3` — Decentralized (DAO governance)

---

### 19. RBAC (`/v1/rbac`)

Permission checking middleware.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/rbac/permissions` | ✓ | List permissions |
| POST | `/v1/rbac/roles` | ✓ | Create role |
| POST | `/v1/rbac/check` | ✓ | Check permission |

**POST /v1/rbac/check**
```json
{
  "tenant_id": "tnt_xyz",
  "user_id": "usr_abc",
  "permission": "governance.proposals.create"
}

// Response
{
  "allowed": true,
  "role": "admin"
}
```

---

### 20. Constitution (`/v1/constitution`)

4-layer constitution enforcement.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/constitution` | ✓ | Get constitution |
| POST | `/v1/constitution/layers` | ✓ | Add layer |
| POST | `/v1/constitution/check` | ✓ | Compliance check |

**Layers:**
- `L0` — Core principles (immutable)
- `L1` — Governance rules (stakeholder vote)
- `L2` — Operational policies (team lead approval)
- `L3` — Procedures (automated)

---

### 21. Marketplace (`/v1/marketplace`)

Plugin marketplace with reviews.

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v1/marketplace/plugins` | ✓ | List plugins |
| POST | `/v1/marketplace/plugins` | ✓ | Submit plugin |
| GET | `/v1/marketplace/plugins/:id` | ✓ | Plugin details |
| POST | `/v1/marketplace/plugins/:id/review` | ✓ | Add review |

---

## Database Schema

### Core Tables

**tenants:** `id`, `name`, `api_key_hash`, `tier`, `created_at`

**credits:** `id`, `tenant_id`, `amount`, `reason`, `created_at`

**missions:** `id`, `tenant_id`, `goal`, `status`, `credits_used`, `total_steps`, `completed_steps`, `result`, `created_at`, `completed_at`

**tenant_settings:** `tenant_id`, `llm_provider`, `llm_api_key_encrypted`, `llm_base_url`, `llm_model`, `updated_at`

### Extended Tables

**ledger_entries:** `id`, `tenant_id`, `account`, `amount`, `direction`, `description`, `metadata`, `created_at`

**governance_proposals:** `id`, `tenant_id`, `title`, `description`, `status`, `votes_for`, `votes_against`, `created_at`

**equity_holdings:** `id`, `tenant_id`, `holder_id`, `shares`, `class`, `issued_at`

---

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `UNAUTHORIZED` | 401 | Invalid/missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Zod validation failed |
| `INSUFFICIENT_CREDITS` | 402 | Credit balance too low |
| `REPLAY_ATTACK` | 409 | Duplicate webhook event |
| `DATABASE_ERROR` | 500 | D1 query failed |
| `SERVICE_UNAVAILABLE` | 503 | D1/KV not configured |

---

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `SERVICE_TOKEN` | Encryption key for BYOK + admin auth | Yes (for BYOK) |
| `POLAR_WEBHOOK_SECRET` | Webhook signature validation | Yes (for payments) |
| `LLM_API_KEY` | Global fallback LLM key | Optional |
| `LLM_BASE_URL` | Global fallback LLM endpoint | Optional |
| `DEFAULT_LLM_MODEL` | Default model name | Optional |
| `ENVIRONMENT` | `production` or `development` | Optional |

---

## Bindings (wrangler.toml)

```toml
[[d1_databases]]
binding = "DB"
database_name = "mekong-db"

[[kv_namespaces]]
binding = "RATE_LIMIT_KV"

[ai]
binding = "AI"
```

---

## Deployment Checklist

```bash
# 1. Build check
pnpm exec wrangler deploy --dry-run --outdir=dist

# 2. Deploy
pnpm exec wrangler deploy

# 3. Health check
curl -s https://mekong-engine.agencyos-openclaw.workers.dev/health

# 4. Smoke test (create tenant + test endpoint)
curl -X POST .../billing/tenants -H "Content-Type: application/json" -d '{"name":"test"}'
```

---

**Version:** 5.0.0 | **Repo:** [mekong-cli/packages/mekong-engine](https://github.com/longtho638-jpg/mekong-cli)
