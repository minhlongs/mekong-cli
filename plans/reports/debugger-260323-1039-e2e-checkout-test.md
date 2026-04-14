# E2E Checkout Flow — Debug Report
**Date:** 2026-03-23 | **API:** https://api.agencyos.network | **Scope:** payment → credits flow

---

## Executive Summary

Billing infrastructure is largely functional. Core endpoints respond correctly, D1 schema is complete, webhook signature verification is implemented properly. **Three issues found:** webhook endpoint returns 503 due to KV unavailability, a product ID/name mismatch between the two handler paths, and `/v1/tenants` requires JWT auth (expected but blocks free-tier onboarding testing).

---

## Test Results

### 1. Webhook Endpoint — POST /billing/webhook

**Result: 503 SERVICE_UNAVAILABLE**

```json
{"error":"Rate limiting unavailable","code":"SERVICE_UNAVAILABLE"}
```

**Root cause:** `authRateLimit()` middleware tries `c.env.RATE_LIMIT_KV.get(key, 'json')` — fails silently and the catch block returns 503 (fail-closed design). The `RATE_LIMIT_KV` binding is either:
- Not bound in the deployed Worker, or
- Temporarily unavailable

The webhook never reaches signature verification. Real Polar.sh webhooks are being rejected.

**Code path:** `src/middleware/auth-rate-limit.ts:72-78`

---

### 2. Billing Pricing — GET /billing/pricing

**Result: PASS**

Returns correct unified pricing:
- Free: $0 / 50 credits
- Starter: $49 / 200 credits
- Pro: $149 / 1000 credits
- Enterprise: $499 / unlimited

Also returns credit packs and annual tiers. Response matches CLAUDE.md spec.

---

### 3. Products Endpoint — GET /billing/checkout/products

**Result: PASS (with mismatch warning)**

Returns 4 products with product_id prefixes:
```json
[
  {"product_id":"ce215739","name":"Starter","tier":"starter"},
  {"product_id":"b810b7eb","name":"Pro","tier":"pro"},
  {"product_id":"0e752654","name":"Agency","tier":"agency"},
  {"product_id":"dc82a4bb","name":"Master","tier":"master"}
]
```

**Warning — Product mismatch between two handler paths:**

| Handler | Lookup method | Products it knows |
|---------|--------------|-------------------|
| `billing.ts` (subscription.created/updated) | `product_id` prefix (8 chars) | Starter, Pro, Agency, Master |
| `billing-service.ts` (order.paid, subscription.active) | `product_name` lowercase | agencyos-starter, agencyos-pro, agencyos-agency, agencyos-master |

The `billing-service.ts` `POLAR_PRODUCT_CREDITS` map uses keys like `agencyos-starter` but Polar returns product names like `"Starter"` — `getProductCredits("Starter")` → lookups `"starter"` → no match. **`order.paid` events will silently fail to allocate credits** unless Polar product names exactly match `agencyos-*` format.

Also: `billing-service.ts` maps `agencyos-starter` → 50 credits (tier: pro), but `billing.ts` maps `ce215739` → 200 credits (tier: starter). **Credit amounts diverge for the same product.**

---

### 4. Tenant Registration — POST /v1/tenants

**Result: 401 AUTHENTICATION_REQUIRED**

```json
{"error":"Valid JWT or API key required","code":"AUTHENTICATION_REQUIRED"}
```

Expected — endpoint is auth-gated. No unauthenticated tenant creation possible. Free-tier signup must go through a frontend that acquires a JWT first. Credits-on-signup behavior cannot be tested without valid auth token.

---

### 5. Webhook Handler Code Analysis

**Signature verification:** Correct Standard Webhooks implementation.
- Strips `whsec_` prefix from secret
- Signs `{webhook-id}.{webhook-timestamp}.{body}`
- Uses `crypto.subtle.verify` (constant-time, prevents timing attacks)
- Supports multiple signatures in header

**Timestamp validation:** 5-minute window, rejects future timestamps. Correct.

**Idempotency:** Checks `webhook_events` table before processing. `webhook_events` table confirmed to exist in D1.

**Event coverage:**

| Event | Handler | Credits allocated |
|-------|---------|------------------|
| order.paid | BillingService.processOrderPaid | Via product_name lookup (broken — see above) |
| subscription.active | BillingService.processSubscriptionActive | Via product_name lookup (broken) |
| subscription.created | handleSubscriptionCreated | Via product_id prefix (works) |
| subscription.updated | handleSubscriptionUpdated | Renewal — reads credits_per_period from DB |
| subscription.cancelled | handleSubscriptionCancelled | Marks cancelled, creates dunning event |
| subscription.revoked | handleSubscriptionRevoked | Immediately downgrades to free |
| refund.created | BillingService.processRefund | Via product_name lookup (broken) |

**Missing event:** `checkout.created` (sent in test) falls through to default case → `received: true` with no action. This is correct behavior.

---

### 6. D1 Tables

**Result: PASS**

All required billing tables exist:
- `credits` (0 rows — empty)
- `credit_transactions` (21 rows — test data present)
- `subscriptions` (0 rows — empty)
- `webhook_events` (exists)
- `dunning_events` (exists)
- `billing_invoices`, `billing_payments`, `billing_statements`

Schema for `subscriptions` is correct — has `polar_subscription_id`, `credits_per_period`, `tier`, `status`, period dates.

`credits` table is empty — no tenant has been granted credits through the webhook flow (consistent with webhook being blocked by KV).

---

## Issues Summary

| # | Severity | Issue | Location |
|---|---------|-------|----------|
| 1 | **CRITICAL** | `RATE_LIMIT_KV` binding unavailable → all webhook POST requests return 503, Polar webhooks never processed | `auth-rate-limit.ts:22` / wrangler.toml |
| 2 | **HIGH** | `order.paid`/`subscription.active`/`refund.created` handlers use product_name lookup that doesn't match Polar product names | `billing-service.ts:53-64` |
| 3 | **HIGH** | Credit amount inconsistency: `order.paid` path allocates 50 credits for Starter, `subscription.created` path allocates 200 | `billing-service.ts:55` vs `billing.ts:17` |
| 4 | **LOW** | `webhook/status` reports `configured: true` but KV is down — status endpoint gives false confidence | `billing.ts:419-425` |

---

## What Works

- GET /billing/pricing — correct, unified
- GET /billing/checkout/products — correct
- GET /billing/webhook/status — responds (misleading but functional)
- D1 schema complete and deployed
- Signature verification logic correct
- Idempotency check correct
- subscription.created/updated/cancelled/revoked handlers use correct product_id lookup
- Dunning events created on cancellation/revocation
- Tenant webhook notification on cancel/revoke

## What's Broken

- **All webhook POST requests** — blocked by KV rate limiter returning 503
- `order.paid` credit allocation — product name mismatch
- `subscription.active` tier upgrade — product name mismatch
- `refund.created` credit deduction — product name mismatch

---

## Unresolved Questions

1. Is `RATE_LIMIT_KV` bound in the deployed Worker's wrangler.toml? Need to check `wrangler.toml` kv_namespaces section.
2. Is the fail-closed behavior on KV error intentional? (Could use fail-open with logging instead for webhooks.)
3. What exact product names does Polar send in `order.paid` events — `"Starter"` or `"agencyos-starter"`? Determines severity of issue #2.
4. Are there any real Polar webhook deliveries that have failed silently? Check Polar dashboard delivery logs.
