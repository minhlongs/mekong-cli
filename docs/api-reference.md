# Mekong Engine API Reference

> **Runtime:** Cloudflare Workers | **Framework:** Hono | **Version:** 3.2.0
>
> **Base URL:** `https://<your-worker>.workers.dev`
>
> **Status:** Production Ready | **Last Updated:** 2026-03-19

---

## Table of Contents

- [Authentication](#authentication)
- [Health & Status](#health--status)
- [Route Groups](#route-groups)
  - [1. /billing](#1-billing)
  - [2. /payment](#2-payment-vietnam-payments)
  - [3. /v1/tasks](#3-v1tasks)
  - [4. /v1/agents](#4-v1agents)
  - [5. /v1/chat](#5-v1chat)
  - [6. /v1/content](#6-v1content)
  - [7. /v1/crm](#7-v1crm)
  - [8. /v1/reports](#8-v1reports)
  - [9. /v1/onboard](#9-v1onboard)
  - [10. /v1/settings](#10-v1settings)
  - [11. /v1/governance](#11-v1governance)
  - [12. /v1/ledger](#12-v1ledger)
  - [13. /v1/equity](#13-v1equity)
  - [14. /v1/revenue](#14-v1revenue)
  - [15. /v1/funding](#15-v1funding)
- [Rate Limits](#rate-limits)
- [Error Codes](#error-codes)
- [Database Schema](#database-schema)
- [SDK Examples](#sdk-examples)

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

**Middleware behaviors:**
| Middleware | Purpose | Routes |
|------------|---------|--------|
| `authMiddleware` | Validates API key against `tenants` table | All protected routes |
| `creditMeteringMiddleware` | Estimates + deducts credits before execution | `POST /v1/tasks` |

---

## Health & Status

### GET /

**Purpose:** Service information and discovery.

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

**Purpose:** Health check with database latency and binding status.

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

---

## Route Groups

## 1. /billing

**Purpose:** Tenant management, credit billing, and Polar.sh payment integration.

**Base Path:** `/billing`

**Authentication:** Mixed (public endpoints for pricing/tenant creation, protected for credit operations)

### Endpoints

#### POST /billing/tenants

**Purpose:** Create new tenant (returns API key one-time).

**Authentication:** None (public)

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | 1-255 chars |

**Request Example:**
```json
{ "name": "ABC Company" }
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

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Missing or invalid name |
| 503 | D1 database not configured |

---

#### POST /billing/tenants/regenerate-key

**Purpose:** Regenerate API key for existing tenant.

**Authentication:** None (uses tenant_id + name as proof)

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `tenant_id` | string (UUID) | Yes |
| `name` | string | Yes |

**Response:**
```json
{
  "api_key": "sk_live_newkey456",
  "message": "New API key generated. Old key is now invalid. Save this key!"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | Tenant not found or name mismatch |

---

#### POST /billing/webhook

**Purpose:** Polar.sh webhook handler for payment events.

**Authentication:** HMAC-SHA256 signature via `webhook-signature` header

**Headers:**
| Header | Purpose |
|--------|---------|
| `webhook-signature` | HMAC-SHA256 of raw body using `POLAR_WEBHOOK_SECRET` |

**Supported Events:**
| Event | Action |
|-------|--------|
| `order.paid` | Add credits, upgrade tier if subscription |
| `subscription.canceled` | Downgrade tier to `free` |

**Security:** 5-minute timestamp window to prevent replay attacks.

**Response:**
```json
{ "received": true }
```

---

#### GET /billing/pricing

**Purpose:** Public pricing tiers and credit packs.

**Authentication:** None (public)

**Response:**
```json
{
  "tiers": [
    { "id": "free", "name": "Free", "price": 0, "credits": 10, "description": "Try it out" },
    { "id": "agencyos-starter", "name": "Starter", "price": 29, "credits": 50, "description": "Solo non-tech user" },
    { "id": "agencyos-pro", "name": "Pro", "price": 99, "credits": 200, "description": "Small agency" },
    { "id": "agencyos-agency", "name": "Agency", "price": 199, "credits": 500, "description": "Growing agency" },
    { "id": "agencyos-master", "name": "Master", "price": 399, "credits": 1000, "description": "Premium agency" }
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

---

#### GET /billing/credits

**Purpose:** Get current credit balance.

**Authentication:** Required

**Response:**
```json
{
  "tenant_id": "tnt_abc123",
  "balance": 45,
  "tier": "pro"
}
```

---

#### GET /billing/credits/history

**Purpose:** Credit transaction history.

**Authentication:** Required

**Query Parameters:**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | number | 50 | 200 |

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

## 2. /payment (Vietnam Payments)

**Purpose:** MoMo and VNPay payment gateway integration for VND transactions.

**Base Path:** `/payment`

**Authentication:** None for webhook endpoints; HMAC signature validation

### Endpoints

#### POST /payment/create

**Purpose:** Create payment URL for MoMo or VNPay.

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `method` | string | Yes | `momo`, `vnpay` |
| `tenant_id` | string (UUID) | Yes | - |
| `plan` | string | Optional | `starter`, `pro`, `enterprise` |
| `amount` | number | Yes | VND amount |
| `credits` | number | Yes | Credits to add |

**Response:**
```json
{
  "method": "momo",
  "order_id": "tnt_abc-1710849600000",
  "amount": 199000,
  "payment_url": "https://payment.momo.vn/pay?partnerCode=MEKONG&orderId=...&extraData=...",
  "note": "Mock URL — replace with real MoMo API integration"
}
```

---

#### POST /payment/momo/ipn

**Purpose:** MoMo Instant Payment Notification webhook.

**Authentication:** HMAC-SHA256 via `x-signature` or `x-momo-signature` header

**Request Headers:**
| Header | Purpose |
|--------|---------|
| `x-signature` or `x-momo-signature` | HMAC-SHA256 of raw body |

**Request Body (MoMo payload):**
| Field | Type |
|-------|------|
| `partnerCode` | string |
| `orderId` | string |
| `amount` | number |
| `resultCode` | number (0 = success) |
| `extraData` | string (base64 JSON: `{tenant_id, credits, plan}`) |

**Response (200):**
```json
{
  "received": true,
  "tenant_id": "tnt_abc123",
  "credits_added": 50
}
```

---

#### GET /payment/vnpay/ipn

**Purpose:** VNPay IPN webhook handler.

**Authentication:** HMAC-SHA512 via `vnp_SecureHash` query param

**Query Parameters:**
| Param | Purpose |
|-------|---------|
| `vnp_ResponseCode` | `00` = success |
| `vnp_OrderInfo` | Format: `tenant_id|credits|plan` |
| `vnp_TxnRef` | Transaction reference |
| `vnp_Amount` | Amount * 100 |
| `vnp_SecureHash` | HMAC-SHA512 signature |

**Response:**
```json
{ "received": true, "tenant_id": "tnt_abc123", "credits_added": 50 }
```

---

#### GET /payment/pricing-vn

**Purpose:** Vietnam pricing tiers in VND.

**Response:**
```json
{
  "tiers": [
    { "id": "free", "name": "Miễn phí", "price_vnd": 0, "credits": 10 },
    { "id": "starter", "name": "Starter", "price_vnd": 199000, "credits": 50 },
    { "id": "pro", "name": "Pro", "price_vnd": 499000, "credits": 200 },
    { "id": "enterprise", "name": "Enterprise", "price_vnd": 2990000, "credits": 1000 }
  ]
}
```

---

## 3. /v1/tasks

**Purpose:** Mission-based async task execution with credit metering.

**Base Path:** `/v1/tasks`

**Authentication:** Required

**Middleware:** `creditMeteringMiddleware` (auto-deducts credits)

### Endpoints

#### POST /v1/tasks

**Purpose:** Create new mission.

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `goal` | string | Yes | 1-2000 chars |

**Credit Estimation:**
| Goal Type | Credits | Examples |
|-----------|---------|----------|
| Simple | 1 | "Send email", "List contacts" |
| Standard | 3 | "Generate weekly report", "Create content batch" |
| Complex | 5 | "Build CRUD API", "Full onboarding flow" |

**Response (201):**
```json
{
  "id": "msn_tnt_abc_1710849600",
  "tenant_id": "tnt_abc123",
  "goal": "Send welcome email to new users",
  "status": "pending",
  "credits_used": 3,
  "created_at": "2026-03-18T10:30:00Z",
  "updated_at": "2026-03-18T10:30:00Z"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Invalid goal (missing/too long) |
| 402 | Insufficient credits |
| 503 | D1 not configured |

---

#### GET /v1/tasks

**Purpose:** List missions with pagination.

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

---

#### GET /v1/tasks/:id

**Purpose:** Get mission by ID.

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

---

#### GET /v1/tasks/:id/stream

**Purpose:** SSE stream for real-time mission progress.

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Stream Events:**
```
data: {"id":"msn_...","status":"running","result":null}
```

---

#### POST /v1/tasks/:id/cancel

**Purpose:** Cancel pending mission with credit refund.

**Response:**
```json
{
  "id": "msn_...",
  "status": "cancelled",
  "refunded": 3
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | Mission not found |
| 409 | Only pending missions can be cancelled |

---

## 4. /v1/agents

**Purpose:** Agent execution and discovery.

**Base Path:** `/v1/agents`

**Authentication:** Required for `POST /:name/run`

### Available Agents

| Agent | Description |
|-------|-------------|
| `git` | Git operations: status, diff, log, commit, branch |
| `file` | File operations: find, read, tree, stats, grep |
| `shell` | Shell command execution |
| `lead-hunter` | Company and CEO lead discovery |
| `content-writer` | Content generation |
| `recipe-crawler` | Recipe file discovery |

### Endpoints

#### GET /v1/agents

**Purpose:** List available agents.

**Response:**
```json
{
  "agents": [
    { "name": "git", "description": "Git operations: status, diff, log, commit, branch" },
    { "name": "file", "description": "File operations: find, read, tree, stats, grep" },
    { "name": "shell", "description": "Shell command execution" },
    { "name": "lead-hunter", "description": "Company and CEO lead discovery" },
    { "name": "content-writer", "description": "Content generation" },
    { "name": "recipe-crawler", "description": "Recipe file discovery" }
  ]
}
```

---

#### POST /v1/agents/:name/run

**Purpose:** Execute agent by name.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `command` | string | Yes |
| `params` | object | Optional |

**Response (202):**
```json
{
  "agent": "git",
  "command": "status",
  "status": "accepted",
  "message": "Agent execution queued — use /v1/tasks to track progress"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | Agent not found |
| 400 | Missing command |

---

## 5. /v1/chat

**Purpose:** Zalo OA and Facebook Messenger webhook handlers.

**Base Path:** `/v1/chat`

**Authentication:** Platform-specific signature validation

### Endpoints

#### POST /v1/chat/webhook/zalo

**Purpose:** Zalo OA message webhook.

**Authentication:** HMAC-SHA256 via `x-zalo-signature` header

**Request Headers:**
| Header | Purpose |
|--------|---------|
| `x-zalo-signature` or `x-signature` | HMAC-SHA256 signature |

**Request Body (Zalo event):**
| Field | Type |
|-------|------|
| `event_name` | string (e.g., `user_send_text`) |
| `app_id` | string |
| `sender.id` | string |
| `recipient.id` | string |
| `message.text` | string |
| `message.msg_id` | string |
| `timestamp` | string |

**Response:**
```json
{ "received": true }
```

---

#### GET /v1/chat/webhook/facebook

**Purpose:** Facebook Messenger webhook verification.

**Query Parameters:**
| Param | Purpose |
|-------|---------|
| `hub.mode` | Must be `subscribe` |
| `hub.verify_token` | Must match `FB_VERIFY_TOKEN` |
| `hub.challenge` | String to return |

**Response:** Challenge string (200) or Forbidden (403)

---

#### POST /v1/chat/webhook/facebook

**Purpose:** Facebook Messenger event handler.

**Authentication:** HMAC-SHA256 via `X-Hub-Signature-256` header

**Response:**
```json
{ "received": true }
```

---

## 6. /v1/content

**Purpose:** AI-generated content batches for social media.

**Base Path:** `/v1/content`

**Authentication:** Required

### Endpoints

#### POST /v1/content/generate

**Purpose:** Generate 7-14 day content batch via LLM.

**Request Body:**
| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `channel` | string | `facebook` | - |
| `days` | number | 7 | 7-14 |
| `industry` | string | `cafe` | - |
| `topic` | string | `daily promotions` | - |

**Response (201):**
```json
{
  "generated": 14,
  "ids": ["cp_tnt_abc_1710849600_1", "cp_tnt_abc_1710849600_2"]
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 502 | LLM generation failed |
| 503 | D1 not configured |

---

#### GET /v1/content

**Purpose:** List content posts.

**Query Parameters:**
| Param | Type | Values |
|-------|------|--------|
| `status` | string | `draft`, `approved`, `scheduled`, `rejected` |
| `limit` | number | Max 100 |

**Response:**
```json
{
  "posts": [
    {
      "id": "cp_...",
      "tenant_id": "tnt_abc",
      "channel": "facebook",
      "content_text": "Post content with emojis...",
      "image_prompt": "...",
      "status": "draft",
      "scheduled_at": "2026-03-19T09:00:00Z",
      "created_at": "2026-03-18T10:30:00Z"
    }
  ],
  "count": 14
}
```

---

#### PATCH /v1/content/:id

**Purpose:** Update content post (approve/reject/edit).

**Request Body:**
| Field | Type | Values |
|-------|------|--------|
| `status` | string | `approved`, `rejected`, `scheduled`, `draft` |
| `content_text` | string | Updated content |
| `scheduled_at` | string (ISO) | New schedule time |

**Response:**
```json
{ "updated": true }
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | Post not found |
| 400 | No fields to update |

---

## 7. /v1/crm

**Purpose:** Contact management and remarketing campaigns.

**Base Path:** `/v1/crm`

**Authentication:** Required

### Endpoints

#### GET /v1/crm/contacts

**Purpose:** List contacts with filters.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `tag` | string | Filter by tag |
| `limit` | number | Max 200, default 50 |

**Response:**
```json
{
  "contacts": [
    {
      "id": "ct_tnt_abc_1710849600",
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

---

#### POST /v1/crm/contacts

**Purpose:** Create contact manually.

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `external_id` | string | No | - |
| `platform` | string | No | Default: `zalo` |
| `name` | string | No | - |
| `phone` | string | No | - |
| `email` | string | No | Email format |
| `tags` | string[] | No | - |
| `notes` | string | No | - |

**Response (201):**
```json
{ "id": "ct_tnt_abc_1710849600", "created": true }
```

---

#### POST /v1/crm/contacts/auto

**Purpose:** Upsert contact from chat event.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `external_id` | string | Yes |
| `platform` | string | Yes |
| `name` | string | No |

**Behavior:**
- If exists: increment `visit_count`, update `last_contact_at`
- If new: create contact

**Response:**
```json
{ "id": "ct_tnt_abc_1710849600", "upserted": "created" }
```

---

#### GET /v1/crm/campaigns

**Purpose:** List remarketing campaigns.

**Response:**
```json
{
  "campaigns": [
    {
      "id": "rc_tnt_abc_1710849600",
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

---

#### POST /v1/crm/campaigns

**Purpose:** Create remarketing campaign.

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `name` | string | Yes | Min 1 char |
| `trigger_type` | string | Yes | `days_since_visit`, `birthday`, `manual`, `tag_match` |
| `trigger_value` | string | No | - |
| `message_template` | string | Yes | - |
| `channel` | string | No | Default: `zalo` |

**Response (201):**
```json
{ "id": "rc_tnt_abc_1710849600", "created": true }
```

---

## 8. /v1/reports

**Purpose:** AI-generated analytics and business reports.

**Base Path:** `/v1/reports`

**Authentication:** Required

### Endpoints

#### GET /v1/reports/weekly

**Purpose:** 7-day summary with AI-generated insights.

**Query Parameters:**
| Param | Type | Example |
|-------|------|---------|
| `week` | string | `2026-W11` (ISO week) |

**Response:**
```json
{
  "period": "7d",
  "stats": {
    "messages": 150,
    "new_contacts": 25,
    "conversations": 45,
    "content": [{ "status": "draft", "count": 7 }]
  },
  "ai_summary": "Tuần này bạn có 150 tin nhắn, 25 contact mới..."
}
```

---

#### GET /v1/reports/overview

**Purpose:** Real-time dashboard metrics (today).

**Response:**
```json
{
  "today_messages": 45,
  "total_contacts": 150,
  "pending_content": 12,
  "active_conversations": 8
}
```

---

## 9. /v1/onboard

**Purpose:** 4-step tenant onboarding flow.

**Base Path:** `/v1/onboard`

**Authentication:** Required

### Onboarding Steps

| Step | Endpoint | Purpose |
|------|----------|---------|
| 1 | POST /profile | Business info |
| 2 | POST /channel | Connect Zalo/FB |
| 3 | POST /menu | Upload menu + generate FAQ |
| 4 | POST /activate | Complete onboarding |

### Endpoints

#### GET /v1/onboard/status

**Purpose:** Check onboarding progress.

**Response:**
```json
{
  "step": 2,
  "completed": false,
  "steps": ["profile", "channel", "menu", "activate"]
}
```

---

#### POST /v1/onboard/profile

**Purpose:** Submit company profile (Step 1).

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `business_name` | string | Yes |
| `industry` | string | No |
| `address` | string | No |
| `phone` | string | No |
| `hours` | string | No |
| `logo_url` | string | No |

**Response:**
```json
{ "step": 1, "next": "channel" }
```

---

#### POST /v1/onboard/channel

**Purpose:** Connect messaging channel (Step 2).

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `type` | string | Yes | `zalo_oa`, `facebook_page` |
| `external_id` | string | Yes | Channel/page ID |
| `access_token` | string | No | OAuth token |
| `name` | string | No | Channel name |

**Response:**
```json
{ "step": 2, "channel_id": "ch_tnt_abc_zalo_oa", "next": "menu" }
```

---

#### POST /v1/onboard/menu

**Purpose:** Store menu + auto-generate FAQ (Step 3).

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `menu_data` | object | Yes |

**Response:**
```json
{ "step": 3, "faq_generated": 5, "next": "activate" }
```

---

#### POST /v1/onboard/activate

**Purpose:** Complete onboarding (Step 4).

**Response:**
```json
{ "step": 4, "completed": true, "message": "Onboarding complete. System is active." }
```

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Steps 1-3 not completed |

---

## 10. /v1/settings

**Purpose:** LLM provider configuration.

**Base Path:** `/v1/settings`

**Authentication:** Required

**Available Providers:** `openai`, `google`, `anthropic`, `custom`, `workers-ai` (default)

### Endpoints

#### POST /v1/settings/llm

**Purpose:** Save LLM configuration.

**Request Body:**
| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `provider` | string | Yes | Enum: `openai`, `google`, `anthropic`, `custom` |
| `api_key` | string | Yes | Min 1 char |
| `base_url` | string | No | URL format (required if `custom`) |
| `model` | string | No | - |

**Response:**
```json
{ "ok": true, "provider": "openai", "message": "LLM settings saved" }
```

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Invalid provider, missing base_url for custom |
| 503 | D1 or SERVICE_TOKEN not configured |

---

#### GET /v1/settings/llm

**Purpose:** Get current configuration (API key masked).

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

---

#### DELETE /v1/settings/llm

**Purpose:** Remove custom config, fallback to Workers AI.

**Response:**
```json
{ "ok": true, "deleted": true, "message": "LLM settings removed, falling back to Workers AI" }
```

---

## 11. /v1/governance

**Purpose:** Quadratic voting, stakeholder management, reputation system, and Ngũ Sự analysis.

**Base Path:** `/v1/governance`

**Authentication:** Required

### Stakeholder Roles & Voice Credits

| Role | Level | Monthly Voice Credits |
|------|-------|----------------------|
| `owner` | 1 | 10 |
| `admin` | 2 | 15 |
| `operator` | 3 | 20 |
| `vc_partner` | 4 | 30 |
| `founder` | 5 | 40 |
| `expert` | 5 | 50 |
| `developer` | 6 | 60 |
| `customer` | 6 | 80 |
| `community` | 6 | 100 |

### Endpoints

#### POST /v1/governance/stakeholders

**Purpose:** Register stakeholder.

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `display_name` | string | Yes | - |
| `email` | string | No | Email format |
| `role` | string | No | Default: `community` |

**Response (201):**
```json
{
  "id": "stk_abc123",
  "role": "community",
  "governance_level": 6,
  "voice_credits": 100,
  "message": "Stakeholder registered successfully"
}
```

---

#### GET /v1/governance/stakeholders

**Purpose:** List stakeholders.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `role` | string | Filter by role |

**Response:**
```json
{
  "stakeholders": [
    {
      "id": "stk_abc123",
      "display_name": "Nguyen Van A",
      "email": "a@example.com",
      "role": "founder",
      "governance_level": 5,
      "voice_credits_monthly": 40,
      "reputation_score": 850,
      "created_at": "2026-03-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

#### POST /v1/governance/proposals

**Purpose:** Create proposal.

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `author_id` | string (UUID) | Yes | - |
| `title` | string | Yes | - |
| `body` | string | Yes | - |
| `proposal_type` | string | No | `feature`, `strategic`, `constitutional`, `treasury`, `equity` |
| `voting_mechanism` | string | No | `quadratic`, `simple_majority`, `supermajority` |
| `voting_days` | number | No | 1-30, default 7 |

**Quorum Rules:**
| Proposal Type | Quorum | Mechanism |
|---------------|--------|-----------|
| `constitutional` | 75% | `supermajority` (forced) |
| Other | 10% | `quadratic` (default) |

**Response (201):**
```json
{
  "id": "prp_abc123",
  "proposal_type": "feature",
  "mechanism": "quadratic",
  "quorum": 0.10,
  "voting_ends_at": "2026-03-25T10:30:00Z",
  "message": "Proposal created successfully"
}
```

---

#### GET /v1/governance/proposals

**Purpose:** List proposals.

**Query Parameters:**
| Param | Type | Values |
|-------|------|--------|
| `status` | string | `draft`, `discussion`, `voting`, `approved`, `rejected`, `implemented` |

**Response:**
```json
{
  "proposals": [
    {
      "id": "prp_abc123",
      "title": "Upgrade to Pro plan",
      "body": "...",
      "status": "voting",
      "vote_stats": [
        { "direction": "for", "count": 5, "total_votes": 25.5 },
        { "direction": "against", "count": 2, "total_votes": 8.0 }
      ]
    }
  ]
}
```

---

#### POST /v1/governance/vote

**Purpose:** Cast quadratic vote.

**Formula:** `votes = sqrt(credits_spent)`, `cost = credits²`

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `proposal_id` | string (UUID) | Yes | - |
| `stakeholder_id` | string (UUID) | Yes | - |
| `voice_credits` | number | Yes | Positive integer |
| `direction` | string | No | `for`, `against`, `abstain` (default: `for`) |

**Example:** Spend 100 credits → 10 votes

**Response (201):**
```json
{
  "vote_id": "vote_abc123",
  "credits_spent": 100,
  "votes_cast": "10.00",
  "direction": "for",
  "message": "QV: 100 credits → 10.00 votes"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | Proposal/stakeholder not found |
| 400 | Voting period ended |
| 409 | Already voted on this proposal |

---

#### POST /v1/governance/reputation

**Purpose:** Add reputation event.

**Request Body:**
| Field | Type | Required | Values |
|-------|------|----------|--------|
| `stakeholder_id` | string (UUID) | Yes | - |
| `dimension` | string | No | `code`, `mentorship`, `governance`, `expertise`, `community`, `general` |
| `points` | number | Yes | -100 to 100 |
| `reason` | string | Yes | - |

**Response (201):**
```json
{ "added": 50, "dimension": "general" }
```

---

#### GET /v1/governance/reputation

**Purpose:** Get reputation leaderboard.

**Response:**
```json
{
  "leaderboard": [
    {
      "id": "stk_abc123",
      "display_name": "Nguyen Van A",
      "role": "founder",
      "reputation_score": 850,
      "governance_level": 5
    }
  ]
}
```

---

#### POST /v1/governance/ngu-su

**Purpose:** Score entity using Ngũ Sự framework (Đạo-Thiên-Địa-Tướng-Pháp).

**Request Body:**
| Field | Type | Required | Range |
|-------|------|----------|-------|
| `entity_name` | string | Yes | - |
| `dao` | number | Yes | 0-5 |
| `thien` | number | Yes | 0-5 |
| `dia` | number | Yes | 0-5 |
| `tuong` | number | Yes | 0-5 |
| `phap` | number | Yes | 0-5 |
| `terrain` | string | No | Auto-classified |
| `notes` | string | No | - |

**Terrain Auto-Classification:**
| Overall Score | Terrain |
|---------------|---------|
| < 1.5 | `tu_dia` (Death ground) |
| 1.5-2.5 | `vi_dia` (Hemmed-in) |
| 2.5-3.5 | `tranh_dia` (Contentious) |
| >= 3.5 | `giao_dia` (Intersecting) |

**Response (201):**
```json
{
  "id": "ns_abc123",
  "overall": "4.20",
  "terrain": "giao_dia"
}
```

---

#### GET /v1/governance/ngu-su

**Purpose:** List Ngũ Sự scores.

**Response:**
```json
{
  "scores": [
    {
      "id": "ns_abc123",
      "entity_name": "Portfolio Company A",
      "dao_score": 4,
      "thien_score": 4,
      "dia_score": 5,
      "tuong_score": 4,
      "phap_score": 4,
      "overall_score": 4.2,
      "terrain": "giao_dia",
      "scored_at": "2026-03-18T10:30:00Z"
    }
  ]
}
```

---

#### GET /v1/governance/treasury

**Purpose:** Get treasury balance.

**Response:**
```json
{
  "id": "trs_abc123",
  "tenant_id": "tnt_abc",
  "balance": 50000,
  "total_in": 75000,
  "total_out": 25000,
  "last_updated": "2026-03-18T10:30:00Z"
}
```

---

## 12. /v1/ledger

**Purpose:** Double-entry accounting system for credit transfers.

**Base Path:** `/v1/ledger`

**Authentication:** Required

### Account Types

| Type | Purpose |
|------|---------|
| `asset` | Credit balances (customers, rewards) |
| `revenue` | Income accounts |
| `expense` | Cost accounts (AI compute) |
| `equity` | Treasury, platform ownership |

### Endpoints

#### POST /v1/ledger/transfer

**Purpose:** Transfer credits between accounts (double-entry).

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `from_code` | string | Yes |
| `to_code` | string | Yes |
| `amount` | number | Yes (positive) |
| `description` | string | Yes |
| `entry_type` | string | No |
| `idempotency_key` | string | No |

**Response (201):**
```json
{
  "journal_entry_id": "je_abc123",
  "from": "customer:xyz",
  "to": "revenue:platform",
  "amount": 100
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Missing fields, insufficient balance |
| 409 | Idempotency key already processed |

---

#### POST /v1/ledger/topup

**Purpose:** Add credits to account from platform treasury.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `account_code` | string | Yes |
| `amount` | number | Yes |
| `description` | string | No |

**Response (201):**
```json
{
  "journal_entry_id": "je_abc123",
  "account": "customer:xyz",
  "credited": 500
}
```

---

#### GET /v1/ledger/balance

**Purpose:** Get account balance(s).

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `code` | string | Filter by account code |

**Response:**
```json
{
  "accounts": [
    {
      "id": "acc_abc123",
      "tenant_id": "tnt_abc",
      "owner_id": null,
      "code": "customer:xyz",
      "account_type": "asset",
      "balance": 1500,
      "created_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

---

#### GET /v1/ledger/history

**Purpose:** Transaction history.

**Query Parameters:**
| Param | Type | Default | Max |
|-------|------|---------|-----|
| `limit` | number | 30 | 100 |

**Response:**
```json
{
  "entries": [
    {
      "id": "je_abc123",
      "tenant_id": "tnt_abc",
      "description": "Revenue split",
      "entry_type": "revenue_share",
      "posted_at": "2026-03-18T10:30:00Z",
      "lines": "acc_1:100:1,acc_2:100:-1"
    }
  ]
}
```

---

## 13. /v1/equity

**Purpose:** Cap table management, equity grants, and SAFE notes.

**Base Path:** `/v1/equity`

**Authentication:** Required

### Endpoints

#### POST /v1/equity/entities

**Purpose:** Create equity entity (portfolio company).

**Request Body:**
| Field | Type | Default |
|-------|------|---------|
| `name` | string | - |
| `entity_type` | string | `portfolio_company` |
| `total_shares` | number | 10,000,000 |
| `jurisdiction` | string | `VN` |

**Response (201):**
```json
{
  "id": "ent_abc123",
  "share_class_id": "sc_abc123"
}
```

**Note:** Auto-creates Common share class.

---

#### GET /v1/equity/entities

**Purpose:** List equity entities.

**Response:**
```json
{
  "entities": [
    {
      "id": "ent_abc123",
      "tenant_id": "tnt_abc",
      "name": "Portfolio Company A",
      "entity_type": "portfolio_company",
      "total_authorized_shares": 10000000,
      "jurisdiction": "VN",
      "created_at": "2026-03-01T00:00:00Z"
    }
  ]
}
```

---

#### POST /v1/equity/grants

**Purpose:** Create equity grant.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `entity_id` | string (UUID) | Yes |
| `stakeholder_id` | string (UUID) | Yes |
| `share_class_id` | string (UUID) | Yes |
| `shares` | number | Yes |
| `price_per_share` | number | No |
| `grant_type` | string | No |
| `vesting_months` | number | No |
| `cliff_months` | number | No |

**Response (201):**
```json
{
  "id": "grt_abc123",
  "shares": 1000,
  "vesting_months": 48
}
```

---

#### GET /v1/equity/cap-table/:entityId

**Purpose:** Compute cap table for entity.

**Response:**
```json
{
  "entity": { "name": "Portfolio Company A", "total_authorized": 10000000 },
  "total_outstanding": 5000000,
  "dilution_pct": "50.00",
  "holders": [
    {
      "stakeholder_id": "stk_abc123",
      "display_name": "Founder",
      "role": "founder",
      "share_class": "Common",
      "total_granted": 5000000,
      "total_cancelled": 0
    }
  ],
  "vesting_schedule": [
    {
      "id": "grt_abc123",
      "shares": 1000000,
      "vested_shares": 250000,
      "vested_pct": 25
    }
  ],
  "safe_notes": [
    {
      "id": "safe_abc123",
      "investor_stakeholder_id": "stk_investor",
      "display_name": "Investor ABC",
      "principal_amount": 100000,
      "valuation_cap": 5000000,
      "status": "outstanding"
    }
  ]
}
```

---

#### POST /v1/equity/safe

**Purpose:** Create SAFE note.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `entity_id` | string (UUID) | Yes |
| `investor_stakeholder_id` | string (UUID) | Yes |
| `principal_amount` | number | Yes |
| `valuation_cap` | number | No |
| `discount_rate` | number | No |

**Response (201):**
```json
{ "id": "safe_abc123", "status": "outstanding" }
```

---

#### POST /v1/equity/safe/:id/convert

**Purpose:** Convert SAFE to equity.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `price_per_share` | number | Yes |
| `share_class_id` | string (UUID) | Yes |

**Conversion Formula:**
```
effective_price = price_per_share * (1 - discount_rate)
shares = principal / effective_price

If valuation_cap:
  cap_shares = principal / (valuation_cap / total_authorized)
  shares = max(shares, cap_shares)
```

**Response:**
```json
{
  "grant_id": "grt_abc123",
  "shares_converted": 2000,
  "effective_price": "0.0500"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 404 | SAFE not found or already converted |

---

## 14. /v1/revenue

**Purpose:** 6-way revenue distribution via double-entry ledger.

**Base Path:** `/v1/revenue`

**Authentication:** Required

### Default Revenue Split (Tam Giác Ngược)

| Recipient | Percentage | Account Code |
|-----------|------------|--------------|
| Platform | 20% | `revenue:platform` |
| Expert | 30% | `revenue:expert` |
| AI Compute | 15% | `expense:ai_compute` |
| Developer | 15% | `revenue:developer` |
| Community Fund | 10% | `treasury:community` |
| Customer Reward | 10% | `customer:rewards` |

### Endpoints

#### POST /v1/revenue/split

**Purpose:** Execute revenue split for completed task.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `total_credits` | number | Yes (positive) |
| `customer_account` | string | Yes |
| `expert_account` | string | No |
| `developer_account` | string | No |
| `description` | string | Yes |
| `split_override` | object | No |

**Response (201):**
```json
{
  "journal_entry_id": "je_abc123",
  "total": 100,
  "split": {
    "platform": 20,
    "expert": 30,
    "ai_compute": 15,
    "developer": 15,
    "community_fund": 10,
    "customer_reward": 10
  },
  "message": "Revenue split executed — 6-way distribution via double-entry ledger"
}
```

**Errors:**
| Code | Reason |
|------|--------|
| 400 | Invalid credits, insufficient balance |

---

#### GET /v1/revenue/split-config

**Purpose:** Get current split configuration.

**Response:**
```json
{
  "split": {
    "platform": 0.20,
    "expert": 0.30,
    "ai_compute": 0.15,
    "developer": 0.15,
    "community_fund": 0.10,
    "customer_reward": 0.10
  },
  "note": "Tam giác ngược: community_fund + customer_reward = 20% goes back to community"
}
```

---

#### GET /v1/revenue/summary

**Purpose:** Revenue by account.

**Response:**
```json
{
  "accounts": [
    { "code": "revenue:platform", "balance": 5000 },
    { "code": "revenue:expert", "balance": 7500 }
  ]
}
```

---

## 15. /v1/funding

**Purpose:** Quadratic funding rounds and project matching.

**Base Path:** `/v1/funding`

**Authentication:** Required

### Quadratic Funding Formula

```
For each project:
  sqrt_sum = Σ√(contribution_i)
  direct_sum = Σ(contribution_i)
  qf_score = sqrt_sum² - direct_sum

Matched amount = (qf_score / total_qf_score) * matching_pool
```

**Key Insight:** 10 people × $1 beats 1 person × $10 (democratic funding)

### Endpoints

#### POST /v1/funding/rounds

**Purpose:** Create funding round.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `title` | string | Yes |
| `matching_pool` | number | Yes |
| `duration_days` | number | No (default: 14) |

**Response (201):**
```json
{
  "id": "round_abc123",
  "matching_pool": 10000,
  "ends_at": "2026-04-01T10:30:00Z"
}
```

---

#### POST /v1/funding/projects

**Purpose:** Add project to round.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `round_id` | string (UUID) | Yes |
| `name` | string | Yes |
| `description` | string | No |
| `author_id` | string (UUID) | No |

**Response (201):**
```json
{ "id": "proj_abc123" }
```

---

#### POST /v1/funding/contribute

**Purpose:** Contribute to project.

**Request Body:**
| Field | Type | Required |
|-------|------|----------|
| `project_id` | string (UUID) | Yes |
| `stakeholder_id` | string (UUID) | Yes |
| `amount` | number | Yes |

**Response (201):**
```json
{ "id": "contrib_abc123", "amount": 100 }
```

**Errors:**
| Code | Reason |
|------|--------|
| 409 | Already contributed to this project |

---

#### POST /v1/funding/rounds/:id/calculate

**Purpose:** Calculate QF matching and distribute pool.

**Path Parameters:**
| Param | Type |
|-------|------|
| `id` | string (UUID) |

**Response:**
```json
{
  "round_id": "round_abc123",
  "matching_pool": 10000,
  "results": [
    {
      "id": "proj_1",
      "name": "Community Garden",
      "direct": 5000,
      "qf_score": 8500,
      "contributors": 50,
      "matched_amount": 6300,
      "total": 11300
    }
  ],
  "note": "QF: 10 people × $1 beats 1 person × $10 — democratic funding"
}
```

---

#### GET /v1/funding/rounds

**Purpose:** List funding rounds.

**Response:**
```json
{
  "rounds": [
    {
      "id": "round_abc123",
      "tenant_id": "tnt_abc",
      "title": "Q2 2026 Community Round",
      "matching_pool": 10000,
      "status": "completed",
      "starts_at": "2026-03-18T10:30:00Z",
      "ends_at": "2026-04-01T10:30:00Z"
    }
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

| Code | Meaning | Description |
|------|---------|-------------|
| 400 | Bad Request | Invalid input, validation failed |
| 401 | Unauthorized | Invalid/missing API key or signature |
| 402 | Payment Required | Insufficient credits |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | State conflict (e.g., cancel non-pending mission) |
| 429 | Too Many Requests | Rate limit exceeded |
| 502 | Bad Gateway | LLM generation failed |
| 503 | Service Unavailable | D1/KV not configured |

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

stakeholders (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  display_name TEXT,
  email TEXT,
  role TEXT,
  governance_level INTEGER,
  voice_credits_monthly INTEGER,
  reputation_score INTEGER DEFAULT 0
)

ledger_accounts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  owner_id TEXT,
  code TEXT,
  account_type TEXT,
  balance INTEGER DEFAULT 0
)

journal_entries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  description TEXT,
  entry_type TEXT,
  posted_at TEXT DEFAULT datetime('now')
)

transaction_lines (
  id TEXT PRIMARY KEY,
  journal_entry_id TEXT REFERENCES journal_entries(id),
  account_id TEXT REFERENCES ledger_accounts(id),
  amount INTEGER,
  direction INTEGER -- 1=credit, -1=debit
)

equity_entities (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  name TEXT,
  entity_type TEXT,
  total_authorized_shares INTEGER
)

equity_grants (
  id TEXT PRIMARY KEY,
  entity_id TEXT REFERENCES equity_entities(id),
  stakeholder_id TEXT,
  share_class_id TEXT,
  grant_type TEXT,
  shares INTEGER,
  price_per_share REAL,
  vesting_months INTEGER,
  cliff_months INTEGER,
  vesting_start_date TEXT
)

safe_notes (
  id TEXT PRIMARY KEY,
  entity_id TEXT REFERENCES equity_entities(id),
  investor_stakeholder_id TEXT,
  principal_amount INTEGER,
  valuation_cap INTEGER,
  discount_rate REAL DEFAULT 0,
  status TEXT DEFAULT 'outstanding'
)

funding_rounds (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  title TEXT,
  matching_pool INTEGER,
  status TEXT DEFAULT 'active',
  starts_at TEXT,
  ends_at TEXT
)

funding_projects (
  id TEXT PRIMARY KEY,
  round_id TEXT REFERENCES funding_rounds(id),
  tenant_id TEXT REFERENCES tenants(id),
  name TEXT,
  total_contributions INTEGER DEFAULT 0,
  contributor_count INTEGER DEFAULT 0,
  matched_amount INTEGER DEFAULT 0
)

funding_contributions (
  id TEXT PRIMARY KEY,
  project_id TEXT REFERENCES funding_projects(id),
  stakeholder_id TEXT,
  amount INTEGER,
  UNIQUE(project_id, stakeholder_id)
)

ngu_su_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT REFERENCES tenants(id),
  entity_name TEXT,
  dao_score INTEGER,
  thien_score INTEGER,
  dia_score INTEGER,
  tuong_score INTEGER,
  phap_score INTEGER,
  terrain TEXT,
  scored_at TEXT DEFAULT datetime('now')
)
```

---

## SDK Examples

### JavaScript/TypeScript

```typescript
import { MekongClient } from '@mekong/cli-core'

const client = new MekongClient({
  baseUrl: 'https://your-worker.workers.dev',
  apiKey: 'sk_live_...'
})

// Create tenant
const tenant = await client.billing.createTenant({ name: 'My Company' })
console.log('Save this key:', tenant.api_key)

// Create mission
const mission = await client.tasks.create({
  goal: 'Send welcome emails'
})

// Stream progress
const stream = client.tasks.stream(mission.id)
for await (const event of stream) {
  console.log(event.status)
}

// Governance: Create proposal
const proposal = await client.governance.createProposal({
  author_id: 'stk_...',
  title: 'Upgrade to Pro plan',
  body: 'We need more credits for scaling',
  proposal_type: 'treasury'
})

// Quadratic voting
const vote = await client.governance.vote({
  proposal_id: proposal.id,
  stakeholder_id: 'stk_...',
  voice_credits: 100, // = 10 votes (sqrt)
  direction: 'for'
})

// Equity: Create SAFE note
const safe = await client.equity.createSafe({
  entity_id: 'ent_...',
  investor_stakeholder_id: 'stk_investor',
  principal_amount: 100000,
  valuation_cap: 5000000
})

// Revenue split
const split = await client.revenue.split({
  total_credits: 100,
  customer_account: 'customer:xyz',
  description: 'Payment for service'
})

// Quadratic funding
const round = await client.funding.createRound({
  title: 'Q2 2026 Round',
  matching_pool: 10000,
  duration_days: 14
})
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

# Create stakeholder
curl -X POST https://your-worker.workers.dev/v1/governance/stakeholders \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Nguyen Van A","role":"founder"}'

# Cast quadratic vote
curl -X POST https://your-worker.workers.dev/v1/governance/vote \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{"proposal_id":"prp_...","stakeholder_id":"stk_...","voice_credits":100,"direction":"for"}'

# Create SAFE note
curl -X POST https://your-worker.workers.dev/v1/equity/safe \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{"entity_id":"ent_...","investor_stakeholder_id":"stk_...","principal_amount":100000,"valuation_cap":5000000}'

# Execute revenue split
curl -X POST https://your-worker.workers.dev/v1/revenue/split \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{"total_credits":100,"customer_account":"customer:xyz","description":"Service payment"}'

# Create funding round
curl -X POST https://your-worker.workers.dev/v1/funding/rounds \
  -H "Authorization: Bearer sk_live_..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Q2 2026","matching_pool":10000}'
```

### Python

```python
import requests

BASE_URL = 'https://your-worker.workers.dev'
API_KEY = 'sk_live_...'
headers = {'Authorization': f'Bearer {API_KEY}'}

# Create mission
response = requests.post(f'{BASE_URL}/v1/tasks', json={
    'goal': 'Generate weekly report'
}, headers=headers)
mission = response.json()

# Governance: Vote
response = requests.post(f'{BASE_URL}/v1/governance/vote', json={
    'proposal_id': 'prp_...',
    'stakeholder_id': 'stk_...',
    'voice_credits': 100,
    'direction': 'for'
}, headers=headers)
vote = response.json()
print(f"Votes cast: {vote['votes_cast']}")

# Revenue split
response = requests.post(f'{BASE_URL}/v1/revenue/split', json={
    'total_credits': 100,
    'customer_account': 'customer:xyz',
    'description': 'Service payment'
}, headers=headers)
split = response.json()
print(f"Split: {split['split']}")
```

---

## Appendix: Governance Voice Credits Reference

| Role | Level | Monthly Voice Credits | Description |
|------|-------|----------------------|-------------|
| `owner` | 1 | 10 | Servant leader (least power) |
| `admin` | 2 | 15 | Operations manager |
| `operator` | 3 | 20 | Day-to-day executor |
| `vc_partner` | 4 | 30 | Investment partner |
| `founder` | 5 | 40 | Company founder |
| `expert` | 5 | 50 | Domain expert |
| `developer` | 6 | 60 | Technical contributor |
| `customer` | 6 | 80 | Paying customer |
| `community` | 6 | 100 | Community member (most power - inverted triangle) |

---

_Last Updated: 2026-03-19_
_Version: 3.2.0_
_Maintained by: Mekong Engine Team_
