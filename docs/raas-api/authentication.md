# Authentication & Security

> **Security Model**: Bearer token API keys với HMAC signature verification cho webhooks.

---

## Authentication Methods

### 1. Bearer Token (Primary)

**Used by:** All authenticated endpoints

```http
Authorization: Bearer sk_live_7x8y9z0a1b2c3d4e5f6g
```

**API Key Format:**
```
sk_live_xxxxxxxxxxxxxxxx  (Production)
sk_test_xxxxxxxxxxxxxxxx  (Staging/Test)
```

---

## 2. HMAC Signature (Webhooks)

**Used by:** Polar.sh, MoMo, VNPAY webhooks

### Signature Verification Flow

```
1. Server receives webhook payload + signature header
2. Compute HMAC-SHA256(payload, secret_key)
3. Compare computed signature with received signature
4. Accept if match, reject if mismatch or replay attack detected
```

### Example: Polar.sh Webhook

**Request Headers:**
```http
POST /billing/webhook
Content-Type: application/json
webhook-signature: sha256=abc123def456...
```

**Verification Code (Cloudflare Workers):**
```typescript
const secret = c.env.POLAR_WEBHOOK_SECRET
const signature = c.req.header('webhook-signature')
const rawBody = await c.req.text()

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

### Replay Attack Prevention

**5-minute window:**
```typescript
const timestamp = event.timestamp ?? event.created_at
const eventTime = new Date(timestamp).getTime()
const now = Date.now()
const age = now - eventTime

if (age > 5 * 60 * 1000) { // 5 minutes
  return c.json({ error: 'Webhook timestamp too old', code: 'REPLAY_ATTACK' }, 401)
}
if (age < 0) {
  return c.json({ error: 'Webhook timestamp in future' }, 400)
}
```

---

## API Key Management

### Create Tenant (Get API Key)

```bash
POST /billing/tenants
Content-Type: application/json

{
  "name": "My Cafe"
}
```

**Response:**
```json
{
  "tenant_id": "tenant_abc123",
  "api_key": "sk_live_7x8y9z0a1b2c3d4e5f6g",
  "tier": "free",
  "credits": 10,
  "message": "Save your API key — it cannot be recovered if lost!"
}
```

⚠️ **CRITICAL:** API key chỉ hiện **MỘT LẦN DUY NHẤT**. Lưu ngay vào secure storage.

---

### Regenerate Lost API Key

```bash
POST /billing/tenants/regenerate-key
Content-Type: application/json

{
  "tenant_id": "tenant_abc123",
  "name": "My Cafe"
}
```

**Response:**
```json
{
  "api_key": "sk_live_newkey123456789",
  "revoked_at": "2026-03-19T10:30:00Z",
  "message": "New API key generated. Old key is now invalid. Save this key!"
}
```

**Ownership Proof Required:**
- `tenant_id` + `name` must match database record
- Old key immediately revoked

---

## Security Best Practices

### 1. Store API Keys Securely

```bash
# ✅ GOOD: Environment variable
export RAAS_API_KEY="sk_live_7x8y9z0a1b2c3d4e5f6g"

# ✅ GOOD: Secret manager (AWS Secrets Manager, Vault)
aws secretsmanager get-secret-value --secret-id raas/api-key

# ❌ BAD: Hardcoded in source code
const apiKey = "sk_live_7x8y9z0a1b2c3d4e5f6g"

# ❌ BAD: Committed to git
echo "RAAS_API_KEY=sk_live_..." >> .env  # If .env not in .gitignore
```

### 2. Use HTTPS Only

All API requests must use HTTPS. HTTP requests are rejected.

```bash
# ✅ GOOD
curl https://agencyos.network/v1/tasks -H "Authorization: Bearer $RAAS_API_KEY"

# ❌ BAD (rejected)
curl http://agencyos.network/v1/tasks -H "Authorization: Bearer $RAAS_API_KEY"
```

### 3. Rotate Keys Periodically

Recommended rotation schedule:
- **Free/Starter**: Every 90 days
- **Pro/Enterprise**: Every 30 days

### 4. Monitor Usage

```bash
GET /billing/credits/history?limit=50
Authorization: Bearer $RAAS_API_KEY
```

Check for unauthorized usage patterns.

---

## Error Responses

### 401 Unauthorized

```json
{
  "error": "UNAUTHORIZED",
  "code": "INVALID_API_KEY",
  "message": "API key is missing or invalid"
}
```

### 401 Signature Mismatch (Webhooks)

```json
{
  "error": "UNAUTHORIZED",
  "code": "INVALID_SIGNATURE",
  "message": "HMAC signature verification failed"
}
```

### 401 Replay Attack Detected

```json
{
  "error": "UNAUTHORIZED",
  "code": "REPLAY_ATTACK",
  "message": "Webhook timestamp too old (replay attack prevented)"
}
```

---

## Webhook Endpoints (No Auth Required)

| Endpoint | Method | Purpose | Signature |
|----------|--------|---------|-----------|
| `/billing/webhook` | POST | Polar.sh payments | HMAC-SHA256 |
| `/v1/chat/webhook/zalo` | POST | Zalo OA messages | HMAC |
| `/v1/chat/webhook/facebook` | GET/POST | Facebook Messenger | Verify token |
| `/payment/momo/ipn` | POST | MoMo IPN | HMAC |
| `/payment/vnpay/ipn` | GET | VNPAY IPN | HMAC-SHA512 |

All webhook endpoints verify signatures before processing.

---

## Tenant Isolation

Each tenant's data is completely isolated:

```sql
SELECT * FROM tasks WHERE tenant_id = ?  -- Tenant-scoped queries
SELECT * FROM credits WHERE tenant_id = ?
SELECT * FROM stakeholders WHERE tenant_id = ?
```

Cross-tenant access is **impossible** via API layer.

---

## Audit Trail

All authenticated requests are logged:

```typescript
{
  "tenant_id": "tenant_abc123",
  "endpoint": "/v1/tasks",
  "method": "POST",
  "timestamp": "2026-03-19T10:30:00Z",
  "ip_address": "1.2.3.4",
  "user_agent": "curl/7.68.0",
  "status_code": 201
}
```

Audit logs retained for **90 days**.

---

## Next Steps

- [Tasks API](./tasks.md) — Create and track missions
- [Billing API](./billing.md) — Manage credits and subscriptions
- [Governance API](./governance.md) — Quadratic voting and proposals
