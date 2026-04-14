# Mission Execution & Credit Flow Verification
**Date:** 2026-03-23 | **Agent:** debugger

---

## Executive Summary

Core credit + mission flow is **implemented and sound**. All five checkpoints pass: signup allocates free credits, missions deduct atomically, HTTP 402 fires on zero balance. Two gaps found: (1) signup free tier grants **10 MCU** (not 50 as stated in task description), (2) Polar `order.paid` + `subscription.created` may **double-credit** on subscription purchase.

---

## Full Flow (ASCII Diagram)

```
SIGNUP                          MISSION SUBMIT                      BILLING
------                          --------------                      -------
POST /tenants/signup            POST /v1/missions                   POST /billing/webhook
   │                               │                                    │
   ├─ Validate name/email           ├─ auth() middleware                ├─ verifySignature (HMAC)
   ├─ Check duplicate email         │   → JWT or X-API-Key              ├─ isDuplicateEvent (idempotency)
   ├─ INSERT tenants                ├─ getTenant(c)                     │
   │   tier='free'                  ├─ validate goal / complexity       ├─ order.paid
   │   balance=10 ◄── FREE CREDITS  ├─ check daily limit (free=3/day)   │   └─ extractTenantId
   ├─ INSERT credit_transactions    │                                    │       (metadata.tenant_id
   │   amount=10 'Welcome bonus'    ├─ CreditService.deduct()           │        OR customer.external_id)
   ├─ [if ref code] +5 to both      │   UPDATE tenants                  │   └─ addCredits() ✅
   ├─ generateJwt()                 │   SET balance = balance - cost     │
   └─ sendWelcome email (async)     │   WHERE id=? AND balance >= cost  ├─ subscription.created
                                    │   ← ATOMIC (race-safe)            │   └─ resolveTierFromProductId
                                    │                                    │       (first 8 chars of product_id)
ZERO BALANCE GUARD                 ├─ if changes=0 → INSUFFICIENT      │   └─ UPDATE tenants SET tier=?
------------------                 │   → return 402 ✅                  │   └─ addCredits() ✅ (monthly)
creditMetering middleware:         │
  hasSufficientCredits()           ├─ INSERT missions status='queued'  ├─ subscription.updated (renewal)
  balance < cost → HTTP 402 ✅     ├─ INSERT usage_logs                │   └─ addCredits() rollover ✅
  balance <= 5  → alerts table     └─ return 201 + mission             │
  balance == 0  → X-Credits-Alert                                      ├─ subscription.cancelled
                                                                        │   → mark cancelled, keep tier
CANCEL/REFUND                                                          │   → dunning_events created
-------------                                                          │
POST /missions/:id/cancel                                              ├─ subscription.revoked
  → status must be 'queued'                                            │   → tier='free' immediately
  → addCredits() refund ✅                                             │   → dunning_events created
                                                                        │
                                                                        └─ refund.created
                                                                            → deduct() credits ✅
```

---

## Checkpoint Results

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | Free credits on signup | PASS (partial) | 10 MCU allocated, not 50 — task description said 50 |
| 2 | Credit deduction per mission | PASS | Atomic SQL: `balance >= cost` guard prevents overdraw |
| 3 | HTTP 402 on zero balance | PASS | Both `creditMetering` middleware AND `MissionService.submit()` return 402 |
| 4 | Polar webhook credit grant | PASS | `order.paid` and `subscription.created` both add credits |
| 5 | Cancel refunds credits | PASS | `mission.cancel()` calls `addCredits(type='refund')` |

---

## Credit Cost Table (Implemented)

| Complexity | Base | Premium model |
|-----------|------|--------------|
| simple    | 1 MCU | 2 MCU |
| standard  | 3 MCU | 6 MCU |
| complex   | 5 MCU | 10 MCU |

---

## Tier Credits on Signup/Purchase

| Source | Credits | Tier |
|--------|---------|------|
| Signup (free) | **10 MCU** (hardcoded in INSERT) | free |
| Signup + referral | **15 MCU** | free |
| Trial extension (`/trial-extend`) | +10 MCU | free |
| Starter subscription | 200 MCU | starter |
| Pro subscription | 1000 MCU | pro |
| Enterprise subscription | -1 (unlimited) | enterprise |
| Credit pack 10 | 10 MCU | — |
| Credit pack 50 | 50 MCU | — |
| Credit pack 100 | 100 MCU | — |
| Credit pack 500 | 500 MCU | — |

**Note:** The `billing.ts` pricing endpoint claims free tier = 50 MCU but actual signup gives 10. Discrepancy exists between marketing copy and code.

---

## Gaps / Issues Found

