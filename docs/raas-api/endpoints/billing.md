# Billing API — Tenant & Credits

> **Purpose**: Quản lý tenants, API keys, subscriptions, và credit metering. Tích hợp Polar.sh webhooks.

---

## Endpoints Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/billing/tenants` | ❌ | Create tenant (nhận 10 credits free) |
| POST | `/billing/tenants/regenerate-key` | ❌ | Regenerate API key |
| GET | `/billing/pricing` | ❌ | Get pricing tiers |
| GET | `/billing/credits` | ✅ | Get credit balance |
| GET | `/billing/credits/history` | ✅ | Transaction history |
| POST | `/billing/webhook` | ❌ | Polar.sh webhook |

---

## POST /billing/tenants — Create Tenant

### Request

```bash
curl -X POST https://agencyos.network/billing/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Cafe"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Tenant name (1-255 chars) |

### Response (201 Created)

```json
{
  "tenant_id": "tenant_abc123",
  "name": "My Cafe",
  "api_key": "sk_live_7x8y9z0a1b2c3d4e5f6g",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

### Welcome Bonus

- **10 free credits** granted on creation
- Enough for 3-10 standard missions
- No credit card required

### ⚠️ Critical: Save API Key

API key chỉ hiện **MỘT LẦN DUY NHẤT**. If lost, must regenerate.

---

## POST /billing/tenants/regenerate-key — Regenerate API Key

### Request

```bash
curl -X POST https://agencyos.network/billing/tenants/regenerate-key \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "tenant_abc123",
    "name": "My Cafe"
  }'
```

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | string | ✅ | Tenant ID |
| `name` | string | ✅ | Tenant name (ownership proof) |

### Response (200 OK)

```json
{
  "api_key": "sk_live_newkey123456789",
  "revoked_at": "2026-03-19T10:30:00Z",
  "message": "New API key generated. Old key is now invalid. Save this key!"
}
```

### Security

- Old key immediately revoked
- Requires `tenant_id` + `name` as ownership proof
- All active sessions with old key invalidated

---

## GET /billing/pricing — Pricing Tiers

### Request

```bash
curl -X GET https://agencyos.network/billing/pricing
```

### Response

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

### Vietnam Pricing (VND)

| Tier | USD | VND | Credits |
|------|-----|-----|---------|
| Free | $0 | 0đ | 10 |
| Starter | $29 | 199kđ | 50 |
| Pro | $99 | 499kđ | 200 |
| Agency | $199 | 2.99Mđ | 500 |
| Master | $399 | 5.99Mđ | 1000 |

---

## GET /billing/credits — Check Balance

### Request

```bash
curl -X GET https://agencyos.network/billing/credits \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response

```json
{
  "tenant_id": "tenant_abc123",
  "balance": 7,
  "tier": "free",
  "used_this_month": 3,
  "resets_at": "2026-04-01T00:00:00Z"
}
```

---

## GET /billing/credits/history — Transaction History

### Request

```bash
curl -X GET "https://agencyos.network/billing/credits/history?limit=10" \
  -H "Authorization: Bearer $RAAS_API_KEY"
```

### Response

```json
{
  "tenant_id": "tenant_abc123",
  "history": [
    {
      "id": "txn_001",
      "amount": -3,
      "balance_after": 7,
      "reason": "mission: Write a blog post about coffee...",
      "type": "usage",
      "created_at": "2026-03-19T10:30:00Z"
    },
    {
      "id": "txn_002",
      "amount": 10,
      "balance_after": 10,
      "reason": "welcome: free tier bonus",
      "type": "grant",
      "created_at": "2026-03-19T10:00:00Z"
    }
  ],
  "limit": 10
}
```

### Transaction Types

| Type | Description | Amount |
|------|-------------|--------|
| `grant` | Welcome bonus, rewards | Positive |
| `usage` | Mission execution | Negative |
| `refund` | Cancelled missions | Positive |
| `purchase` | Polar.sh purchase | Positive |
| `transfer` | Inter-account transfer | Variable |

---

## POST /billing/webhook — Polar.sh Integration

### Purpose

Xử lý payments từ Polar.sh (subscription, credit packs).

### Request (from Polar.sh)

```http
POST /billing/webhook
Content-Type: application/json
webhook-signature: sha256=abc123...

{
  "type": "order.paid",
  "data": {
    "tenant_id": "tenant_abc123",
    "product_name": "agencyos-starter",
    "credits": 50
  }
}
```

### Event Types

| Event | Description | Action |
|-------|-------------|--------|
| `order.paid` | Payment completed | Add credits, upgrade tier |
| `subscription.created` | New subscription | Set recurring billing |
| `subscription.updated` | Subscription changed | Update tier |
| `subscription.canceled` | Subscription ended | Downgrade to free |

### Security: HMAC Verification

```typescript
const secret = c.env.POLAR_WEBHOOK_SECRET
const signature = c.req.header('webhook-signature')
const rawBody = await c.req.text()

// Verify HMAC-SHA256 signature
const keyData = new TextEncoder().encode(secret)
const msgData = new TextEncoder().encode(rawBody)
const cryptoKey = await crypto.subtle.importKey(
  'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
)
const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData)
const expectedSig = Array.from(new Uint8Array(sigBuffer))
  .map(b => b.toString(16).padStart(2, '0')).join('')

