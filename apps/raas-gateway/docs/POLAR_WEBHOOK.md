# Polar.sh Billing Webhook Integration

## Overview

Polar.sh webhook integration for automated credit allocation and subscription management.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Polar.sh Webhook Flow                                  │
├─────────────────────────────────────────────────────────┤
│  1. Polar sends webhook → /billing/webhook             │
│  2. Verify HMAC-SHA256 signature                       │
│  3. Check timestamp (5 min window)                     │
│  4. Check idempotency (event_id uniqueness)            │
│  5. Process event type                                 │
│  6. Allocate credits / Update tier                     │
│  7. Record to webhook_events table                     │
│  8. Return 200 OK                                      │
└─────────────────────────────────────────────────────────┘
```

## Webhook Events

### order.paid
**Action:** Allocate credits, update tier if subscription

**Payload:**
```json
{
  "id": "evt_123",
  "type": "order.paid",
  "data": {
    "order": {
      "id": "ord_456",
      "product_name": "AgencyOS Pro",
      "amount": 9900,
      "currency": "USD",
      "metadata": {
        "tenant_id": "tenant-789"
      }
    }
  },
  "created_at": "2026-03-19T16:00:00Z"
}
```

**Response:**
```json
{
  "received": true,
  "event": "order.paid",
  "credits": 200,
  "tier": "pro"
}
```

### subscription.active
**Action:** Update tenant tier

**Response:**
```json
{
  "received": true,
  "event": "subscription.active",
  "tier": "enterprise"
}
```

### subscription.canceled
**Action:** Downgrade to starter tier

**Response:**
```json
{
  "received": true,
  "event": "subscription.canceled"
}
```

### refund.created
**Action:** Deduct credits from tenant

**Response:**
```json
{
  "received": true,
  "event": "refund.created",
  "deducted": 50
}
```

## Product Mapping

### Subscription Tiers

| Product Key | Credits | Tier | Price |
|-------------|--------:|------|------:|
| agencyos-starter | 50 | pro | $29/mo |
| agencyos-pro | 200 | pro | $99/mo |
| agencyos-agency | 500 | enterprise | $199/mo |
| agencyos-master | 1000 | enterprise | $399/mo |

### Credit Packs

| Product Key | Credits | Price |
|-------------|--------:|------:|
| credits-10 | 10 | $5 |
| credits-50 | 50 | $20 |
| credits-100 | 100 | $35 |
| credits-500 | 500 | $150 |

## Security

### Signature Verification

Polar.sh signs webhooks with HMAC-SHA256.

**Implementation:**
```typescript
const secret = env.POLAR_WEBHOOK_SECRET;
const keyData = new TextEncoder().encode(secret);
const msgData = new TextEncoder().encode(payload);

const cryptoKey = await crypto.subtle.importKey(
  'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
);

const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, msgData);
const expectedSig = Array.from(new Uint8Array(sigBuffer))
  .map((b) => b.toString(16).padStart(2, '0'))
  .join('');

const valid = signature === expectedSig;
```

### Replay Attack Prevention

1. **Timestamp Validation:** Events older than 5 minutes rejected
2. **Idempotency:** Event ID stored in `webhook_events` table
3. **Unique Constraint:** Database-level duplicate prevention

## Database Schema

### webhook_events
```sql
CREATE TABLE webhook_events (
  id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,  -- Polar event ID
  event_type TEXT NOT NULL,
  processed INTEGER DEFAULT 1,
  error_message TEXT,
  created_at TEXT DEFAULT datetime('now')
);
```

## API Endpoints

### POST /billing/webhook
Polar.sh webhook receiver.

**Headers required:**
- `webhook-signature`: HMAC-SHA256 signature

**Rate limits:**
- 100 requests/minute per IP
- Returns 429 with Retry-After header

### GET /billing/webhook/status
Check webhook service health.

**Response:**
```json
{
  "status": "healthy",
  "configured": true,
  "timestamp": "2026-03-19T16:00:00Z"
}
```

### GET /billing/pricing
Public pricing information.

**Response:**
```json
{
  "tiers": [...],
  "credit_packs": [...],
  "credit_costs": {
    "simple": 1,
    "standard": 3,
    "complex": 5
  }
}
```

## Error Handling

### 401 Unauthorized
- Invalid signature
- Timestamp too old (replay attack)

### 409 Conflict
- Duplicate event detected

### 429 Too Many Requests
- Rate limit exceeded

### 500 Internal Server Error
- Processing error (event recorded as failed)

## Testing

```bash
# Run billing tests
npm test -- tests/billing-service.test.ts

# All tests pass:
# ✓ POLAR_PRODUCT_CREDITS - correct mappings
# ✓ getProductCredits - case-insensitive lookup
# ✓ verifySignature - valid/invalid signatures
# ✓ isValidTimestamp - 5 min window
# ✓ extractTenantId - multiple sources
# ✓ isDuplicateEvent - idempotency check
```

## Integration Steps

### 1. Configure Polar Dashboard

1. Go to Polar Dashboard → Settings → Webhooks
2. Add webhook URL: `https://your-domain.com/billing/webhook`
3. Copy webhook secret
4. Select events: order.paid, subscription.*, refund.*

### 2. Set Environment Variables

```bash
# .dev.vars or Cloudflare Workers dashboard
POLAR_WEBHOOK_SECRET=whsec_your-secret-here
```

### 3. Run Migrations

```bash
# Apply webhook_events migration
pnpm wrangler d1 execute mekong-raas-db --local --file=./migrations/0007_create_webhook_events.sql
```

### 4. Test Webhook

```bash
# Using Polar CLI
polar webhooks send evt_test --url https://your-domain.com/billing/webhook

# Or curl with signature
curl -X POST https://your-domain.com/billing/webhook \
  -H "Content-Type: application/json" \
  -H "webhook-signature: whsec_..." \
  -d '{"type":"order.paid","data":{...}}'
```

## Monitoring

### Key Metrics

- **Webhook success rate:** Should be > 99%
- **Duplicate event rate:** Should be 0 (indicates retry issues)
- **Processing latency:** P95 < 500ms

### Alerting

Set up alerts for:
- Webhook failure rate > 5%
- Signature validation failures (security)
- High duplicate event count

## Troubleshooting

### "Invalid signature" errors
1. Verify POLAR_WEBHOOK_SECRET matches Polar dashboard
2. Check webhook-signature header format
3. Ensure raw body is used for verification (not parsed JSON)

### "Duplicate event" errors
- Normal during Polar retries
- Indicates previous event was processed
- Check `webhook_events` table for original processing

### "No tenant_id found" errors
- Customer must have `external_id` set to tenant_id
- Or order must have `metadata.tenant_id`
- Check Polar customer data

## Production Checklist

- [x] Webhook signature verification implemented
- [x] Idempotency via webhook_events table
- [x] Timestamp validation (5 min window)
- [x] Rate limiting (100 req/min)
- [x] Error handling and logging
- [ ] Polar dashboard configured
- [ ] Webhook URL verified (HTTPS)
- [ ] Monitoring/alerting setup
- [ ] Runbook for webhook failures

## Future Enhancements

- [ ] Webhook retry logic for failed processing
- [ ] Dead letter queue for unprocessable events
- [ ] Webhook event analytics dashboard
- [ ] Support for additional Polar events
- [ ] Multi-provider webhook support (Stripe, etc.)
