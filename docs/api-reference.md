# Mekong Engine API Reference

> **Runtime:** Cloudflare Workers | **Framework:** Hono | **Version:** 3.2.0
>
> Base URL: `https://<your-worker>.workers.dev`

---

## Table of Contents

- [Authentication](#authentication)
- [Health & Status](#health--status)
- [PEV Engine](#pev-engine)
- [Task Management](#task-management-v1tasks)
- [Agent Execution](#agent-execution-v1agents)
- [Settings](#settings-v1settings)
- [Chat Webhooks](#chat-webhooks-v1chat)
- [Content Generation](#content-generation-v1content)
- [CRM](#crm-v1crm)
- [Reports](#reports-v1reports)
- [Onboarding](#onboarding-v1onboard)
- [Governance](#governance-v1governance)
- [Ledger](#ledger-v1ledger)
- [Equity](#equity-v1equity)
- [Billing](#billing)
- [Vietnam Payments](#vietnam-payments-payment)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)

---

## Authentication

### Bearer Token Authentication

All protected endpoints require an API key passed in the `Authorization` header:

```
Authorization: Bearer <tenant_api_key>
```

**How to get API key:**
1. Create tenant via `POST /billing/tenants`
2. API key returned once (cannot be recovered if lost)
3. Lost key? Regenerate via `POST /billing/tenants/regenerate-key`

**Middleware behavior:**
- `authMiddleware` validates key against `tenants` table
- Injects `tenant` object into request context
- Returns `401 Unauthorized` if missing/invalid

---

## Health & Status

### GET /

Service information.

**Response:**
```json
{
  "service": "mekong-engine",
  "version": "3.2.0",
  "docs": "https://docs.agencyos.network",
  "health": "/health",
  "api": "/v1"
}
```

### GET /health

Health check with database latency and active workers count.

**Response:**
```json
{
  "status": "ok",
  "version": "3.2.0",
  "uptime": 86400,
  "database": {
    "connected": true,
    "latency_ms": 12
  },
  "active_workers": 3,
  "bindings": {
    "d1": true,
    "kv": true,
    "r2": false,
    "ai": true,
    "llm": true
  }
}
```

### GET /ai/test

Test Workers AI binding.

**Response:**
```json
{
  "ok": true,
  "result": {
    "response": "Xin chào! Tôi là AI trợ lý của bạn."
  }
}
```

---

## PEV Engine

### POST /cmd

Execute Plan-Execute-Verify pipeline.

**Authentication:** Optional (BYOK: tenant key → global key → Workers AI)

**Request:**
```json
{
  "goal": "Create CRUD API for user management"
}
```

**Response:**
```json
{
  "plan": [...],
  "execution": [...],
  "verification": "passed"
}
```

---

## Task Management (`/v1/tasks`)

Mission-based async task execution with credit metering.

### POST /v1/tasks

Create new mission.

**Authentication:** Required | **Middleware:** `creditMeteringMiddleware`

**Request Schema:**
```json
{
  "goal": "string (1-2000 chars) - Mission objective"
}
```

**Credit Estimation:**
- Simple goal: 1 credit
- Standard goal: 3 credits
- Complex goal: 5 credits

**Response (201):**
```json
{
  "id": "msn_<tenant_id>_1234567890",
  "tenant_id": "tnt_abc123",
  "goal": "Send welcome email to new users",
  "status": "pending",
  "credits_used": 3,
  "created_at": "2026-03-18T10:30:00Z",
  "updated_at": "2026-03-18T10:30:00Z"
}
```

**Errors:**
- `400` - Invalid request (goal missing or too long)
- `402` - Insufficient credits
- `503` - D1 database not configured

### GET /v1/tasks

List missions with pagination.

**Query Parameters:**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | number | 20 | 100 |
| `offset` | number | 0 | - |

**Response:**
```json
{
  "missions": [
    {
      "id": "msn_...",
      "goal": "...",
      "status": "running",
      "result": null,
      "credits_used": 3,
      "created_at": "2026-03-18T10:30:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

### GET /v1/tasks/:id

Get mission by ID.

**Response:**
```json
{
  "id": "msn_...",
  "goal": "...",
  "status": "completed",
  "result": { "output": "Success" },
  "credits_used": 3,
  "created_at": "2026-03-18T10:30:00Z",
  "updated_at": "2026-03-18T10:35:00Z"
}
```

### GET /v1/tasks/:id/stream

SSE stream for real-time mission progress.

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Response:**
```
data: {"id":"msn_...","status":"running","result":null}
```

### POST /v1/tasks/:id/cancel

Cancel pending mission with credit refund.

**Response:**
```json
{
  "id": "msn_...",
  "status": "cancelled",
  "refunded": 3
}
```

**Errors:**
- `404` - Mission not found
- `409` - Only pending missions can be cancelled

---

## Agent Execution (`/v1/agents`)

Available agents: `git`, `file`, `shell`, `lead-hunter`, `content-writer`, `recipe-crawler`

### GET /v1/agents

List available agents.

**Response:**
```json
{
  "agents": [
    { "name": "git", "description": "Git operations" },
    { "name": "file", "description": "File operations" },
    { "name": "shell", "description": "Shell command execution" },
    { "name": "lead-hunter", "description": "Lead generation" },
    { "name": "content-writer", "description": "Content creation" },
    { "name": "recipe-crawler", "description": "Recipe discovery" }
  ]
}
```

### POST /v1/agents/:name/run

Execute agent by name.

**Request:**
```json
{
  "args": ["arg1", "arg2"],
  "kwargs": { "key": "value" }
}
```

**Response:**
```json
{
  "agent": "git",
  "output": "Changes committed successfully",
  "success": true
}
```

---

## Settings (`/v1/settings`)

LLM provider configuration.

### POST /v1/settings/llm

Save LLM configuration.

**Request Schema:**
```json
{
  "provider": "openai" | "google" | "anthropic" | "custom",
  "api_key": "string (min 1 char)",
  "base_url": "https://api.example.com (URL, optional)",
  "model": "gpt-4o (optional)"
}
```

**Validation:**
- `provider` must be one of the enum values
- `api_key` required
- `base_url` required if provider is `custom`

**Response:**
```json
{
  "ok": true,
  "provider": "openai",
  "message": "LLM settings saved"
}
```

### GET /v1/settings/llm

Get current configuration (API key masked).

**Response:**
```json
{
  "provider": "openai",
  "api_key": "sk-••••••••••••abcd",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o",
  "available_providers": ["openai", "google", "anthropic", "custom"]
}
```

**Default (no custom config):**
```json
{
  "provider": "workers-ai",
  "api_key": null,
  "base_url": null,
  "model": null,
  "message": "Using default Workers AI"
}
```

### DELETE /v1/settings/llm

Remove custom config, fallback to Workers AI.

**Response:**
```json
{
  "ok": true,
  "deleted": true,
  "message": "LLM settings removed, falling back to Workers AI"
}
```

---

## Chat Webhooks (`/v1/chat`)

Platform webhooks for Zalo OA and Facebook Messenger.

### POST /v1/chat/webhook/zalo

Zalo OA webhook endpoint.

**Authentication:** Zalo app secret validation

**Request:** Zalo event payload

**Response:** `200 OK`

### GET /v1/chat/webhook/facebook

Facebook Messenger webhook verification.

**Query Params:** `hub.mode`, `hub.verify_token`, `hub.challenge`

**Response:** Challenge string if verified

### POST /v1/chat/webhook/facebook

Facebook Messenger event handler.

**Authentication:** Facebook app secret validation

**Response:** `200 OK`

---

## Content Generation (`/v1/content`)

AI-generated content batches (7-14 days).

### POST /v1/content/generate

Generate content batch.

**Request:**
```json
{
  "topic": "AI automation trends",
  "days": 14,
  "platform": "facebook"
}
```

**Response (201):**
```json
{
  "posts": [
    {
      "id": "cnt_...",
      "content_text": "Post content...",
      "scheduled_at": "2026-03-19T09:00:00Z",
      "status": "draft"
    }
  ],
  "count": 14
}
```

### GET /v1/content

List content posts.

**Query Params:** `status`, `limit`, `offset`

**Response:**
```json
{
  "posts": [...],
  "count": 14
}
```

### PATCH /v1/content/:id

Update content post (approve/reject).

**Request:**
```json
{
  "status": "approved" | "rejected" | "draft"
}
```

**Response:**
```json
{
  "id": "cnt_...",
  "status": "approved",
  "updated_at": "2026-03-18T10:30:00Z"
}
```

---

## CRM (`/v1/crm`)

Contact management and remarketing campaigns.

### GET /v1/crm/contacts

List contacts with filters.

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `tag` | string | Filter by tag |
| `limit` | number | Max results (default 50, max 200) |

**Response:**
```json
{
  "contacts": [
    {
      "id": "ct_tnt_1234567890",
      "external_id": "user_zalo_123",
      "platform": "zalo",
      "name": "Nguyen Van A",
      "phone": "+84901234567",
      "email": "a@example.com",
      "tags": ["vip", "interested"],
      "visit_count": 5,
      "last_contact_at": "2026-03-18T10:30:00Z"
    }
  ],
  "count": 1
}
```

### POST /v1/crm/contacts

Create contact manually.

**Request Schema:**
```json
{
  "external_id": "string (optional)",
  "platform": "string (optional, default: zalo)",
  "name": "string (optional)",
  "phone": "string (optional)",
  "email": "string (email format, optional)",
  "tags": ["string"] (optional),
  "notes": "string (optional)"
}
```

**Response (201):**
```json
{
  "id": "ct_tnt_1234567890",
  "created": true
}
```

### POST /v1/crm/contacts/auto

Upsert contact from chat event.

**Request Schema:**
```json
{
  "external_id": "string (required)",
  "platform": "string (required)",
  "name": "string (optional)"
}
```

**Behavior:**
- If contact exists: increment `visit_count`, update `last_contact_at`
- If new: create contact

**Response:**
```json
{
  "id": "ct_tnt_1234567890",
  "upserted": "updated" | "created"
}
```

### GET /v1/crm/campaigns

List remarketing campaigns.

**Response:**
```json
{
  "campaigns": [
    {
      "id": "rc_tnt_1234567890",
      "name": "Re-engagement Campaign",
      "trigger_type": "days_since_visit",
      "trigger_value": "7",
      "message_template": "Hi {name}, come back!",
      "channel": "zalo",
      "created_at": "2026-03-18T10:30:00Z"
    }
  ]
}
```

### POST /v1/crm/campaigns

Create remarketing campaign.

**Request Schema:**
```json
{
  "name": "string (required, min 1 char)",
  "trigger_type": "days_since_visit" | "birthday" | "manual" | "tag_match",
  "trigger_value": "string (optional)",
  "message_template": "string (required)",
  "channel": "string (optional, default: zalo)"
}
```

**Response (201):**
```json
{
  "id": "rc_tnt_1234567890",
  "created": true
}
```

---

## Reports (`/v1/reports`)

AI-generated reports.

### GET /v1/reports/weekly

Weekly summary report.

**Query Params:** `week` (ISO week, e.g., `2026-W11`)

**Response:**
```json
{
  "week": "2026-W11",
  "summary": "Tuần này bạn có 15 contact mới, 3 chiến dịch đã gửi...",
  "metrics": {
    "new_contacts": 15,
    "campaigns_sent": 3,
    "content_published": 7
  }
}
```

### GET /v1/reports/overview

Business overview report.

**Response:**
```json
{
  "tenant_id": "tnt_abc",
  "period": "last_30_days",
  "summary": "Tổng quan 30 ngày qua...",
  "metrics": {
    "total_contacts": 150,
    "total_campaigns": 12,
    "credit_balance": 45
  }
}
```

---

## Onboarding (`/v1/onboard`)

4-step onboarding flow.

### GET /v1/onboard/status

Check onboarding status.

**Response:**
```json
{
  "completed": false,
  "steps": {
    "profile": false,
    "channel": false,
    "menu": false,
    "activate": false
  }
}
```

### POST /v1/onboard/profile

Submit company profile.

**Request:**
```json
{
  "company_name": "ABC Company",
  "industry": "retail",
  "size": "10-50"
}
```

**Response:**
```json
{
  "ok": true,
  "faq_generated": true
}
```

### POST /v1/onboard/channel

Connect messaging channel.

**Request:**
```json
{
  "platform": "facebook" | "zalo",
  "credentials": { ... }
}
```

**Response:**
```json
{
  "ok": true,
  "channel_id": "chn_..."
}
```

### POST /v1/onboard/menu

Setup FAQ menu.

**Response:**
```json
{
  "ok": true,
  "menu_items": 5
}
```

### POST /v1/onboard/activate

Activate tenant.

**Response:**
```json
{
  "ok": true,
  "activated": true
}
```

---

## Governance (`/v1/governance`)

Quadratic voting and stakeholder management.

### GET /v1/governance/stakeholders

List stakeholders.

**Response:**
```json
{
  "stakeholders": [
    {
      "id": "stk_...",
      "name": "Nguyen Van A",
      "role": "founder",
      "credits": 1000,
      "reputation": 850
    }
  ]
}
```

### POST /v1/governance/proposals

Create proposal.

**Request:**
```json
{
  "title": "Upgrade to Pro plan",
  "description": "提议 nội dung...",
  "credits_requested": 500
}
```

**Response (201):**
```json
{
  "id": "prp_...",
  "status": "voting"
}
```

### POST /v1/governance/vote

Cast vote (quadratic: votes = √credits_spent).

**Request:**
```json
{
  "proposal_id": "prp_...",
  "support": true,
  "credits_to_spend": 100
}
```

**Response:**
```json
{
  "votes_cast": 10,
  "remaining_credits": 900
}
```

### GET /v1/governance/reputation

Get stakeholder reputation.

**Response:**
```json
{
  "stakeholder_id": "stk_...",
  "reputation": 850,
  "level": "elder"
}
```

### GET /v1/governance/ngu-su

Ngũ Sự analysis (Đạo-Thiên-Địa-Tướng-Pháp).

**Response:**
```json
{
  "dao": 8.5,
  "thien": 7.0,
  "dia": 9.0,
  "tuong": 8.0,
  "phap": 7.5,
  "overall": 8.0
}
```

### GET /v1/governance/treasury

Treasury balance.

**Response:**
```json
{
  "total_credits": 50000,
  "allocated": 12000,
  "available": 38000
}
```

---

## Ledger (`/v1/ledger`)

Double-entry accounting system.

### POST /v1/ledger/transfer

Transfer credits between accounts.

**Request:**
```json
{
  "from_account": "acc_...",
  "to_account": "acc_...",
  "amount": 100,
  "description": "Payment for services"
}
```

**Response:**
```json
{
  "transaction_id": "txn_...",
  "debits": [...],
  "credits": [...],
  "balanced": true
}
```

### POST /v1/ledger/topup

Add credits to account.

**Request:**
```json
{
  "account_id": "acc_...",
  "amount": 500,
  "source": "purchase"
}
```

**Response:**
```json
{
  "transaction_id": "txn_...",
  "new_balance": 1500
}
```

### GET /v1/ledger/balance

Get account balance.

**Query Params:** `account_id`

**Response:**
```json
{
  "account_id": "acc_...",
  "balance": 1500,
  "currency": "credits"
}
```

### GET /v1/ledger/history

Transaction history.

**Query Params:** `account_id`, `limit`, `offset`

**Response:**
```json
{
  "transactions": [
    {
      "id": "txn_...",
      "type": "transfer",
      "amount": 100,
      "description": "Payment for services",
      "created_at": "2026-03-18T10:30:00Z"
    }
  ]
}
```

---

## Equity (`/v1/equity`)

Cap table, SAFE notes, vesting.

### GET /v1/equity/entities

List equity entities.

**Response:**
```json
{
  "entities": [
    {
      "id": "ent_...",
      "name": "Founder",
      "type": "individual"
    }
  ]
}
```

### POST /v1/equity/grants

Create equity grant.

**Request:**
```json
{
  "entity_id": "ent_...",
  "shares": 1000,
  "vesting_months": 48,
  "cliff_months": 12
}
```

**Response (201):**
```json
{
  "id": "grt_...",
  "vested": 0,
  "vesting_start": "2026-03-18"
}
```

### GET /v1/equity/cap-table

Compute cap table.

**Response:**
```json
{
  "total_shares": 10000,
  "holders": [
    {
      "entity": "Founder",
      "shares": 5000,
      "percentage": 50.0,
      "vested": 4500
    }
  ]
}
```

### POST /v1/equity/safe

Create SAFE note.

**Request:**
```json
{
  "investor": "Investor ABC",
  "amount": 100000,
  "valuation_cap": 5000000
}
```

**Response (201):**
```json
{
  "id": "safe_...",
  "shares_on_conversion": 2000
}
```

### POST /v1/equity/safe/convert

Convert SAFE to equity.

**Request:**
```json
{
  "safe_id": "safe_...",
  "current_valuation": 10000000
}
```

**Response:**
```json
{
  "shares_issued": 2000,
  "conversion_price": 50
}
```

---

## Billing

### POST /billing/tenants

Create tenant (returns API key one-time).

**Request:**
```json
{
  "name": "ABC Company"
}
```

**Response (201):**
```json
{
  "tenant_id": "tnt_abc123",
  "name": "ABC Company",
  "api_key": "sk_live_abc123xyz789",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

### POST /billing/tenants/regenerate-key

Regenerate API key.

**Request:**
```json
{
  "tenant_id": "tnt_abc123",
  "name": "ABC Company"
}
```

**Response:**
```json
{
  "api_key": "sk_live_newkey456",
  "message": "New API key generated. Old key is now invalid. Save this key!"
}
```

### POST /billing/webhook

Polar.sh webhook handler.

**Headers:**
```
webhook-signature: <HMAC-SHA256>
```

**Events:** `order.paid`, `subscription.canceled`

**Response:**
```json
{
  "received": true
}
```

### GET /billing/pricing

Public pricing info.

**Response:**
```json
{
  "tiers": [
    { "id": "free", "name": "Free", "price": 0, "credits": 10 },
    { "id": "agencyos-starter", "name": "Starter", "price": 29, "credits": 50 },
    { "id": "agencyos-pro", "name": "Pro", "price": 99, "credits": 200 },
    { "id": "agencyos-agency", "name": "Agency", "price": 199, "credits": 500 },
    { "id": "agencyos-master", "name": "Master", "price": 399, "credits": 1000 }
  ],
  "credit_packs": [
    { "id": "credits-10", "credits": 10, "price": 5 },
    { "id": "credits-50", "credits": 50, "price": 20 },
    { "id": "credits-100", "credits": 100, "price": 35 }
  ],
  "credit_costs": {
    "simple": 1,
    "standard": 3,
    "complex": 5
  }
}
```

### GET /billing/credits

Get credit balance.

**Authentication:** Required

**Response:**
```json
{
  "tenant_id": "tnt_abc123",
  "balance": 45,
  "tier": "pro"
}
```

### GET /billing/credits/history

Credit transaction history.

**Query Params:** `limit` (default 50, max 200)

**Response:**
```json
{
  "tenant_id": "tnt_abc123",
  "history": [
    {
      "id": "crd_...",
      "type": "purchase",
      "amount": 50,
      "balance_after": 100,
      "description": "Polar.sh: agencyos-starter (50 credits)",
      "created_at": "2026-03-18T10:30:00Z"
    }
  ],
  "limit": 50
}
```

---

## Vietnam Payments (`/payment`)

### POST /payment/create

Create Vietnam payment (MoMo/VNPay).

**Request:**
```json
{
  "provider": "momo" | "vnpay",
  "amount": 500000,
  "order_id": "ord_123456"
}
```

**Response:**
```json
{
  "payment_url": "https://payment.momo.vn/...",
  "order_id": "ord_123456"
}
```

### POST /payment/momo/ipn

MoMo IPN webhook.

**Request:** MoMo callback payload

**Response:**
```json
{
  "received": true
}
```

### GET /payment/vnpay/ipn

VNPay IPN webhook.

**Query Params:** VNPay callback params

**Response:**
```json
{
  "received": true
}
```

### GET /payment/pricing-vn

Vietnam pricing (VND).

**Response:**
```json
{
  "tiers_vnd": [
    { "id": "free", "name": "Miễn phí", "price": 0, "credits": 10 },
    { "id": "starter", "name": "Khởi đầu", "price": 690000, "credits": 50 },
    { "id": "pro", "name": "Chuyên nghiệp", "price": 2390000, "credits": 200 },
    { "id": "agency", "name": "Agency", "price": 4790000, "credits": 500 },
    { "id": "master", "name": "Master", "price": 9590000, "credits": 1000 }
  ]
}
```

---

## Rate Limits

| Tier | Requests/min | Credits/day |
|------|--------------|-------------|
| free | 10 | 10 |
| pro | 60 | 100 |
| enterprise | 300 | 1000 |

**Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1710756000
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing API key |
| 402 | Payment Required - Insufficient credits |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - State conflict (e.g., cancel non-pending mission) |
| 503 | Service Unavailable - D1/KV not configured |

---

## SDK Examples

### JavaScript/TypeScript

```typescript
import { MekongClient } from '@mekong/cli-core'

const client = new MekongClient({
  baseUrl: 'https://your-worker.workers.dev',
  apiKey: 'sk_live_...'
})

// Create mission
const mission = await client.tasks.create({
  goal: 'Send welcome emails'
})

// Stream progress
const stream = client.tasks.stream(mission.id)
for await (const event of stream) {
  console.log(event.status)
}
```

### cURL

```bash
# Create tenant
curl -X POST https://your-worker.workers.dev/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"My Company"}'

# Create mission
curl -X POST https://your-worker.workers.dev/v1/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_..." \
  -d '{"goal":"Generate weekly report"}'

# Get credit balance
curl -X GET https://your-worker.workers.dev/billing/credits \
  -H "Authorization: Bearer sk_live_..."
```

---

## Database Schema

### Core Tables

```sql
tenants (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  api_key_hash TEXT NOT NULL,
  tier TEXT DEFAULT 'free',
  created_at TEXT
)

contacts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  external_id TEXT,
  platform TEXT,
  name TEXT,
  phone TEXT,
  email TEXT,
  tags TEXT, -- JSON array
  visit_count INTEGER DEFAULT 1,
  last_contact_at TEXT
)

missions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  goal TEXT NOT NULL,
  status TEXT, -- pending, running, completed, failed
  result TEXT, -- JSON
  credits_used INTEGER,
  created_at TEXT,
  updated_at TEXT
)

credit_transactions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  amount INTEGER,
  balance_after INTEGER,
  type TEXT,
  description TEXT,
  created_at TEXT
)

proposals (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  title TEXT,
  description TEXT,
  credits_requested INTEGER,
  status TEXT,
  votes_for INTEGER,
  votes_against INTEGER,
  created_at TEXT
)
```