if (signature !== expectedSig) {
  return c.json({ error: 'Invalid signature' }, 401)
}
```

### Product Mapping

| Polar Product | Credits | Tier Upgrade |
|---------------|---------|--------------|
| `agencyos-starter` | 50 | pro |
| `agencyos-pro` | 200 | pro |
| `agencyos-agency` | 500 | enterprise |
| `agencyos-master` | 1000 | enterprise |
| `credits-10` | 10 | — |
| `credits-50` | 50 | — |
| `credits-100` | 100 | — |

---

## Subscription Tiers

### Tier Benefits

| Benefit | Free | Starter | Pro | Agency | Master |
|---------|------|---------|-----|--------|--------|
| Credits/month | 10 | 50 | 200 | 500 | 1000 |
| Max missions/day | 3 | 10 | 50 | 200 | 1000 |
| SSE streaming | ✅ | ✅ | ✅ | ✅ | ✅ |
| Priority queue | ❌ | ❌ | ✅ | ✅ | ✅ |
| Custom LLM (BYOK) | ❌ | ❌ | ✅ | ✅ | ✅ |
| SLA | — | — | 99% | 99.9% | 99.99% |
| Support | Community | Email | Priority | Dedicated | 24/7 |

### Upgrade Flow

1. Select tier on Polar.sh checkout
2. Complete payment
3. Polar.sh sends webhook
4. Credits added, tier upgraded instantly
5. Email confirmation sent

### Downgrade Flow

- Subscription cancelled → tier downgrades to `free` at period end
- Unused credits expire at period end
- Data retained indefinitely

---

## Error Responses

### 400 Invalid Request

```json
{
  "error": "BAD_REQUEST",
  "message": "Tenant name is required"
}
```

### 404 Not Found

```json
{
  "error": "NOT_FOUND",
  "message": "Tenant not found or name mismatch"
}
```

### 401 Invalid Signature (Webhook)

```json
{
  "error": "UNAUTHORIZED",
  "code": "INVALID_SIGNATURE",
  "message": "HMAC signature verification failed"
}
```

---

## Related Endpoints

- [POST /v1/tasks](./tasks.md) — Create missions with credits
- [GET /v1/ledger/balance](./ledger.md) — Account balances
- [POST /v1/ledger/topup](./ledger.md) — Add credits to account

---

## Next Steps

- [Tasks API](./tasks.md) — Use credits for missions
- [Ledger API](./ledger.md) — Double-entry accounting
- [Polar.sh Integration Guide](../guides/polar-integration.md) — Payment setup
