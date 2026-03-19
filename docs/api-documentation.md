# Mekong Engine API Documentation

**Version:** 5.0.0 | **License:** MIT

AI-operated business platform API with RaaS (Agent-as-a-Service) architecture.

**Base URL:** `https://api.mekong.engine` (Production) | `http://localhost:8787` (Local)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Credit System](#credit-system)
3. [Error Handling](#error-handling)
4. [API Endpoints](#api-endpoints)
   - [Tasks](#tasks)
   - [Agents](#agents)
   - [Billing](#billing)
   - [Chat](#chat)
   - [Content](#content)
   - [CRM](#crm)
   - [Settings](#settings)
   - [Reports](#reports)
   - [Onboarding](#onboarding)
   - [Payment VN](#payment-vn)
   - [Governance](#governance)
   - [Ledger](#ledger)
   - [Equity](#equity)
   - [Revenue](#revenue)
   - [Funding](#funding)
   - [Matching](#matching)
   - [Conflicts](#conflicts)
   - [Decentralization](#decentralization)
   - [RBAC](#rbac)

---

## Authentication

All API requests require **Bearer token authentication** using tenant API keys.

```http
Authorization: Bearer <tenant_api_key>
```

### Getting Your API Key

1. Create a tenant via `/v1/billing/tenants`
2. Generate API key from the tenant settings
3. Include the key in all subsequent requests

---

## Credit System

Most endpoints consume **MCU (Mission Control Unit) credits** based on operation complexity.

| Operation Type | MCU Cost |
|---------------|----------|
| Simple read | 1-5 MCU |
| Write operation | 5-15 MCU |
| Agent execution | 10-50 MCU |
| LLM generation | 20-100 MCU |

---

## API Endpoints

### Tasks

Mission execution with credit metering, SSE streaming, and lifecycle management.

**Credit Flow:**
1. `POST /v1/tasks` → `estimateCredits(goal)` → Check balance → Deduct → Create mission
2. Mission status: `pending` → `running` → `completed` | `failed`
3. Cancel pending mission → Refund credits automatically

#### `POST /v1/tasks`

Create and execute a new mission (task).

**Credit Metering:**
- Simple (< 50 chars): 10 MCU
- Standard (50-150 chars): 25 MCU
- Complex (> 150 chars): 50 MCU

**Request:**
```json
{
  "goal": "Fix authentication bug in login flow"
}
```

**Response (201 Created):**
```json
{
  "id": "msn_abc123",
  "tenant_id": "tn_xyz789",
  "goal": "Fix authentication bug in login flow",
  "status": "pending",
  "credits_used": 25,
  "total_steps": 0,
  "completed_steps": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
```json
// 402 Insufficient Credits
{ "error": "Insufficient credits", "code": "INSUFFICIENT_CREDITS" }

// 429 Rate Limited
{ "error": "Rate limit exceeded", "dailyUsed": 1000, "monthlyUsed": 5000 }
```

#### `GET /v1/tasks`

List all missions for the tenant with pagination.

**Query Parameters:**
- `limit`: Number of results (1-100, default: 20)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "missions": [
    {
      "id": "msn_abc123",
      "tenant_id": "tn_xyz789",
      "goal": "Deploy to production",
      "status": "completed",
      "credits_used": 50,
      "result": "Successfully deployed to production",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:35:00Z"
    }
  ],
  "limit": 20,
  "offset": 0
}
```

#### `GET /v1/tasks/:id`

Get mission details and execution status.

**Response:**
```json
{
  "id": "msn_abc123",
  "tenant_id": "tn_xyz789",
  "goal": "Deploy to production",
  "status": "completed",
  "credits_used": 50,
  "result": "Successfully deployed to production",
  "total_steps": 5,
  "completed_steps": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:35:00Z"
}
```

#### `GET /v1/tasks/:id/stream`

SSE (Server-Sent Events) stream for real-time mission execution updates.

**Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Event Format:**
```
event: status
data: {"id":"msn_abc123","status":"running","result":null}
```

**Example (JavaScript):**
```javascript
const stream = await fetch('https://api.mekong.engine/v1/tasks/msn_abc123/stream')
const reader = stream.body.getReader()
const decoder = new TextDecoder()

for await (const chunk of readChunks(reader)) {
  const text = decoder.decode(chunk)
  // Parse SSE events: event: status\ndata: {...}\n\n
}
```

#### `POST /v1/tasks/:id/cancel`

Cancel a pending mission and refund credits.

**Constraint:** Only `pending` missions can be cancelled.

**Response (200 OK):**
```json
{
  "id": "msn_abc123",
  "status": "cancelled",
  "refunded": 25
}
```

**Error Responses:**
```json
// 409 Conflict - Not pending
{ "error": "Only pending missions can be cancelled", "code": "CONFLICT" }

// 404 Not Found
{ "error": "Mission not found", "code": "NOT_FOUND" }
```

---

### Agents

Agent execution for git, file, shell, lead-hunter, content-writer, recipe-crawler.

Agents are executed via the PEV (Plan-Execute-Verify) orchestrator and return tasks that can be tracked via `/v1/tasks`.

#### `GET /v1/agents`

List all available agents.

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

#### `POST /v1/agents/:name/run`

Execute a specific agent with a command and optional parameters.

**Authentication:** Bearer token required

**Request:**
```json
{
  "command": "status",
  "params": {
    "path": "./src"
  }
}
```

**Response (202 Accepted):**
```json
{
  "agent": "git",
  "command": "status",
  "status": "accepted",
  "message": "Agent execution queued — use /v1/tasks to track progress"
}
```

**Error Responses:**
```json
// 404 Agent Not Found
{ "error": "Agent 'unknown-agent' not found", "code": "NOT_FOUND" }

// 400 Validation Error
{
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": [{ "field": "command", "message": "command is required" }]
}
```

**Agent Commands:**

| Agent | Commands | Example Params |
|-------|----------|----------------|
| `git` | status, diff, log, commit, branch | `{ path: "./src" }` |
| `file` | find, read, tree, stats, grep | `{ path: "./src", pattern: "*.ts" }` |
| `shell` | exec | `{ cmd: "npm install" }` |
| `lead-hunter` | discover, enrich | `{ industry: "saas", location: "US" }` |
| `content-writer` | generate, rewrite | `{ type: "blog", topic: "AI trends" }` |
| `recipe-crawler` | scan, extract | `{ path: "./recipes" }` |

---

### Billing

Tenant creation, API key management, Polar.sh webhook handling, credit balance, and pricing.

#### `POST /v1/billing/tenants`

Create a new tenant. Automatically grants 10 free welcome credits.

**Request:**
```json
{
  "name": "Acme Corporation"
}
```

**Response (201 Created):**
```json
{
  "tenant_id": "tn_abc123",
  "name": "Acme Corporation",
  "api_key": "mekong_sk_live_xyz789",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

**Important:** The API key is shown only once during creation. Store it securely.

#### `POST /v1/billing/tenants/regenerate-key`

Regenerate a lost or compromised API key. Requires tenant_id and name as ownership proof.

**Request:**
```json
{
  "tenant_id": "tn_abc123",
  "name": "Acme Corporation"
}
```

**Response (200 OK):**
```json
{
  "api_key": "mekong_sk_live_newkey456",
  "message": "New API key generated. Old key is now invalid. Save this key!"
}
```

**Error Responses:**
```json
// 404 Not Found / Name Mismatch
{ "error": "Tenant not found or name mismatch", "code": "NOT_FOUND" }
```

#### `GET /v1/billing/pricing`

Get public pricing tiers and credit packs. No authentication required.

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
  "credit_costs": { "simple": 1, "standard": 3, "complex": 5 }
}
```

#### `GET /v1/billing/credits`

Get tenant credit balance. Authentication required.

**Response:**
```json
{
  "tenant_id": "tn_abc123",
  "balance": 185,
  "tier": "pro"
}
```

#### `GET /v1/billing/credits/history`

Get credit transaction history with pagination.

**Query Parameters:**
- `limit`: Number of results (1-200, default: 50)

**Response:**
```json
{
  "tenant_id": "tn_abc123",
  "history": [
    {
      "id": "crd_abc123",
      "tenant_id": "tn_abc123",
      "amount": 200,
      "reason": "Polar.sh: agencyos-pro (200 credits)",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "crd_def456",
      "tenant_id": "tn_abc123",
      "amount": -25,
      "reason": "mission: Deploy to production",
      "created_at": "2024-01-15T11:00:00Z"
    },
    {
      "id": "crd_ghi789",
      "tenant_id": "tn_abc123",
      "amount": 10,
      "reason": "refund: cancelled mission",
      "created_at": "2024-01-15T11:05:00Z"
    }
  ],
  "limit": 50
}
```

#### `POST /v1/billing/webhook`

Handle Polar.sh payment webhooks. Verifies HMAC-SHA256 signature and 5-minute replay window.

**Headers:**
```
webhook-signature: <hmac-sha256-hex>
Content-Type: application/json
```

**Event: order.paid**
```json
{
  "type": "order.paid",
  "data": {
    "tenant_id": "tn_abc123",
    "product_name": "agencyos-pro",
    "credits": 200
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Security:**
- Signature verification via `POLAR_WEBHOOK_SECRET`
- 5-minute replay attack prevention (validates timestamp)
- Rejects events with future timestamps

**Response:**
```json
{ "received": true }
```

**Error Responses:**
```json
// 401 Invalid Signature
{ "error": "Invalid webhook signature" }

// 401 Replay Attack Detected
{ "error": "Webhook timestamp too old (replay attack prevented)", "code": "REPLAY_ATTACK" }

// 400 Invalid Timestamp
{ "error": "Webhook timestamp in future", "code": "INVALID_TIMESTAMP" }
```

---

### Chat

Zalo OA and Facebook Messenger webhook receivers with auto-KB lookup and AI replies.

**Webhook URLs:**
- Zalo: `POST /v1/chat/webhook/zalo`
- Facebook: `GET/POST /v1/chat/webhook/facebook`

#### `POST /v1/chat/webhook/zalo`

Receive messages from Zalo Official Account.

**Headers:**
```
X-Zalo-Signature: HMAC-SHA256 signature (optional if ZALO_APP_SECRET not configured)
```

**Request Body:**
```json
{
  "event_name": "user_send_text",
  "app_id": "123456",
  "sender": { "id": "user_zalo_456" },
  "recipient": { "id": "oa_zalo_789" },
  "message": {
    "text": "What are your business hours?",
    "msg_id": "msg_abc123"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Flow:**
1. Verify HMAC-SHA256 signature (if `ZALO_APP_SECRET` configured)
2. Lookup channel by `recipient.id` (Zalo OA ID) in `channels` table
3. Auto-create conversation: `zalo_{oa_id}_{user_id}`
4. Save user message to `messages` table
5. Async process: KB lookup → LLM reply → Send via Zalo API
6. Auto-upsert contact via `POST /v1/crm/contacts/auto`

**Response:**
```json
{ "received": true }
```

**Event Types:**
| Event | Action |
|-------|--------|
| `user_send_text` | Process message, send AI reply |
| Other events | Ignored (returns `{ received: true }`) |

#### `GET /v1/chat/webhook/facebook`

Facebook Messenger webhook verification (subscribe callback).

**Query Parameters:**
- `hub.mode`: Must be `subscribe`
- `hub.verify_token`: FB_VERIFY_TOKEN
- `hub.challenge`: Challenge string to return

**Response:**
- `200 OK` with `hub.challenge` if token matches
- `403 Forbidden` otherwise

#### `POST /v1/chat/webhook/facebook`

Receive messages from Facebook Messenger.

**Headers:**
```
X-Hub-Signature-256: sha256=<hmac_signature>
```

**Request Body:**
```json
{
  "object": "page",
  "entry": [
    {
      "id": "page_123456",
      "messaging": [
        {
          "sender": { "id": "user_fb_456" },
          "recipient": { "id": "page_123456" },
          "message": {
            "mid": "mid_abc123",
            "text": "What are your business hours?"
          },
          "timestamp": 1705312200000
        }
      ]
    }
  ]
}
```

**Flow:** (same as Zalo)
1. Verify HMAC-SHA256 signature
2. Lookup channel by `entry.id` (Page ID)
3. Auto-create conversation: `fb_{page_id}_{user_id}`
4. Save user message
5. Async process: KB lookup → LLM reply → Send via Facebook Graph API
6. Auto-upsert contact via `POST /v1/crm/contacts/auto`

**Response:**
```json
{ "received": true }
```

**Processing Pipeline:**
```
1. KB Lookup: SELECT answer FROM knowledge_base WHERE question LIKE '%user_message%'
   ├─ Found → Return cached answer
   └─ Not found → LLM chat with conversation history

2. LLM Chat (via LLMClient):
   - System: "Bạn là trợ lý AI cho doanh nghiệp. Trả lời bằng tiếng Việt, ngắn gọn, thân thiện."
   - History: Last 10 messages (user + assistant)
   - Max tokens: 300, Temperature: 0.7

3. Save reply to messages table
4. Send via platform API:
   - Zalo: POST https://openapi.zalo.me/v3.0/oa/message/cs
   - Facebook: POST https://graph.facebook.com/v19.0/me/messages
```

---

### Content

AI content generation for social media with batch scheduling (7-14 days).

#### `POST /v1/content/generate`

Generate 7-14 days of social media content as drafts via LLM.

**Request:**
```json
{
  "channel": "facebook",
  "days": 7,
  "industry": "cafe",
  "topic": "daily promotions"
}
```

**Response (201 Created):**
```json
{
  "generated": 7,
  "ids": ["cp_tn123_1710847200_1", "cp_tn123_1710847200_2", ...]
}
```

**Parameters:**
| Field | Type | Default | Validation |
|-------|------|---------|------------|
| `channel` | string | `"facebook"` | Platform type (facebook, zalo, tiktok) |
| `days` | number | `7` | 7-14 days |
| `industry` | string | `"cafe"` | Business type for tone customization |
| `topic` | string | `"daily promotions"` | Content theme focus |

**LLM Prompt:**
```
Generate {days} social media posts for a {industry} business on {channel}.
Topic focus: {topic}. Each post should be engaging, include emojis, and be suitable for Vietnamese audiences.
Return JSON array: [{ "day": 1, "content_text": "...", "image_prompt": "..." }, ...]
```

**Saved Content Structure:**
```json
{
  "id": "cp_tn123_1710847200_1",
  "tenant_id": "tn_abc789",
  "channel": "facebook",
  "content_text": "☕ Morning special! Buy 1 Get 1 Free...",
  "image_prompt": "A steaming cup of coffee on wooden table...",
  "status": "draft",
  "scheduled_at": "2024-01-16T08:00:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### `GET /v1/content`

List all content posts with optional status filter.

**Query Parameters:**
- `status`: Filter by status (`draft`, `approved`, `scheduled`, `published`)
- `limit`: Number of results (1-100, default: 50)

**Response:**
```json
{
  "posts": [
    {
      "id": "cp_tn123_1710847200_1",
      "tenant_id": "tn_abc789",
      "channel": "facebook",
      "content_text": "☕ Morning special! Buy 1 Get 1 Free...",
      "image_prompt": "A steaming cup of coffee on wooden table...",
      "status": "draft",
      "scheduled_at": "2024-01-16T08:00:00Z",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### `PATCH /v1/content/:id`

Approve, reject, edit, or schedule a post.

**Request:**
```json
{
  "status": "approved",
  "content_text": "Updated content text...",
  "scheduled_at": "2024-01-16T09:00:00Z"
}
```

**Response:**
```json
{ "updated": true }
```

**Status Values:**
| Status | Description |
|--------|-------------|
| `draft` | AI-generated, pending review |
| `approved` | Ready to publish |
| `rejected` | Discarded |
| `scheduled` | Queued for auto-publish |

---

### CRM

Contact management and remarketing campaigns with auto-upsert from chat events.

#### `GET /v1/crm/contacts`

List contacts with optional tag filter and pagination.

**Query Parameters:**
- `tag`: Filter by tag (optional)
- `limit`: Number of results (1-200, default: 50)

**Response:**
```json
{
  "contacts": [
    {
      "id": "ct_tn123_1710847200",
      "tenant_id": "tn_abc789",
      "external_id": "zalo_user_456",
      "platform": "zalo",
      "name": "John Doe",
      "phone": "+84901234567",
      "email": "john@example.com",
      "tags": ["lead", "enterprise"],
      "notes": "Interested in Pro tier",
      "visit_count": 3,
      "last_contact_at": "2024-01-15T10:30:00Z",
      "created_at": "2024-01-10T08:00:00Z"
    }
  ],
  "count": 1
}
```

#### `POST /v1/crm/contacts`

Create a new contact manually.

**Request:**
```json
{
  "external_id": "zalo_user_456",
  "platform": "zalo",
  "name": "John Doe",
  "phone": "+84901234567",
  "email": "john@example.com",
  "tags": ["lead", "enterprise"],
  "notes": "Interested in Pro tier"
}
```

**Response (201 Created):**
```json
{
  "id": "ct_tn123_1710847200",
  "created": true
}
```

**Validation:**
- `email`: Must be valid email format (or empty string)
- `tags`: Optional array of strings
- All other fields optional

#### `POST /v1/crm/contacts/auto`

Upsert contact from chat event (used by Chat webhooks).

**Key Behavior:**
- Uses `platform + external_id` as composite key
- If contact exists: increments `visit_count`, updates `last_contact_at`
- If contact doesn't exist: creates new contact with `visit_count = 1`

**Request:**
```json
{
  "external_id": "zalo_user_456",
  "platform": "zalo",
  "name": "John Doe"
}
```

**Response (201 Created):**
```json
// New contact
{
  "id": "ct_tn123_1710847200",
  "upserted": "created"
}

// Existing contact
{
  "id": "ct_tn123_1710847200",
  "upserted": "updated"
}
```

#### `GET /v1/crm/campaigns`

List all remarketing campaigns.

**Response:**
```json
{
  "campaigns": [
    {
      "id": "rc_tn123_1710847200",
      "tenant_id": "tn_abc789",
      "name": "7-Day Re-engagement",
      "trigger_type": "days_since_visit",
      "trigger_value": "7",
      "message_template": "Hi {name}, we miss you! Come back for 20% off.",
      "channel": "zalo",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `POST /v1/crm/campaigns`

Create a new remarketing campaign.

**Request:**
```json
{
  "name": "Birthday Promotion",
  "trigger_type": "birthday",
  "trigger_value": "0",
  "message_template": "Happy birthday {name}! Here's a special gift: 30% off today only!",
  "channel": "zalo"
}
```

**Response (201 Created):**
```json
{
  "id": "rc_tn123_1710847200",
  "created": true
}
```

**Trigger Types:**
| Type | Description | trigger_value |
|------|-------------|---------------|
| `days_since_visit` | Days after last visit | Number of days (e.g., "7") |
| `birthday` | On contact's birthday | "0" (same day) |
| `manual` | Manual trigger only | Ignored |
| `tag_match` | Contacts with specific tag | Tag name (e.g., "vip") |

---

---

### Settings

LLM provider configuration (BYOK - Bring Your Own Key) with provider presets.

**Available Providers:** `openai`, `google`, `anthropic`, `custom`

#### `POST /v1/settings/llm`

Save LLM provider settings for tenant.

**Request:**
```json
{
  "provider": "anthropic",
  "api_key": "sk-ant-xxx",
  "base_url": "",
  "model": "claude-sonnet-4-20250514"
}
```

**Response:**
```json
{
  "ok": true,
  "provider": "anthropic",
  "message": "LLM settings saved"
}
```

**Validation:**
- `provider`: Required, must be one of `openai`, `google`, `anthropic`, `custom`
- `api_key`: Required
- `base_url`: Required only for `custom` provider (must be valid URL)
- `model`: Optional, uses provider default if not specified

**Error Responses:**
```json
// 400 - Custom provider without base_url
{ "error": "base_url required for custom provider" }

// 400 - Validation error
{ "error": "API key is required", "code": "VALIDATION_ERROR" }
```

#### `GET /v1/settings/llm`

Get current LLM configuration (API key masked for security).

**Response:**
```json
{
  "provider": "anthropic",
  "api_key": "sk-an...xxx",
  "base_url": null,
  "model": "claude-sonnet-4-20250514",
  "available_providers": ["openai", "google", "anthropic", "custom"]
}
```

**Default Response (no custom settings):**
```json
{
  "provider": "workers-ai",
  "api_key": null,
  "base_url": null,
  "model": null,
  "message": "Using default Workers AI"
}
```

#### `DELETE /v1/settings/llm`

Remove custom LLM configuration, fall back to default Workers AI.

**Response:**
```json
{
  "ok": true,
  "deleted": true,
  "message": "LLM settings removed, falling back to Workers AI"
}
```

---

### Reports

Analytics and reporting with AI-generated summaries.

#### `GET /v1/reports/weekly`

Get 7-day (configurable 1-30 days) aggregated stats with AI summary.

**Query Parameters:**
- `days`: Number of days (1-30, default: 7)

**Response:**
```json
{
  "period": "7d",
  "stats": {
    "messages": 150,
    "new_contacts": 23,
    "conversations": 45,
    "content": [
      { "status": "draft", "count": 10 },
      { "status": "approved", "count": 5 }
    ]
  },
  "ai_summary": "Trong 7 ngày qua, bạn đã xử lý 150 tin nhắn với 23 liên hệ mới..."
}
```

**AI Summary Prompt:**
```
Business weekly report summary (be concise, 3 sentences max, in Vietnamese):
- Messages handled: {count}
- New contacts: {count}
- Conversations: {count}
- Content posts: {status_breakdown}
```

#### `GET /v1/reports/overview`

Get real-time dashboard metrics (today's stats + totals).

**Query Parameters:**
- `include_history`: Boolean (true/false) - include 7-day trend data

**Response:**
```json
{
  "today_messages": 25,
  "total_contacts": 150,
  "pending_content": 15,
  "active_conversations": 8,
  "history": {
    "messages_7d": 150,
    "contacts_7d": 23
  }
}
```

**Metrics:**
| Field | Description |
|-------|-------------|
| `today_messages` | Messages received today (since midnight) |
| `total_contacts` | Total contacts in database |
| `pending_content` | Draft + approved content posts awaiting publish |
| `active_conversations` | Conversations with status = 'active' |
| `history` | (Optional) 7-day backward comparison |

---

### Onboarding

4-step tenant onboarding flow: profile → channel → menu → activate. Step tracking via `tenant_profiles` table.

#### `GET /v1/onboarding/status`

Check current onboarding progress.

**Response:**
```json
{
  "step": 2,
  "completed": false,
  "steps": ["profile", "channel", "menu", "activate"]
}
```

**Step Values:**
| Step | Name | Description |
|------|------|-------------|
| 0 | `none` | Just created, no profile |
| 1 | `profile` | Business info saved |
| 2 | `channel` | Connected Zalo/FB |
| 3 | `menu` | Menu uploaded + FAQ generated |
| 4 | `activate` | Fully activated |

#### `POST /v1/onboarding/profile`

Step 1: Save business profile information.

**Request:**
```json
{
  "business_name": "Cafe Central",
  "industry": "cafe",
  "address": "123 Main St, District 1, HCMC",
  "phone": "+84123456789",
  "hours": "7:00-22:00"
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "step": 1,
  "message": "Profile saved. Next: connect your channel."
}
```

#### `POST /v1/onboarding/channel`

Step 2: Connect communication channel (Zalo OA or Facebook Page).

**Request:**
```json
{
  "type": "zalo_oa",
  "external_id": "zalo_oa_123",
  "access_token": "xxx",
  "name": "Cafe Central OA"
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "step": 2,
  "message": "Channel connected. Next: upload your menu."
}
```

**Supported Channel Types:**
| Type | Description |
|------|-------------|
| `zalo_oa` | Zalo Official Account |
| `facebook_page` | Facebook Messenger Page |

#### `POST /v1/onboarding/menu`

Step 3: Upload menu data + auto-generate FAQ knowledge base entries via LLM.

**Request:**
```json
{
  "menu_data": {
    "categories": [
      { "id": "coffee", "name": "Cà phê" },
      { "id": "tea", "name": "Trà" }
    ],
    "items": [
      { "id": "capuchino", "name": "Capuchino", "price": 45000, "category_id": "coffee" },
      { "id": "tra-dao", "name": "Trà đào", "price": 35000, "category_id": "tea" }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "ok": true,
  "step": 3,
  "faq_generated": 15,
  "message": "Menu uploaded. FAQ KB generated. Next: activate your account."
}
```

**LLM FAQ Generation:**
```
Prompt: "Generate FAQ questions and answers for this cafe menu in Vietnamese.
Focus on: prices, ingredients, allergies, customization, popular items.
Return JSON: [{ question, answer, category }, ...]"
```

#### `POST /v1/onboarding/activate`

Step 4: Complete onboarding and activate tenant. Requires steps 1-3 to be completed.

**Validation:**
- Step must be 3 (menu completed)
- Profile must exist
- Channel must exist
- Menu must exist

**Response (200 OK):**
```json
{
  "ok": true,
  "step": 4,
  "onboarding_completed": true,
  "message": "Welcome to Mekong! Your account is now active."
}
```

**Error Responses:**
```json
// 400 - Incomplete onboarding
{ "error": "Please complete steps 1-3 first", "code": "VALIDATION_ERROR" }
```

---

### Payment VN

Vietnamese payment integration (MoMo, VNPAY) with HMAC signature verification and replay attack prevention.

**Payment Flow:**
1. `GET /pricing-vn` → Display VND tiers
2. `POST /create` → Get payment URL (MoMo or VNPAY)
3. User completes payment on gateway
4. Gateway calls IPN webhook (MoMo: POST, VNPAY: GET)
5. Webhook verifies signature + replay prevention → Credits tenant

#### `GET /v1/payment-vn/pricing-vn`

Get public VND pricing tiers. No authentication required.

**Response:**
```json
{
  "tiers": [
    { "id": "free", "name": "Miễn phí", "price_vnd": 0, "credits": 10, "description": "Dùng thử" },
    { "id": "starter", "name": "Starter", "price_vnd": 199000, "credits": 50, "description": "Cá nhân" },
    { "id": "pro", "name": "Pro", "price_vnd": 499000, "credits": 200, "description": "Nhóm nhỏ" },
    { "id": "enterprise", "name": "Enterprise", "price_vnd": 2990000, "credits": 1000, "description": "Doanh nghiệp" }
  ]
}
```

#### `POST /v1/payment-vn/create`

Create payment URL for MoMo or VNPAY.

**Request:**
```json
{
  "method": "momo",
  "tenant_id": "tn_abc123",
  "plan": "pro",
  "amount": 499000,
  "credits": 200
}
```

**Response (201 Created):**
```json
{
  "method": "momo",
  "order_id": "tn_abc123-1705234567890",
  "amount": 499000,
  "payment_url": "https://payment.momo.vn/pay?partnerCode=MEKONG&orderId=..."
}
```

**Order ID Format:**
- MoMo: `{tenant_id}-{timestamp}` (base64-encoded in extraData)
- VNPAY: `{tenant_id}-{timestamp}` (pipe-delimited in vnp_OrderInfo)

#### `POST /v1/payment-vn/momo/ipn`

MoMo Instant Payment Notification (IPN) handler.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "partnerCode": "MEKONG",
  "orderId": "tn_abc123-1705234567890",
  "amount": 499000,
  "transId": 1234567890,
  "resultCode": 0,
  "message": "Success",
  "localMessage": "Giao dịch thành công",
  "timestamp": 1705234567000,
  "signature": "hmac-sha256-hex-signature",
  "extraData": "dG5fYWJjMTIzLTE3MDUyMzQ1Njc4OTA="  // base64-encoded order_id
}
```

**Verification Steps:**
1. **Signature:** HMAC-SHA256 of raw body using `MOMO_SECRET_KEY`
2. **Result Code:** `resultCode === 0` (success)
3. **Replay Prevention:** Check `payment_logs` table for duplicate `transId`
4. **Timestamp:** Within 5-minute window

**Response:**
```json
{ "result": "success", "transaction_id": "momo_1234567890" }
```

**Error Responses:**
```json
// 400 Invalid Signature
{ "error": "Invalid MoMo signature", "code": "INVALID_SIGNATURE" }

// 400 Payment Failed
{ "error": "Payment failed", "resultCode": 1006 }

// 409 Replay Attack Detected
{ "error": "Duplicate transaction", "code": "REPLAY_ATTACK" }
```

#### `GET /v1/payment-vn/vnpay/ipn`

VNPAY IPN + return handler (GET with query params).

**Query Parameters:**
```
vnp_TmnCode=MEKONG
vnp_TransactionNo=1234567890
vnp_TransactionStatus=00
vnp_ResponseCode=00
vnp_Amount=49900000  // Amount * 100 (VND)
vnp_TxnRef=tn_abc123-1705234567890
vnp_SecureHash=sha512-hex-signature
vnp_CreateDate=20240115103000
vnp_OrderInfo=tn_abc123-1705234567890|pro|200
```

**Verification Steps:**
1. **Signature:** SHA512 hash of sorted query params (excluding `vnp_SecureHash`) using `VNPAY_SECRET_KEY`
2. **Transaction Status:** `vnp_TransactionStatus === '00'` (success)
3. **Response Code:** `vnp_ResponseCode === '00'` (success)
4. **Replay Prevention:** Check `payment_logs` table for duplicate `vnp_TransactionNo`
5. **Timestamp:** Within 5-minute window

**Response:**
```
RSPCODE=00
```

**Error Responses:**
```
RSPCODE=99  // Invalid signature
RSPCODE=01  // Payment failed
```

**Security Features:**
- **HMAC Verification:** MoMo (SHA256), VNPAY (SHA512)
- **Replay Attack Prevention:** Unique transaction ID check in `payment_logs`
- **Timestamp Window:** 5 minutes from gateway timestamp
- **Idempotency:** Same transaction processed only once

---

### Governance

Stakeholders, proposals, voting, reputation, Ngũ Sự framework.

#### `GET /v1/governance/stakeholders`

List all stakeholders.

#### `POST /v1/governance/stakeholders`

Add a new stakeholder.

**Request:**
```json
{
  "name": "Alice Nguyen",
  "role": "expert",
  "share": 0.15,
  "reputation": 100
}
```

#### `GET /v1/governance/proposals`

List all governance proposals.

**Query Parameters:**
- `status`: Filter by status (pending, approved, rejected)
- `type`: Filter by type (funding, policy, constitutional)

#### `POST /v1/governance/proposals`

Create a new governance proposal.

**Request:**
```json
{
  "title": "Increase community fund allocation to 15%",
  "description": "Proposal details...",
  "type": "funding",
  "votes_required": 0.66
}
```

#### `POST /v1/governance/proposals/:id/vote`

Cast a vote on a proposal (quadratic voting: votes = √credits).

**Request:**
```json
{
  "stakeholder_id": "stk_abc123",
  "vote": "yes",
  "credits_spent": 100
}
```

**Response:**
```json
{
  "vote_id": "vote_xyz789",
  "votes_cast": 10,
  "credits_spent": 100,
  "proposal_status": "pending"
}
```

#### `GET /v1/governance/reputation`

Get stakeholder reputation score.

#### `POST /v1/governance/reputation`

Update stakeholder reputation score.

**Request:**
```json
{
  "stakeholder_id": "stk_abc123",
  "score_change": 10,
  "reason": "Successfully mediated conflict #42"
}
```

#### `POST /v1/governance/ngu-su`

Perform Ngũ Sự 5-element governance scoring.

**Request:**
```json
{
  "proposal_id": "prop_abc123",
  "scores": {
    "dao": 8,
    "thien": 7,
    "dia": 9,
    "tuong": 6,
    "phap": 8
  }
}
```

#### `GET /v1/governance/ngu-su`

Get Ngũ Sự scores for a proposal.

#### `GET /v1/governance/treasury`

Get treasury balance and allocation.

**Response:**
```json
{
  "total_balance": 1500000,
  "allocations": {
    "community_fund": 150000,
    "expert_pool": 300000,
    "operations": 1050000
  }
}
```

---

### Ledger

Double-entry accounting transfers, topups, balance queries, transaction history.

#### `GET /v1/ledger/balance`

Get current account balance.

**Query Parameters:**
- `code`: Filter by account code (e.g., `revenue`, `expenses`)

**Response:**
```json
{
  "balance": 1500000,
  "currency": "VND",
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### `GET /v1/ledger/history`

Get transaction history.

**Query Parameters:**
- `from`: Start date (ISO 8601)
- `to`: End date (ISO 8601)
- `account`: Filter by account code

**Response:**
```json
{
  "transactions": [
    {
      "id": "txn_abc123",
      "type": "transfer",
      "amount": 500000,
      "from_account": "revenue",
      "to_account": "expenses",
      "description": "Expert share payment",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### `POST /v1/ledger/transfer`

Create a transfer between accounts.

**Request:**
```json
{
  "from_account": "acc_revenue",
  "to_account": "acc_expert_share",
  "amount": 150000,
  "description": "Expert share payment",
  "idempotency_key": "unique_key_123"
}
```

#### `POST /v1/ledger/topup`

Top up account balance.

**Request:**
```json
{
  "amount": 1000000,
  "source": "momo_payment",
  "transaction_id": "momo_txn_xyz789"
}
```

**Response:**
```json
{
  "transaction_id": "topup_abc123",
  "amount": 1000000,
  "new_balance": 2500000,
  "source": "momo_payment"
}
```

---

### Equity

Equity management, cap tables, SAFE notes, vesting schedules.

#### `GET /v1/equity/entities`

List all portfolio entities.

**Response:**
```json
{
  "entities": [
    {
      "id": "ent_abc123",
      "name": "Acme Corporation",
      "entity_type": "portfolio_company",
      "total_authorized_shares": 10000000,
      "jurisdiction": "VN"
    }
  ]
}
```

#### `POST /v1/equity/entities`

Create a new portfolio entity (auto-creates Common share class).

**Request:**
```json
{
  "name": "Acme Corporation",
  "entity_type": "portfolio_company",
  "total_shares": 10000000,
  "jurisdiction": "VN"
}
```

**Response:**
```json
{
  "id": "ent_abc123",
  "share_class_id": "sc_xyz789"
}
```

#### `POST /v1/equity/grants`

Issue equity grant to stakeholder.

**Request:**
```json
{
  "entity_id": "ent_abc123",
  "stakeholder_id": "stk_def456",
  "share_class_id": "sc_xyz789",
  "shares": 10000,
  "price_per_share": 0.001,
  "grant_type": "grant",
  "vesting_months": 48,
  "cliff_months": 12
}
```

**Response:**
```json
{
  "id": "grant_ghi789",
  "shares": 10000,
  "vesting_months": 48
}
```

#### `GET /v1/equity/cap-table/:entityId`

Get cap table for an entity with vesting details.

**Response:**
```json
{
  "entity": { "name": "Acme Corporation", "total_authorized": 10000000 },
  "total_outstanding": 2500000,
  "dilution_pct": "25.00",
  "holders": [
    { "stakeholder_id": "stk_def456", "display_name": "Alice Nguyen", "share_class": "Common", "total_granted": 10000 }
  ],
  "vesting_schedule": [
    { "grant_id": "grant_ghi789", "shares": 10000, "vested_shares": 2500, "vested_pct": 25 }
  ],
  "safe_notes": []
}
```

#### `POST /v1/equity/safe`

Issue SAFE note to investor.

**Request:**
```json
{
  "entity_id": "ent_abc123",
  "investor_stakeholder_id": "stk_inv123",
  "principal_amount": 100000,
  "valuation_cap": 5000000,
  "discount_rate": 0.2
}
```

**Response:**
```json
{
  "id": "safe_jkl012",
  "status": "outstanding"
}
```

#### `POST /v1/equity/safe/:id/convert`

Convert SAFE note to equity.

**Request:**
```json
{
  "price_per_share": 1.00,
  "share_class_id": "sc_xyz789"
}
```

**Response:**
```json
{
  "grant_id": "grant_mno345",
  "shares_converted": 125000,
  "effective_price": 0.80
}
```

**Conversion Formula:**
- `effective_price = price_per_share * (1 - discount_rate)`
- `shares = principal_amount / effective_price`
- Investor receives better of discount vs valuation cap

---

### Revenue

6-way revenue split distribution (Binh Pháp tam giác ngược — inverted triangle philosophy).

**Default Split Configuration:**
| Recipient | Percentage | Purpose |
|-----------|------------|---------|
| `platform` | 20% | Platform owner (servant leader, smallest share) |
| `expert` | 30% | Expert who provided knowledge/IP |
| `ai_compute` | 15% | LLM inference cost + margin |
| `developer` | 15% | Developer/agency who brought customer |
| `community_fund` | 10% | Treasury for quadratic funding matching |
| `customer_reward` | 10% | Loyalty credits back to customer |

#### `POST /v1/revenue/split`

Execute revenue split for a completed task. Creates journal entry with 6-way distribution via double-entry ledger.

**Request:**
```json
{
  "task_id": "msn_abc123",
  "total_amount": 1000000,
  "currency": "VND"
}
```

**Response (201 Created):**
```json
{
  "journal_entry_id": "je_xyz789",
  "total_amount": 1000000,
  "splits": [
    { "recipient": "platform", "amount": 200000, "account_code": "revenue:platform" },
    { "recipient": "expert", "amount": 300000, "account_code": "revenue:expert" },
    { "recipient": "ai_compute", "amount": 150000, "account_code": "revenue:ai_compute" },
    { "recipient": "developer", "amount": 150000, "account_code": "revenue:developer" },
    { "recipient": "community_fund", "amount": 100000, "account_code": "treasury:community" },
    { "recipient": "customer_reward", "amount": 100000, "account_code": "liability:customer_credits" }
  ],
  "treasury_updated": true
}
```

**Flow:**
1. Validate task completion status
2. Create journal entry with 6 transaction lines (double-entry)
3. Update `treasury` table with `community_fund` allocation
4. Return journal entry ID for audit trail

#### `GET /v1/revenue/split-config`

Get current revenue split configuration for tenant.

**Response:**
```json
{
  "tenant_id": "tn_abc123",
  "split_config": {
    "platform": 0.20,
    "expert": 0.30,
    "ai_compute": 0.15,
    "developer": 0.15,
    "community_fund": 0.10,
    "customer_reward": 0.10
  },
  "customized": false
}
```

#### `GET /v1/revenue/summary`

Get revenue summary for a date range.

**Query Parameters:**
- `from`: Start date (ISO 8601)
- `to`: End date (ISO 8601)

**Response:**
```json
{
  "period": { "from": "2024-01-01", "to": "2024-01-31" },
  "total_revenue": 15000000,
  "by_recipient": {
    "platform": 3000000,
    "expert": 4500000,
    "ai_compute": 2250000,
    "developer": 2250000,
    "community_fund": 1500000,
    "customer_reward": 1500000
  },
  "treasury_balance": 2500000
}
```

---

### Funding

Quadratic funding rounds with democratic matching pool distribution — funded by `community_fund` treasury (10% of revenue split).

**RaaS Value Proposition:**
- **Community-funded**: Matching pool comes from `community_fund` (10% of all revenue via `/v1/revenue/split`)
- **Democratic**: 10 people × $1 beats 1 person × $10 — many small contributions win
- **Transparent**: All contributions tracked in double-entry ledger (`journal_entries` + `transaction_lines`)

**Core Principle:** `matched = (Σ√ci)² - Σci`

#### `GET /v1/funding/rounds`

List all funding rounds for the tenant.

**Response:**
```json
{
  "rounds": [
    {
      "id": "fr_abc123",
      "tenant_id": "tn_xyz789",
      "title": "Q1 2026 Community Projects",
      "matching_pool": 500000,
      "status": "active",
      "starts_at": "2024-01-01T00:00:00Z",
      "ends_at": "2024-03-31T23:59:59Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### `POST /v1/funding/rounds`

Create a new funding round. Matching pool is transferred from `treasury:community` account via ledger.

**Request:**
```json
{
  "title": "Q1 2026 Community Projects",
  "matching_pool": 500000,
  "duration_days": 90
}
```

**Validation:**
| Field | Constraint |
|-------|------------|
| `title` | Required, 1-200 chars |
| `matching_pool` | Required, positive integer, max 10B (must exist in `treasury:community`) |
| `duration_days` | Optional, positive integer, max 365 (default: 14) |

**Ledger Integration:**
```
1. Debit: treasury:community (decrease community fund balance)
2. Credit: funding:matching_pool (allocate to round)
3. Create journal entry via /v1/ledger/transfer
```

**Response (201 Created):**
```json
{
  "id": "fr_abc123",
  "matching_pool": 500000,
  "journal_entry_id": "je_funding123",
  "ends_at": "2024-03-31T23:59:59Z"
}
```

#### `POST /v1/funding/projects`

Add a project to a funding round.

**Request:**
```json
{
  "round_id": "fr_abc123",
  "name": "Open Source Education Platform",
  "description": "Free coding bootcamp for underprivileged youth",
  "author_id": "stakeholder_xyz"
}
```

**Validation:**
| Field | Constraint |
|-------|------------|
| `round_id` | Required, valid UUID |
| `name` | Required, 1-200 chars |
| `description` | Optional, max 1000 chars |
| `author_id` | Optional, valid UUID |

**Response (201 Created):**
```json
{
  "id": "fp_def456"
}
```

#### `POST /v1/funding/contribute`

Contribute to a project (stakeholder can only contribute once per project).

**Request:**
```json
{
  "project_id": "fp_def456",
  "stakeholder_id": "stakeholder_xyz",
  "amount": 1000
}
```

**Validation:**
| Field | Constraint |
|-------|------------|
| `project_id` | Required, valid UUID |
| `stakeholder_id` | Required, valid UUID |
| `amount` | Required, positive integer, max 1B |

**Response (201 Created):**
```json
{
  "id": "fc_ghi789",
  "amount": 1000
}
```

**Error Responses:**
```json
// 409 Conflict - Already contributed
{ "error": "Already contributed to this project", "code": "CONFLICT" }
```

#### `POST /v1/funding/rounds/:id/calculate`

Calculate and distribute matching pool using quadratic funding formula. Updates ledger for each project.

**Quadratic Funding Formula:**
```
matched = (Σ√ci)² - Σci

Where:
- ci = each individual contribution
- Σ√ci = sum of square roots of all contributions
- matched = matching amount to distribute

Examples:
- 10 people × $1: √1×10 = 10 → 10² = 100 → matched = 100 - 10 = 90
- 1 person × $10: √10 = 3.16 → 3.16² = 10 → matched = 10 - 10 = 0
```

**Algorithm:**
1. For each project: `qf_score = (Σ√ci)² - Σci`
2. Sum all QF scores: `total_qf_score = Σ qf_score`
3. Distribute matching pool: `project_match = (qf_score / total_qf_score) × matching_pool`
4. For each project, create ledger entry:
   - Debit: `funding:matching_pool`
   - Credit: `project:funding_{id}`
5. Update round status to `completed`

**Response:**
```json
{
  "round_id": "fr_abc123",
  "matching_pool": 500000,
  "results": [
    {
      "id": "fp_def456",
      "name": "Open Source Education Platform",
      "direct": 5000,
      "qf_score": 12500,
      "contributors": 25,
      "matched_amount": 312500,
      "total": 317500,
      "journal_entry_id": "je_match456"
    },
    {
      "id": "fp_ghi789",
      "name": "Climate Data Visualization",
      "direct": 10000,
      "qf_score": 7500,
      "contributors": 10,
      "matched_amount": 187500,
      "total": 197500,
      "journal_entry_id": "je_match789"
    }
  ],
  "note": "QF: 10 people × $1 beats 1 person × $10 — democratic funding"
}
```

**Reports Integration:**
- Funding contributions visible in `/v1/reports/weekly` under `content` stats
- Treasury balance tracked in `/v1/revenue/summary` → `treasury_balance`

**Database Tables:**
| Table | Purpose |
|-------|---------|
| `funding_rounds` | Round metadata (title, matching_pool, status, dates) |
| `funding_projects` | Projects in round (tracks `total_contributions`, `matched_amount`) |
| `funding_contributions` | Individual contributions (unique: `project_id` + `stakeholder_id`) |

**Ledger Integration:**
| Table | Purpose |
|-------|---------|
| `journal_entries` | Audit trail for matching pool allocation |
| `transaction_lines` | Double-entry records (debit/credit per project) |
| `ledger_accounts` | Account balances (`funding:matching_pool`, `project:funding_{id}`) |

---

### Matching

Stakeholder matching algorithm with weighted scoring (skill 60% + reputation 40% + industry bonus) — connecting talent to opportunities, driving revenue-generating collaborations.

**RaaS Value Proposition:**
- **Revenue catalyst**: Matched stakeholders → collaborations → revenue events → 6-way split via `/v1/revenue/split`
- **Community-driven**: Matching pool funded by `community_fund` (10% of revenue) creates virtuous cycle
- **Transparent outcomes**: Match results visible in `/v1/reports/weekly` analytics

**Matching Algorithm:**
```
totalScore = (skillScore + industryBonus) × 0.6 + reputationScore × 0.4

Where:
- skillScore = overlap / skillsNeeded.length (60% weight)
  - overlap = count of matching skills (case-insensitive)
  - If no skills needed or no profiles with skills, skillScore = 1
- industryBonus = 0.1 if stakeholder has matching industry, else 0
- reputationScore = min(reputation_score / 1000, 1) (40% weight)
  - Assumes max reputation ~1000
```

**Request Types:**
| Type | Purpose | Revenue Potential |
|------|---------|-------------------|
| `expert_needed` | Looking for domain expert | High — expert delivers paid work |
| `cofounder_needed` | Seeking co-founder | Very High — long-term partnership |
| `mentor_needed` | Seeking mentor/advisor | Medium — advisory relationship |
| `vc_intro` | Introduction to VCs/investors | High — funding → platform usage |

**Match Status Workflow:**
| Status | Description | Next Action |
|--------|-------------|-------------|
| `pending` | Match proposed, awaiting response | Stakeholder reviews match |
| `accepted` | Stakeholder accepted the match | Begin collaboration |
| `rejected` | Stakeholder declined the match | Return to matching pool |
| `completed` | Collaboration completed successfully | Track revenue impact via `/v1/revenue/split` |

#### `POST /v1/matching/profiles`

Create or update a stakeholder skill profile.

**Request:**
```json
{
  "stakeholder_id": "stakeholder_abc123",
  "skills": ["React", "TypeScript", "Node.js", "Product Strategy"],
  "industries": ["SaaS", "FinTech", "E-commerce"],
  "availability": "available",
  "hourly_rate_usd": 150,
  "bio": "Senior full-stack engineer with 10 years of experience"
}
```

**Validation:**
| Field | Constraint |
|-------|------------|
| `stakeholder_id` | Required, valid UUID (must exist in stakeholders table) |
| `skills` | Optional, array of strings |
| `industries` | Optional, array of strings |
| `availability` | Optional, default "available" |
| `hourly_rate_usd` | Optional, positive number |
| `bio` | Optional, string |

**Response (201 Created for new profile):**
```json
{
  "id": "sp_xyz789",
  "created": true
}
```

**Response (200 OK for updated profile):**
```json
{
  "updated": true
}
```

**Error Responses:**
```json
// 404 Not Found - Stakeholder does not exist
{ "error": "Stakeholder not found", "code": "NOT_FOUND" }
```

#### `POST /v1/matching/requests`

Create a match request with automatic matching.

**Request Types:**
- `expert_needed` — Looking for domain expert
- `cofounder_needed` — Seeking co-founder
- `mentor_needed` — Seeking mentor/advisor
- `vc_intro` — Introduction to VCs/investors

**Request:**
```json
{
  "requester_id": "stakeholder_def456",
  "request_type": "expert_needed",
  "skills_needed": ["Machine Learning", "Python", "MLOps"],
  "industry": "HealthTech",
  "description": "Need ML expert for medical imaging AI project",
  "budget_usd": 5000
}
```

**Matching Algorithm:**

```
totalScore = (skillScore + industryBonus) × 0.6 + reputationScore × 0.4

Where:
- skillScore = overlap / skillsNeeded.length (60% weight)
  - overlap = count of matching skills (case-insensitive)
  - If no skills needed or no profiles with skills, skillScore = 1
- industryBonus = 0.1 if stakeholder has matching industry, else 0
- reputationScore = min(reputation_score / 1000, 1) (40% weight)
  - Assumes max reputation ~1000
```

**Auto-Match Process:**
1. Find all available profiles in same tenant (excludes requester)
2. Calculate totalScore for each profile
3. Skip profiles with score < 0.1
4. Create match records with score and reasons
5. Update request status to `matched` if matches found
6. Return top 5 matches sorted by score

**Response (201 Created):**
```json
{
  "request_id": "mr_abc123",
  "matches_found": 3,
  "matches": [
    {
      "match_id": "match_xyz789",
      "stakeholder_id": "stakeholder_ghi789",
      "score": 0.85,
      "reasons": ["skill_overlap:80%", "industry_match", "reputation:75"]
    },
    {
      "match_id": "match_jkl012",
      "stakeholder_id": "stakeholder_mno345",
      "score": 0.62,
      "reasons": ["skill_overlap:60%", "reputation:45"]
    }
  ]
}
```

**Reports Integration:**
- Match outcomes tracked in `/v1/reports/weekly` under `conversations` metric
- Successful matches → collaborations → revenue → visible in `/v1/revenue/summary`
- Active matches count contributes to `active_conversations` in `/v1/reports/overview`

**Ledger Integration (Post-Match):**
```
After match status = "accepted":
1. Collaboration generates revenue (e.g., expert service payment)
2. Revenue split via `/v1/revenue/split`:
   - Debit: `revenue:platform` (20%)
   - Debit: `revenue:expert` (30%)
   - Debit: `revenue:community_fund` (10% → funds future matching)
   - Credit: respective stakeholder accounts
3. Journal entry created for audit trail
```

**Validation:**
| Field | Constraint |
|-------|------------|
| `requester_id` | Required, valid UUID |
| `request_type` | Required, enum: `expert_needed`, `cofounder_needed`, `mentor_needed`, `vc_intro` |
| `skills_needed` | Optional, array of strings |
| `industry` | Optional, string |
| `description` | Optional, string |
| `budget_usd` | Optional, positive number |

#### `GET /v1/matching/requests`

List all match requests for the tenant.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | — | Optional filter: `pending`, `matched` |

**Response:**
```json
{
  "requests": [
    {
      "id": "mr_abc123",
      "tenant_id": "tn_xyz789",
      "requester_id": "stakeholder_def456",
      "request_type": "expert_needed",
      "skills_needed": ["Machine Learning", "Python", "MLOps"],
      "industry": "HealthTech",
      "description": "Need ML expert for medical imaging AI project",
      "budget_usd": 5000,
      "status": "matched",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### `PATCH /v1/matching/matches/:id`

Accept or reject a match.

**Request:**
```json
{
  "status": "accepted"
}
```

**Match Status Workflow:**
| Status | Description |
|--------|-------------|
| `accepted` | Stakeholder accepted the match |
| `rejected` | Stakeholder declined the match |
| `completed` | Collaboration completed successfully |

**Response:**
```json
{
  "id": "match_xyz789",
  "status": "accepted"
}
```

**Error Responses:**
```json
// 404 Not Found
{ "error": "Match not found", "code": "NOT_FOUND" }
```

**Database Tables:**
| Table | Purpose |
|-------|---------|
| `skill_profiles` | Stakeholder skills, industries, availability, hourly rate |
| `match_requests` | Match requests with type, skills needed, budget |
| `matches` | Match records linking requests to stakeholders with scores |

**RaaS Flow: Match → Revenue → Community Fund:**
```
1. Match accepted → Collaboration begins
2. Collaboration generates revenue (e.g., $1000 expert service)
3. Revenue split via /v1/revenue/split:
   - Platform: $200 (20%)
   - Expert: $300 (30%)
   - AI Compute: $150 (15%)
   - Developer: $150 (15%)
   - Community Fund: $100 (10%) → Funds next matching round
   - Customer Reward: $100 (10%)
4. Community Fund replenished → More quadratic funding → More matches
5. Virtuous cycle: matches → revenue → community fund → more matches
```

---

### Conflicts

5-level conflict resolution system.

#### `GET /v1/conflicts`

List all conflicts.

#### `POST /v1/conflicts`

Create a new conflict case.

**Request:**
```json
{
  "parties": ["stakeholder_a", "stakeholder_b"],
  "description": "Dispute over resource allocation",
  "level": "agent_negotiation"
}
```

**Conflict Levels:**
1. `auto_resolve` - Automated resolution
2. `agent_negotiation` - AI-mediated negotiation
3. `governance_review` - Human governance review
4. `human_arbitration` - External arbitration
5. `constitutional_review` - Constitutional court review

---

### Decentralization

4-phase progressive power transfer.

#### `GET /v1/decentralization/status`

Get current decentralization phase.

#### `POST /v1/decentralization/check-transition`

Check eligibility for transition to next phase.

**Response:**
```json
{
  "eligible": true,
  "current_phase": "foundation",
  "target_phase": "growth",
  "checks": {
    "stakeholders": { "required": 20, "actual": 25, "met": true },
    "months": { "required": 12, "actual": 14, "met": true }
  },
  "message": "Ready to transition to growth phase"
}
```

**Phases:**
1. **Foundation** (50/25/25) - Platform retains majority control
2. **Growth** (33/34/33) - Balanced power distribution
3. **Maturity** (25/40/35) - Community majority
4. **Full Inversion** (20/45/35) - DAO-governed

---

### RBAC

Role-based access control policy checking.

#### `GET /v1/rbac/policies`

List all RBAC policies.

#### `POST /v1/rbac/check`

Check if a role has permission.

**Request:**
```json
{
  "role": "expert",
  "action": "transfer",
  "resource": "ledger"
}
```

**Response:**
```json
{
  "allowed": true,
  "policy": "expert_ledger_transfer"
}
```

---

## Error Handling

All errors follow this format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `INSUFFICIENT_CREDITS` | 402 | Not enough MCU credits |
| `RATE_LIMITED` | 429 | Too many requests |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limits

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 10 | 1,000 |
| Starter | 60 | 10,000 |
| Pro | 300 | 100,000 |
| Enterprise | 1,000 | Unlimited |

---

## SDK Examples

### JavaScript/TypeScript

```typescript
import { MekongClient } from '@mekong/sdk'

const client = new MekongClient('mekong_sk_live_xyz789')

// Create a task
const task = await client.tasks.create({
  goal: 'Deploy to production',
  params: { priority: 'high' }
})

// Stream task execution
const stream = await client.tasks.stream(task.id)
stream.on('data', (event) => console.log(event))
```

### Python

```python
from mekong import MekongClient

client = MekongClient(api_key='mekong_sk_live_xyz789')

# Create a task
task = client.tasks.create(
    goal='Deploy to production',
    params={'priority': 'high'}
)

# Stream task execution
for event in client.tasks.stream(task.id):
    print(event)
```

---

## Changelog

### v5.0.0 (2024-01)
- Added governance module (Ngũ Sự framework)
- Added double-entry ledger system
- Added quadratic funding support
- Added Vietnamese payment integration (MoMo, VNPAY)
- Added 5-level conflict resolution
- Added progressive decentralization

### v4.0.0 (2023-12)
- Added RaaS architecture
- Added multi-agent support
- Added credit metering

---

*Generated from OpenAPI 3.0 specification.*
