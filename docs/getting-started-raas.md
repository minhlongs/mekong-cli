# RaaS Getting Started — From Signup to First AI Task

> **Repository-as-a-Service (RaaS)** — Multi-tenant AI task execution platform
> **Version:** 3.2.0 | **Endpoint:** `https://engine.agencyos.network`

---

## Prerequisites

- **cURL** or **HTTPie** for API testing
- **Node.js 18+** (optional, for SDK usage)
- **5 minutes** to complete setup

---

## Step 1: Create Your Tenant Account

Register a new tenant to receive your unique API key.

### Request

```bash
curl -X POST https://engine.agencyos.network/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agency"
  }'
```

### Response (201 Created)

```json
{
  "tenant_id": "tnt_abc123xyz",
  "name": "my-agency",
  "api_key": "sk_live_7FpQ2mN9xK4wR8vL3jH6",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

### ⚠️ Critical: Save Your API Key

- **Displayed once only** — cannot be recovered if lost
- Store in password manager or secure vault
- If lost, regenerate via `POST /billing/tenants/regenerate-key`

### Authentication Format

All authenticated requests require:

```
Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6
```

---

## Step 2: Understand Credit System

RaaS uses credit-based metering. Each tenant receives **10 free welcome credits**.

### Credit Tiers

| Tier | Credits | Task Complexity | Example Goals |
|------|---------|-----------------|---------------|
| **Simple** | 1 credit | < 50 chars | "List files in /tmp" |
| **Standard** | 3 credits | 50-150 chars | "Create a Python script that fetches weather API" |
| **Complex** | 5 credits | > 150 chars | "Build a REST API with authentication, database models, and deploy to Cloudflare Workers" |

### Rate Limits by Tier

| Tier | Requests/minute | Monthly Credits |
|------|-----------------|-----------------|
| Free | 10 | 10 (welcome only) |
| Pro | 60 | 50-200 (via subscription) |
| Enterprise | 300 | 500-1000+ |

### Check Credit Balance

```bash
curl https://engine.agencyos.network/billing/credits \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6"
```

**Response:**

```json
{
  "tenant_id": "tnt_abc123xyz",
  "balance": 10,
  "tier": "free"
}
```

### View Credit History

```bash
curl "https://engine.agencyos.network/billing/credits/history?limit=20" \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6"
```

**Response:**

```json
{
  "tenant_id": "tnt_abc123xyz",
  "history": [
    {
      "id": "crd_welcome_001",
      "tenant_id": "tnt_abc123xyz",
      "amount": 10,
      "reason": "welcome: free tier bonus",
      "created_at": "2026-03-19T10:30:00Z"
    }
  ],
  "limit": 20
}
```

---

## Step 3: Create Your First AI Task

Submit a goal for the AI agent to execute.

### Estimate Credits Before Submission

Task complexity determines credit cost:

```typescript
import { estimateCredits } from '@mekong/cli-core'

estimateCredits("List files")           // → 1 (simple)
estimateCredits("Build a CRUD API")     // → 3 (standard)
estimateCredits("Create full-stack app with auth, database, and deployment") // → 5 (complex)
```

### Create Mission (Task)

```bash
curl -X POST https://engine.agencyos.network/v1/tasks \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6" \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Create a Python script that lists all files in /tmp directory"
  }'
```

### Response (201 Created)

```json
{
  "id": "msn_7xK9pL2mN4qR8wV3",
  "tenant_id": "tnt_abc123xyz",
  "goal": "Create a Python script that lists all files in /tmp directory",
  "status": "pending",
  "credits_used": 1,
  "total_steps": 0,
  "completed_steps": 0,
  "created_at": "2026-03-19T10:35:00Z",
  "result": null,
  "completed_at": null
}
```

### Status Lifecycle

```
pending → running → completed
                    ↓
                 failed (if error)
```

---

## Step 4: Stream Task Progress (SSE)

Watch task execution in real-time via Server-Sent Events.

### Open SSE Stream

```bash
curl -N https://engine.agencyos.network/v1/tasks/msn_7xK9pL2mN4qR8wV3/stream \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6"
```

### SSE Event Format

```
data: {"type":"status","data":{"id":"msn_7xK9pL2mN4qR8wV3","status":"running","result":null}}

data: {"type":"step","data":{"step":1,"total":3,"description":"Analyzing goal..."}}

data: {"type":"step","data":{"step":2,"total":3,"description":"Executing shell commands..."}}

data: {"type":"step","data":{"step":3,"total":3,"description":"Verifying results..."}}

data: {"type":"status","data":{"id":"msn_7xK9pL2mN4qR8wV3","status":"completed","result":"Script created successfully"}}
```

### JavaScript SSE Client Example

```typescript
const eventSource = new EventSource(
  'https://engine.agencyos.network/v1/tasks/msn_7xK9pL2mN4qR8wV3/stream',
  {
    headers: { 'Authorization': 'Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6' }
  }
)

