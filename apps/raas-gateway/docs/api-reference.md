# RaaS Gateway — API Reference

Cloudflare Worker API for Mekong CLI billing and agent missions.

**Base URL:** `https://raas-gateway.agencyos-openclaw.workers.dev`
**Runtime:** Cloudflare Workers + D1 + KV | **Framework:** Hono

---

## Quick Start

```bash
BASE=https://raas-gateway.agencyos-openclaw.workers.dev

# 1. Sign up — get JWT + 10 free credits
curl -s -X POST $BASE/v1/tenants/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","email":"dev@acme.io"}' | jq .

# 2. Submit a mission (use JWT from step 1)
TOKEN=<jwt_from_signup>
curl -s -X POST $BASE/v1/missions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Audit codebase for security issues","complexity":"standard"}' | jq .

# 3. Check credit balance
curl -s $BASE/credits \
  -H "Authorization: Bearer $TOKEN" | jq .
```

---

## Authentication

All protected endpoints accept either header:

| Header | Format | Notes |
|--------|--------|-------|
| `Authorization` | `Bearer <jwt>` | JWT from signup or refresh |
| `X-API-Key` | `mk_...` | Generated via `/v1/tenants/api-keys` |

---

## API Reference

### Tenants

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/tenants/signup` | Public | Create tenant — returns JWT + 10 credits |
| `GET` | `/v1/tenants/profile` | Required | Get authenticated tenant profile |
| `POST` | `/v1/tenants/api-keys` | Required | Generate API key (`mk_...`) |
| `GET` | `/v1/tenants/api-keys` | Required | List API keys (secrets not returned) |
| `DELETE` | `/v1/tenants/api-keys/:id` | Required | Revoke API key by ID |

**POST /v1/tenants/signup**

```json
// Request
{ "name": "Acme Corp", "email": "dev@acme.io" }

// Response 201
{
  "tenantId": "uuid",
  "name": "Acme Corp",
  "email": "dev@acme.io",
  "tier": "free",
  "credits": 10,
  "token": "<jwt>"
}
```

**POST /v1/tenants/api-keys** — Key shown once, cannot be retrieved later.

```json
// Request
{ "name": "CI Key" }

// Response 201
{ "keyId": "uuid", "apiKey": "mk_...", "name": "CI Key" }
```

---

### Missions

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/v1/missions` | Required | Submit mission — deducts MCU credits |
| `GET` | `/v1/missions` | Required | List missions (`?status=&limit=&offset=`) |
| `GET` | `/v1/missions/:id` | Required | Get mission details |
| `POST` | `/v1/missions/:id/cancel` | Required | Cancel queued mission + refund credits |

**POST /v1/missions**

```json
// Request
{
  "goal": "Build auth module with JWT and refresh tokens",
  "complexity": "standard",   // simple | standard | complex
  "project": "my-app"         // optional
}

// Response 201
{
  "id": "uuid",
  "tenantId": "uuid",
  "goal": "...",
  "complexity": "standard",
  "status": "queued",
  "creditsCharged": 3
}
```

Credit costs: `simple=1 MCU`, `standard=3 MCU`, `complex=5 MCU`.
Returns HTTP `402` if balance insufficient.

**GET /v1/missions**

Query params: `status` (queued|executing|completed|failed|cancelled), `limit` (default 20), `offset` (default 0).

---

### Credits

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/credits` | Required | Current balance + totals |
| `GET` | `/credits/history` | Required | Transaction history (`?limit=&offset=`) |
| `GET` | `/credits/usage` | Required | Usage logs (`?limit=&mission_id=`) |
| `POST` | `/credits/check` | Required | Pre-check cost for a complexity level |
| `POST` | `/credits/topup` | Admin only | Manual credit topup (1–1000 credits) |

**GET /credits** response:
```json
{
  "tenantId": "uuid",
  "balance": 47,
  "totalEarned": 60,
  "totalSpent": 13
}
```

**POST /credits/check**
```json
// Request
{ "complexity": "complex" }

// Response
{ "tenantId": "uuid", "complexity": "complex", "cost": 5, "balance": 47, "sufficient": true }
```

**POST /credits/topup** — requires `admin` permission in JWT claims.
```json
// Request
{ "amount": 100, "reason": "Promotional grant" }

// Response
{ "tenantId": "uuid", "amountAdded": 100, "newBalance": 147 }
```

---

### Billing

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/billing/pricing` | Public | Pricing tiers + credit packs |
| `POST` | `/billing/webhook` | Polar sig | Polar.sh Standard Webhooks handler |
| `GET` | `/billing/webhook/status` | Public | Webhook service health |

**GET /billing/pricing** — returns tier and credit pack catalog:

| Tier | Price | Credits |
|------|-------|---------|
| Free | $0 | 10 |
| Starter (`agencyos-starter`) | $29/mo | 50 |
| Pro (`agencyos-pro`) | $99/mo | 200 |
| Agency (`agencyos-agency`) | $199/mo | 500 |
| Master (`agencyos-master`) | $399/mo | 1000 |

Webhook events handled: `order.paid`, `subscription.active`, `subscription.canceled`, `refund.created`.

---

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | Public | Health check |

---

## Deployment

```bash
# Install deps
npm install

# Local dev (with D1 + KV via miniflare)
npm run dev

# Apply DB migrations
npm run db:migrate                                          # local
npx wrangler d1 migrations apply mekong-raas-db --remote   # production

# Deploy
npm run deploy
```

**Required secrets** (set via Wrangler or Cloudflare dashboard):

| Secret | Description |
|--------|-------------|
| `JWT_SECRET=REDACTED` | HS256 signing key for tenant JWTs |
| `POLAR_WEBHOOK_SECRET` | Polar.sh Standard Webhooks signing secret |

**Required bindings** (configure in `wrangler.toml`):

| Binding | Type | Name |
|---------|------|------|
| `DB` | D1 | `mekong-raas-db` |
| `RATE_LIMIT_KV` | KV | Rate limit counters |
| `SESSION_KV` | KV | Session cache |

---

## Error Format

```json
{ "error": "Human-readable message", "code": "MACHINE_READABLE_CODE" }
```

Common codes: `INVALID_EMAIL`, `EMAIL_EXISTS`, `INSUFFICIENT_CREDITS`, `NOT_FOUND`, `FORBIDDEN`, `INVALID_SIGNATURE`, `REPLAY_ATTACK`.
