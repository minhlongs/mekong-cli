# Phase 02: Credit/Billing System

## Context Links
- [Research: Pricing Models](research/researcher-01-open-core-raas-models.md) — Section 5
- [Research: Credit Bundles](research/researcher-02-non-tech-user-onboarding.md) — Section 4
- [Polar.sh mandate](../../.claude/rules/payment-provider.md)

## Overview
- **Priority:** P1
- **Status:** pending
- **Group:** A (parallel with Phase 01, 03)
- **Est:** 3h

AgencyCoin credit system. Tenants buy credit bundles via Polar.sh, spend credits per mission.

## Key Insights
- Credit packs best for VN SME (predictable spend, no token complexity)
- 1 credit = 1 simple mission, 5 credits = complex mission
- Markup: buy API ~$0.015/task, sell $0.50/task = 33x margin
- Polar.sh webhook: `subscription.created` -> provision credits
- VND 500K-2M/month ceiling for target market

## Requirements

### Functional
- Credit balance per tenant (integer, atomic increment/decrement)
- Deduct credits before mission dispatch (pre-auth pattern)
- Refund credits on mission failure (configurable)
- Credit cost per mission type: simple=1, standard=3, complex=5
- Polar.sh webhook handler: receive payment -> add credits
- Credit history log (who, when, amount, reason)

### Non-Functional
- Atomic credit operations (no double-spend)
- Credit check < 2ms (SQLite, cached)
- Webhook idempotency (Polar event_id dedup)

## Architecture

```
Polar.sh payment -> webhook POST /raas/billing/webhook
    -> verify signature
    -> provision credits to tenant
    -> log transaction

Mission dispatch -> check credits >= cost
    -> deduct credits (atomic)
    -> dispatch mission
    -> on failure: refund credits
```

## File Ownership (EXCLUSIVE)

| Action | File |
|--------|------|
| CREATE | `src/raas/credits.py` |
| CREATE | `src/raas/billing.py` |

## Implementation Steps

1. Create `src/raas/credits.py`:
   - `CreditAccount` dataclass: tenant_id, balance, total_earned, total_spent
   - `CreditStore` class (SQLite, same DB as tenants):
     - `get_balance(tenant_id) -> int`
     - `deduct(tenant_id, amount, reason) -> bool` — atomic, returns False if insufficient
     - `add(tenant_id, amount, reason) -> int` — returns new balance
     - `get_history(tenant_id, limit=50) -> List[CreditTransaction]`
   - `CreditTransaction` dataclass: id, tenant_id, amount (+/-), reason, timestamp
   - `MISSION_COSTS` dict: `{"simple": 1, "standard": 3, "complex": 5}`

2. Create `src/raas/billing.py`:
   - `PolarWebhookHandler` class:
     - `verify_signature(payload, signature, secret) -> bool`
     - `handle_event(event_data) -> dict` — routes by event type
     - `provision_credits(tenant_id, product_id) -> int` — maps Polar product to credit amount
   - `POLAR_PRODUCT_MAP` dict: maps product_id -> credit amount
   - FastAPI router: `POST /raas/billing/webhook`
   - Idempotency: store processed event_ids in SQLite

## Todo List
- [ ] Create `CreditStore` with atomic SQLite operations
- [ ] Create `CreditTransaction` logging
- [ ] Implement Polar webhook handler with signature verification
- [ ] Map Polar products to credit amounts
- [ ] Idempotency guard on webhook events
- [ ] Unit tests: `tests/test_raas_credits.py`

## Success Criteria
- `deduct(tenant, 3, "mission")` returns True when balance >= 3, False otherwise
- `add(tenant, 100, "purchase")` atomically increases balance
- Polar webhook provisions credits correctly
- Double-webhook with same event_id only provisions once
- Tests pass: `pytest tests/test_raas_credits.py`

## Risk Assessment
- **SQLite write contention:** Low risk for v1 volume. Mitigate: WAL mode + retry.
- **Polar webhook reliability:** Polar retries failed webhooks. Idempotency key prevents duplication.
- **LLM cost volatility:** Credit cost is fixed; margin absorbs variance. Monitor in Phase 04 dashboard.

## Security Considerations
- Webhook signature verification mandatory (Polar standard webhooks)
- Credit operations only via authenticated endpoints (Phase 01 auth)
- No direct credit manipulation API exposed to tenants (admin only)