eventSource.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data)
  console.log(`[${type}]`, data)

  if (type === 'status' && data.status === 'completed') {
    console.log('✅ Task completed:', data.result)
    eventSource.close()
  }
}
```

---

## Step 5: View Task Results

### Get Mission Status

```bash
curl https://engine.agencyos.network/v1/tasks/msn_7xK9pL2mN4qR8wV3 \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6"
```

### Response (Completed)

```json
{
  "id": "msn_7xK9pL2mN4qR8wV3",
  "tenant_id": "tnt_abc123xyz",
  "goal": "Create a Python script that lists all files in /tmp directory",
  "status": "completed",
  "credits_used": 1,
  "total_steps": 3,
  "completed_steps": 3,
  "created_at": "2026-03-19T10:35:00Z",
  "result": "Created /tmp/list_files.py with 15 lines",
  "completed_at": "2026-03-19T10:35:45Z"
}
```

### List All Missions

```bash
curl "https://engine.agencyos.network/v1/tasks?limit=10&offset=0" \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6"
```

**Response:**

```json
{
  "missions": [
    {
      "id": "msn_7xK9pL2mN4qR8wV3",
      "tenant_id": "tnt_abc123xyz",
      "goal": "Create a Python script...",
      "status": "completed",
      "credits_used": 1,
      "created_at": "2026-03-19T10:35:00Z"
    }
  ],
  "limit": 10,
  "offset": 0
}
```

---

## Step 6: Configure LLM Provider (BYOK)

Bring Your Own Key (BYOK) to use custom LLM providers instead of default Workers AI.

### Set LLM Settings

```bash
curl -X PUT https://engine.agencyos.network/v1/settings/llm \
  -H "Authorization: Bearer sk_live_7FpQ2mN9xK4wR8vL3jH6" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-proj-your-openai-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o"
  }'
```

### Supported Providers

| Provider | Default Model | Configuration |
|----------|---------------|---------------|
| **Workers AI** (default) | `@cf/meta/llama-3.1-8b-instruct` | No setup required |
| **OpenAI** | `gpt-4o` | Set `api_key` + `base_url` |
| **Anthropic** | `claude-sonnet-4-6` | Set `api_key` + `base_url` |
| **Qwen** (DashScope) | `qwen3.5-plus` | Set `api_key` + `base_url` |
| **DeepSeek** | `deepseek-chat` | Set `api_key` + `base_url` |

### Fallback Chain

RaaS uses this priority order:

1. **Tenant settings** (your BYOK config)
2. **Global env** (`LLM_API_KEY`, `LLM_BASE_URL`)
3. **Workers AI** (free, default)

---

## Troubleshooting

### HTTP 401 — Unauthorized

**Cause:** Invalid or missing API key

```json
{ "error": "Invalid API key" }
```

**Fix:**
- Check `Authorization: Bearer <key>` header format
- Ensure API key is correct (no extra spaces)
- Verify tenant exists in database

---

### HTTP 402 — Payment Required

**Cause:** Insufficient credits

```json
{ "error": "Insufficient credits" }
```

**Fix:**
- Check balance: `GET /billing/credits`
- Purchase credits via Polar.sh checkout
- Wait for webhook to credit your account

---

### HTTP 404 — Not Found

**Cause:** Mission ID doesn't exist or belongs to another tenant

```json
{ "error": "Mission not found" }
```

**Fix:**
- Verify mission ID format: `msn_*`
- Ensure mission belongs to your tenant

---

### HTTP 409 — Conflict

**Cause:** Cannot cancel non-pending mission

```json
{ "error": "Only pending missions can be cancelled" }
```

**Fix:**
- Only `pending` status missions can be cancelled
- Running/completed missions cannot be cancelled

---

### HTTP 503 — Service Unavailable

**Cause:** D1 database not configured or LLM provider unavailable

```json
{ "error": "D1 not configured" }
// or
{ "error": "No LLM provider configured (need AI binding or LLM_API_KEY)" }
```

**Fix:**
- Server-side issue — check Cloudflare Workers dashboard
- For BYOK, verify `LLM_API_KEY` is set in tenant settings

---

### HTTP 400 — Invalid Request

**Cause:** Missing or invalid request body

```json
{ "error": "Missing goal" }
// or
{ "error": "Goal must be 2000 characters or less" }
```

**Fix:**
- Include `goal` field in request body
- Ensure goal is 1-2000 characters

---

## Next Steps

After completing your first task:

1. **Explore Route Groups**
   - `/v1/agents` — Execute git, file, shell operations
   - `/v1/crm` — Manage contacts and campaigns
   - `/v1/governance` — Quadratic voting and proposals
   - `/v1/ledger` — Double-entry accounting
   - `/v1/equity` — Cap table and SAFE notes

2. **Read Full API Reference**
   - See [`docs/api-reference.md`](./api-reference.md) for complete endpoint documentation

3. **Subscribe for Credits**
   - Visit pricing page or checkout Polar.sh products
   - Webhooks auto-credit your account within 5 minutes

4. **Join AgencyOS Community**
   - Discord: https://agencyos.network/discord
   - Docs: https://docs.agencyos.network

---

## Quick Reference Card

```bash
# 1. Create tenant
curl -X POST https://engine.agencyos.network/billing/tenants \
  -H "Content-Type: application/json" -d '{"name":"my-agency"}'

# 2. Check balance
curl https://engine.agencyos.network/billing/credits \
  -H "Authorization: Bearer YOUR_API_KEY"

# 3. Create mission
curl -X POST https://engine.agencyos.network/v1/tasks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Your AI task goal"}'

# 4. Stream progress
curl -N https://engine.agencyos.network/v1/tasks/MISSION_ID/stream \
  -H "Authorization: Bearer YOUR_API_KEY"

# 5. Get results
curl https://engine.agencyos.network/v1/tasks/MISSION_ID \
  -H "Authorization: Bearer YOUR_API_KEY"
```

---

_See also: [API Reference](./api-reference.md) | [CLI Getting Started](./getting-started.md)_