### GAP-1: Free tier credits inconsistency (minor)
- **Where:** `tenants.ts` L49 vs `billing.ts` L434
- `tenants/signup` inserts `balance=10` ("10 free credits")
- `billing/pricing` endpoint advertises free tier = 50 credits
- `upgrade` endpoint lists free tier = 10 credits
- **Impact:** Marketing/UX mismatch. New users expect 50, get 10.

### GAP-2: Potential double-credit on subscription purchase (medium risk)
- **Where:** `billing.ts` handles both `order.paid` AND `subscription.created`
- When a user subscribes, Polar fires **both** events
- `order.paid` → `addCredits(200)` for starter
- `subscription.created` → `addCredits(200)` for starter again
- No deduplication between these two event handlers (only per-event idempotency)
- **Impact:** Tenant may receive 400 MCU instead of 200 on first subscribe.
- **Fix:** Either skip credit grant in `order.paid` for subscription products (only use `subscription.created`), or check if credits already added for this subscription period.

### GAP-3: `subscription.canceled` downgrades to `starter` tier (not `free`) (low)
- **Where:** `BillingService.processSubscriptionCanceled()` L308
- Calls `updateTenantTier(tenantId, 'starter')` — but user cancelled their subscription
- `handleSubscriptionRevoked()` correctly downgrades to `free`
- **Impact:** Cancelled users keep `starter` tier until revoked. May be intentional (grace period), but inconsistent with `revoked` behavior.

### GAP-4: Daily limit check uses tenant tier from DB (extra query per mission) (perf)
- **Where:** `MissionService.checkDailyLimit()` L178 — separate `SELECT tier FROM tenants`
- Tenant tier is already in JWT context (`tenant.tier`)
- **Impact:** Extra D1 query per submission. Minor at current scale.

### GAP-5: `creditMetering` middleware uses `type='mission'` for all API calls
- **Where:** `credit-metering.ts` L71
- All API calls logged as type='mission' in `credit_transactions` even when not a mission
- **Impact:** Transaction history pollution; makes audit harder.

---

## What's Implemented vs Missing

| Feature | Status |
|---------|--------|
| Signup with free credits | Implemented |
| JWT + API key auth | Implemented |
| Atomic credit deduction | Implemented |
| HTTP 402 on zero balance | Implemented (dual: middleware + service) |
| Low-balance alerts (<=5 MCU) | Implemented |
| Polar webhook sig verification | Implemented (HMAC SHA-256, Standard Webhooks) |
| Replay attack prevention | Implemented (timestamp + event idempotency) |
| Subscription lifecycle (create/update/cancel/revoke) | Implemented |
| Credit packs via Polar checkout | Implemented |
| Mission cancel + refund | Implemented |
| Webhook callback on mission complete | Implemented |
| Dunning events on cancel/revoke | Implemented |
| Referral bonus system | Implemented |
| Trial extension (+10 MCU) | Implemented |
| Coupon/promo code redemption | Implemented |
| **Actual mission execution (PEV loop)** | **NOT in gateway** — missions sit in `status='queued'`, no executor wired to gateway |

---

## Critical Finding: Mission Execution Gap

`POST /v1/missions` creates a record with `status='queued'` and deducts credits — but there is **no executor** in `apps/raas-gateway/` that processes the queue. The `mission-executor.ts` file exists but is not called from any route or scheduled worker in the gateway.

This means:
- Credits ARE deducted on submit
- Missions stay `queued` forever unless an external process polls/executes them
- No auto-transition to `executing` → `completed`

The actual PEV engine must be a separate process (`mekong/` Python backend or Tôm Hùm daemon) that calls `missionService.completeMission()` via an internal API.

**Verify:** Is there a scheduled Cloudflare Worker or external poller that picks up `queued` missions?

---

## Unresolved Questions

1. **Is 10 MCU (free) intentional or was it supposed to be 50?** The `billing/pricing` endpoint and CLAUDE.md reference 50 MCU free tier — but code gives 10.
2. **Double-credit on subscribe (GAP-2):** Has this been observed in production transactions? Check `credit_transactions` for `amount=200` duplicates on same `tenant_id` near subscription start.
3. **Who executes queued missions?** Is there a separate Worker, cron job, or the Python PEV engine that polls for `status='queued'` missions?
4. **`subscription.canceled` → `starter` tier (GAP-3):** Intentional grace period or bug?
5. **TIER_CREDITS in billing.ts vs POLAR_PRODUCT_CREDITS in billing-service.ts:** Two separate mappings. Which is authoritative? `billing.ts` uses product_id prefix matching; `billing-service.ts` uses product name matching. On `order.paid`, name-based lookup is used. On `subscription.created`, ID-prefix lookup is used. Could mismatch if Polar product names change.
