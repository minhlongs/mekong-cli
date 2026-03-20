# Credit Metering Implementation

## Overview

Credit metering system for RaaS Gateway using D1 database for persistent credit balances and transaction tracking.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Credit Metering Flow                                   │
├─────────────────────────────────────────────────────────┤
│  1. Auth → Rate Limit → Credit Check → Handler         │
│  2. Deduct credits BEFORE handler executes             │
│  3. Return 402 Payment Required if insufficient        │
│  4. Record transaction in credit_transactions table    │
│  5. Log usage in usage_logs table                      │
└─────────────────────────────────────────────────────────┘
```

## Credit Costs

| Mission Type | Credits |
|-------------|---------|
| simple      | 1       |
| standard    | 3       |
| complex     | 5       |

## Database Schema

### tenants (updated)
```sql
ALTER TABLE tenants ADD COLUMN balance INTEGER DEFAULT 0;
ALTER TABLE tenants ADD COLUMN total_earned INTEGER DEFAULT 0;
ALTER TABLE tenants ADD COLUMN total_spent INTEGER DEFAULT 0;
```

### credit_transactions
```sql
CREATE TABLE credit_transactions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  amount INTEGER NOT NULL,      -- positive=credit, negative=debit
  type TEXT NOT NULL,            -- purchase|mission|refund|rollover|adjustment|webhook
  mission_id TEXT,
  description TEXT,
  metadata TEXT,                 -- JSON
  created_at TEXT DEFAULT datetime('now')
);
```

### usage_logs
```sql
CREATE TABLE usage_logs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT,
  credits_cost INTEGER NOT NULL,
  timestamp TEXT DEFAULT datetime('now'),
  success INTEGER DEFAULT 1,
  metadata TEXT                  -- JSON
);
```

## Implementation

### Files Created

- `src/services/credit-service.ts` — Core credit operations
- `src/middleware/credit-metering.ts` — Middleware wrapper
- `src/routes/credits.ts` — Credit management endpoints
- `migrations/0006_add_credit_columns_to_tenants.sql` — Schema update
- `tests/credit-service.test.ts` — Unit tests (13 tests)

### Files Modified

- `src/routes/index.ts` — Mount /credits routes
- `src/routes/api.ts` — Remove /credits/* placeholder
- `src/middleware/index.ts` — Export credit metering

## API Endpoints

### GET /v1/credits
Get current credit balance.

**Response:**
```json
{
  "tenantId": "tenant-123",
  "balance": 100,
  "totalEarned": 500,
  "totalSpent": 400
}
```

### GET /v1/credits/history
Get transaction history.

**Query params:**
- `limit` (optional): 1-200, default 50
- `offset` (optional): default 0

**Response:**
```json
{
  "tenantId": "tenant-123",
  "history": [
    {
      "id": "txn-abc",
      "tenantId": "tenant-123",
      "amount": -3,
      "type": "mission",
      "description": "Standard mission execution",
      "createdAt": "2026-03-19T10:00:00Z"
    }
  ],
  "pagination": { "limit": 50, "offset": 0 }
}
```

### GET /v1/credits/usage
Get usage logs.

**Query params:**
- `limit` (optional): 1-200, default 50
- `mission_id` (optional): Filter by mission

### POST /v1/credits/check
Check credit cost for a mission (exempt from metering).

**Request:**
```json
{ "complexity": "standard" }
```

**Response:**
```json
{
  "tenantId": "tenant-123",
  "complexity": "standard",
  "cost": 3,
  "balance": 100,
  "sufficient": true
}
```

### POST /v1/credits/topup
Manual credit topup (for testing, admin only).

**Request:**
```json
{ "amount": 100, "reason": "Testing credits" }
```

**Limits:** 1-1000 credits per request

## Middleware Usage

```typescript
import { creditMetering, getMissionCost } from './middleware/credit-metering';

// Fixed cost endpoint (1 credit)
api.get('/data', creditMetering({ cost: 1 }), (c) => {
  return c.json({ data: '...' });
});

// Variable cost based on complexity
api.post('/mission', creditMetering({
  cost: getMissionCost('complex'), // 5 credits
  description: 'Complex mission execution'
}), (c) => {
  // Handler executes after credits deducted
});

// Exempt tiers (e.g., enterprise has unlimited)
api.get('/premium', creditMetering({
  cost: 10,
  exemptTiers: ['enterprise']
}), (c) => {
  // Enterprise tier skips credit check
});

// Free endpoint (no deduction)
api.post('/check', creditMetering({ cost: 0 }), (c) => {
  // No credits deducted
});
```

## Response Headers

All metered responses include:

```
X-Credit-Cost: 3
X-Credit-Balance: 97
```

## Error Response (402 Payment Required)

```json
{
  "error": "Insufficient credits",
  "code": "INSUFFICIENT_CREDITS",
  "required": 5,
  "available": 2,
  "message": "Required: 5 credits, Available: 2 credits. Please purchase more credits."
}
```

## Transaction Types

| Type       | Description                      | Source          |
|------------|----------------------------------|-----------------|
| purchase   | Credit purchase                  | Polar webhook   |
| mission    | Mission execution cost           | Auto-deducted   |
| refund     | Credit refund                    | Manual/Polar    |
| rollover   | Monthly rollover                 | Scheduled job   |
| adjustment | Manual adjustment                | Admin           |
| webhook    | External webhook credit          | Polar/Billing   |

## Testing

```bash
# Run credit service tests
npm test -- tests/credit-service.test.ts

# All tests pass:
# ✓ getMissionCost - returns correct costs
# ✓ hasSufficientCredits - checks balance
# ✓ deduct - handles insufficient credits
# ✓ addCredits - adds credits to account
# ✓ getHistory - returns transaction history
```

## Integration with Polar Webhook

Phase 8 will implement Polar.sh webhook integration:

```typescript
// Webhook handler (Phase 8)
billingRoutes.post('/webhook', async (c) => {
  if (event.type === 'order.paid') {
    await creditService.addCredits(
      tenantId,
      credits,
      'purchase',
      `Polar.sh: ${productName}`
    );
  }
});
```

## Production Considerations

1. **Concurrency:** D1 doesn't support transactions — race conditions possible
   - Mitigation: Check balance before deduct, accept small margin of error
   - Future: Use D1 batch for atomic multi-step operations

2. **Audit Trail:** All transactions logged to `credit_transactions`
   - Immutable record for billing disputes
   - Metadata JSON for extensibility

3. **Cost Tracking:** Usage logs track per-mission costs
   - Analytics: Most popular mission types
   - Optimization: Identify expensive operations

4. **Credit Expiry:** TODO — Implement monthly expiry/rollover
   - Migration needed for `credit_expires_at` column
   - Scheduled job for expiry processing

## Future Enhancements

- [ ] D1 batch operations for atomic deduct + log
- [ ] Credit expiry and rollover logic
- [ ] Low credit alerts (email/webhook)
- [ ] Usage analytics dashboard
- [ ] Tier-based credit multipliers
- [ ] Pre-authorization hold pattern for long missions
