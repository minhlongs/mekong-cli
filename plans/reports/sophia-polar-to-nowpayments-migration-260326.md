# Sophia AI Factory — Polar.sh to NOWPayments Migration Report

**Date:** 2026-03-26
**Status:** Research Only (no files modified)
**Codebase:** `/Users/macbookprom1/mekong-cli/apps/sophia-proposal`
**Stack:** Next.js 15 + Cloudflare Workers D1 (SQLite)

---

## Executive Summary

Sophia currently uses Polar.sh for SaaS subscription billing (checkout, webhooks, customer portal). NOWPayments is a crypto payment gateway — it does not support recurring subscriptions natively. This migration requires a **fundamental model change**: from Polar's subscription model to NOWPayments' invoice-based one-time payment model with manual renewal tracking.

**Critical architectural difference:**
- Polar: subscription lifecycle (created → updated → deleted) + automatic recurring billing
- NOWPayments: one-time invoice payments + IPN (Instant Payment Notification) callbacks only

---

## 1. Files That Need to Change

### Layer 1: Core Billing Client (HIGH COMPLEXITY)

| File | Lines | What Changes |
|------|-------|--------------|
| `lib/billing/polar-client.ts` | 313 | Replace entirely with `nowpayments-client.ts` |
| `lib/billing/polar-webhook-handlers.ts` | 9 | Replace with `nowpayments-ipn-handlers.ts` |
| `lib/billing/polar-subscription-handlers.ts` | 110 | Replace with `nowpayments-payment-handlers.ts` |
| `lib/billing/polar-order-handlers.ts` | 143 | Merge logic into payment handler |
| `lib/billing/polar-webhook-error.ts` | 5 | Rename to `billing-error.ts`, keep logic |

**Key replacements in `polar-client.ts`:**

```typescript
// REMOVE: Polar client class + all methods
class PolarClient {
  createCheckoutSession()     // → NOWPayments createInvoice()
  createPortalSession()       // → NO EQUIVALENT (crypto has no portal)
  getCustomerByEmail()        // → Remove (crypto is anonymous)
  verifyWebhookSignature()    // → verifyIpnSignature() using x-nowpayments-sig header
}

// REMOVE: POLAR_TIERS with polarProductId
export const POLAR_TIERS = {
  starter: { polarProductId: process.env.POLAR_PRODUCT_STARTER },
  ...
}

// ADD: NOWPAYMENTS_TIERS with invoiceId
export const NOWPAYMENTS_TIERS = {
  starter: {
    nowpaymentsInvoiceId: '6075842741',   // From task brief
    price: 4900,
    currency: 'USD',
    payCurrency: 'USDTTRC20',
    mcuMonthly: 500,
    mcuOverageRate: 0.10,
  },
  growth: {
    nowpaymentsInvoiceId: '5213459112',
    price: 14900, ...
  },
  premium: {
    nowpaymentsInvoiceId: '5321792819',
    price: 49900, ...
  },
  master: {
    nowpaymentsInvoiceId: '4407373589',
    price: 99900, ...
  },
}
```

### Layer 2: API Routes (MEDIUM COMPLEXITY)

| File | Lines | What Changes |
|------|-------|--------------|
| `app/api/webhooks/polar/route.ts` | 88 | Rename folder → `nowpayments`, rewrite IPN handler |
| `app/api/billing/checkout/route.ts` | 127 | Replace Polar checkout with NOWPayments invoice redirect |
| `app/api/billing/portal/route.ts` | 82 | Remove (no crypto portal) or redirect to transaction history |
| `app/api/billing/subscription/route.ts` | 83 | No change needed (reads from DB, provider-agnostic) |

**Webhook route change (`app/api/webhooks/polar/route.ts` → `app/api/webhooks/nowpayments/route.ts`):**

```typescript
// REMOVE: x-polar-signature header
const signature = request.headers.get('x-polar-signature') || '';

// ADD: x-nowpayments-sig header
const signature = request.headers.get('x-nowpayments-sig') || '';

// REMOVE: Polar event types
switch (event.type) {
  case 'subscription.created': ...
  case 'subscription.updated': ...
  case 'subscription.deleted': ...
  case 'order.paid': ...
  case 'order.refunded': ...
}

// ADD: NOWPayments IPN payment_status field
switch (event.payment_status) {
  case 'finished':     // Payment confirmed — credit MCU
  case 'partially_paid': // Underpayment — hold
  case 'expired':      // Invoice expired — no action
  case 'refunded':     // Refund — deduct MCU
  case 'failed':       // Failed — notify user
}
```

**Checkout route change (`app/api/billing/checkout/route.ts`):**

```typescript
// REMOVE: getPolarClient().createCheckoutSession()
// ADD: redirect to NOWPayments pre-built invoice URL
const invoiceUrl = `https://nowpayments.io/payment/?iid=${tier.nowpaymentsInvoiceId}`;
return NextResponse.json({ url: invoiceUrl });

// NOTE: NOWPayments invoices accept email in URL param for tracking:
// https://nowpayments.io/payment/?iid=6075842741&email=user@example.com
```

### Layer 3: Frontend Components (LOW COMPLEXITY)

| File | Lines | What Changes |
|------|-------|--------------|
| `components/billing/upgrade-button.tsx` | 53 | Remove `POLAR_TIERS` import → import `NOWPAYMENTS_TIERS` |
| `components/billing/plan-card.tsx` | 57 | Same as above |
| `components/pricing/pricing-cards.tsx` | 124 | No change — reads from `/api/billing/checkout` API |
| `app/(dashboard)/billing/upgrade/page.tsx` | 44 | Replace `POLAR_TIERS` import |
| `app/(marketing)/pricing/page.tsx` | 107 | No change — uses `PricingCards` component |

**Key import changes:**
```typescript
// REMOVE:
import { POLAR_TIERS } from '@/lib/billing/polar-client';

// ADD:
import { NOWPAYMENTS_TIERS } from '@/lib/billing/nowpayments-client';
```

### Layer 4: Pricing Config (LOW COMPLEXITY)

| File | Lines | What Changes |
|------|-------|--------------|
| `lib/pricing-config.ts` | 86 | Replace `POLAR_TIERS` import → `NOWPAYMENTS_TIERS` |
| `lib/billing/mcu-pricing.ts` | 109 | Replace `POLAR_TIERS` import + `getTierByProductId()` function |

**`mcu-pricing.ts` change:**
```typescript
// REMOVE:
export function getTierByProductId(productId: string): PolarTier | null {
  return Object.values(POLAR_TIERS).find(
    tier => tier.polarProductId === productId
  ) || null;
}

// ADD:
export function getTierByInvoiceId(invoiceId: string): NowPaymentsTier | null {
  return Object.values(NOWPAYMENTS_TIERS).find(
    tier => tier.nowpaymentsInvoiceId === invoiceId
  ) || null;
}
```

### Layer 5: Database Schema (MEDIUM COMPLEXITY)

**New migration file needed** (`migrations/0008-nowpayments.sql`):

```sql
-- Rename Polar columns to provider-agnostic names
ALTER TABLE subscriptions ADD COLUMN nowpayments_payment_id TEXT;
ALTER TABLE subscriptions ADD COLUMN nowpayments_invoice_id TEXT;
-- Drop polar_subscription_id (or keep for backward compat during transition)

ALTER TABLE billing_settings ADD COLUMN nowpayments_order_id TEXT;
-- Drop polar_customer_id (NOWPayments has no customer concept)

ALTER TABLE transactions ADD COLUMN nowpayments_payment_id TEXT;
ALTER TABLE transactions ADD COLUMN nowpayments_invoice_id TEXT;
-- Drop polar_order_id, polar_customer_id, polar_product_id
```

**Affected DB columns:**
- `subscriptions.polar_subscription_id` → `nowpayments_payment_id`
- `billing_settings.polar_customer_id` → `nowpayments_order_id`
- `billing_settings.polar_subscription_id` → remove
- `transactions.polar_order_id` → `nowpayments_payment_id`
- `transactions.polar_customer_id` → remove
- `transactions.polar_product_id` → `nowpayments_invoice_id`

**TypeScript types** (`lib/db/types.ts`):
```typescript
// CHANGE BillingSettings:
export interface BillingSettings {
  // ...
  nowpayments_order_id: string | null;  // was: polar_customer_id
  // remove: polar_subscription_id
}

// CHANGE Subscription:
export interface Subscription {
  // ...
  nowpayments_payment_id: string | null;  // was: polar_subscription_id
}
```

### Layer 6: Tests (MEDIUM COMPLEXITY)

| File | Lines | What Changes |
|------|-------|--------------|
| `tests/billing/polar-checkout.test.ts` | 163 | Rewrite → `nowpayments-checkout.test.ts` |
| `tests/billing/webhook-handler.test.ts` | 245 | Rewrite → `nowpayments-ipn.test.ts` |
| `tests/billing/mcu-pricing.test.ts` | 202 | Update imports only (logic unchanged) |

### Layer 7: CLAUDE.md (TRIVIAL)

| File | What Changes |
|------|--------------|
| `app/sophia-proposal/CLAUDE.md` | Update line "Pricing must reference Polar.sh tiers" → NOWPayments |

---

## 2. Environment Variables to Update

### Remove (Polar)
```bash
POLAR_API_KEY=...
POLAR_API_URL=https://api.polar.sh
POLAR_WEBHOOK_SECRET=...
POLAR_PRODUCT_STARTER=...
POLAR_PRODUCT_GROWTH=...
POLAR_PRODUCT_PREMIUM=...
POLAR_PRODUCT_MASTER=...
```

### Add (NOWPayments)
```bash
NOWPAYMENTS_API_KEY=1MXH4QA-FF742Q2-Q81SQ6T-R7K42KP
NOWPAYMENTS_IPN_SECRET=ce3b140c-e7cd-4a66-a8e8-f0a5535d44dc
NOWPAYMENTS_PAYOUT_ADDRESS=TC6FknawxFcgUn1jr8CN455wsSm87hByDQ

# Invoice IDs (pre-created in NOWPayments dashboard)
NOWPAYMENTS_INVOICE_STARTER=6075842741
NOWPAYMENTS_INVOICE_GROWTH=5213459112
NOWPAYMENTS_INVOICE_PREMIUM=5321792819
NOWPAYMENTS_INVOICE_MASTER=4407373589

# Wrangler secrets (for Cloudflare Workers)
# wrangler secret put NOWPAYMENTS_API_KEY
# wrangler secret put NOWPAYMENTS_IPN_SECRET
```

**Vercel env vars:** Update in `longtho638-jpg/sophia-ai-factory` → Settings → Environment Variables.

---

## 3. Webhook Handler Changes (Critical)

### Polar webhook vs. NOWPayments IPN

| Aspect | Polar | NOWPayments |
|--------|-------|-------------|
| Header | `x-polar-signature` | `x-nowpayments-sig` |
| Signature method | HMAC-SHA256, format `t=TS,v1=HASH` | HMAC-SHA512 of sorted JSON body |
| Event field | `event.type` | `event.payment_status` |
| Retry on 500 | Yes | Yes |
| Idempotency field | `orderId` | `payment_id` |
| Endpoint URL | `/api/webhooks/polar` | `/api/webhooks/nowpayments` |

### New IPN signature verification logic

```typescript
// NOWPayments uses HMAC-SHA512 of the sorted JSON body
async function verifyIpnSignature(
  rawBody: string,
  signature: string,
  secret: string
): Promise<boolean> {
  // Sort JSON keys alphabetically before hashing
  const parsed = JSON.parse(rawBody);
  const sorted = JSON.stringify(parsed, Object.keys(parsed).sort());

  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-512' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, enc.encode(sorted));
  const computed = Array.from(new Uint8Array(sig))
    .map(b => b.toString(16).padStart(2, '0')).join('');

  return computed === signature;
}
```

### New IPN event structure (NOWPayments)

```json
{
  "payment_id": "5745278819",
  "payment_status": "finished",
  "pay_address": "TC6FknawxFcgUn1jr8CN455wsSm87hByDQ",
  "price_amount": 499.00,
  "price_currency": "usd",
  "pay_amount": 499.0,
  "pay_currency": "usdttrc20",
  "order_id": "sophia_org_abc123_1711234567",
  "order_description": "Sophia AI Factory - Premium Plan",
  "invoice_id": "5321792819",
  "created_at": "2026-03-26T10:00:00.000Z",
  "updated_at": "2026-03-26T10:05:00.000Z"
}
```

---

## 4. Frontend Checkout Flow Changes

### Before (Polar)
```
User clicks "Upgrade" → POST /api/billing/checkout
  → PolarClient.createCheckoutSession(productId, email, successUrl)
  → Redirect to https://checkout.polar.sh/cs_xxx
  → User pays on Polar → Polar sends webhook → MCU credited
```

### After (NOWPayments)
```
User clicks "Upgrade" → POST /api/billing/checkout
  → Generate order_id = `sophia_${orgId}_${timestamp}`
  → Build invoice URL with order tracking:
    https://nowpayments.io/payment/?iid=5321792819&order_id=sophia_xxx
  → Redirect to NOWPayments invoice page
  → User pays with USDT TRC20 → NOWPayments sends IPN → MCU credited
```

### Customer Portal (Billing Management)
Polar's `createPortalSession()` has no equivalent in NOWPayments (crypto payments are anonymous and non-recurring by default).

**Replacement:** Build a simple `/dashboard/billing` page showing:
- Payment history from `transactions` table
- Current MCU balance from `org_balances` table
- "Renew Plan" button (generates new NOWPayments invoice)

**Important:** NOWPayments does NOT handle recurring subscriptions automatically. Sophia will need to:
1. Track subscription expiry dates manually in D1
2. Send renewal reminder emails before period_end
3. Show "Renew" button in dashboard for expired subscriptions

---

## 5. Subscription Model Architectural Change

### Critical: Polar subscriptions vs. NOWPayments one-time payments

| Feature | Polar | NOWPayments |
|---------|-------|-------------|
| Recurring billing | Automatic | Manual (customer must re-pay) |
| Subscription lifecycle | Full (created/updated/deleted) | None |
| Payment currency | USD/fiat | Crypto only |
| Customer accounts | Yes (portal) | No |
| Refunds | Via Polar dashboard | Via NOWPayments dashboard |
| Chargeback protection | Yes | No (crypto = irreversible) |

**Impact on business logic:**
- `handleSubscriptionCreated` → `handlePaymentFinished` (credit MCU + set period_end to +30 days)
- `handleSubscriptionUpdated` → Remove (not applicable)
- `handleSubscriptionDeleted` → Replace with scheduled task to downgrade on `period_end`
- `handleOrderPaid` → Merge into `handlePaymentFinished`
- `handleOrderRefunded` → `handlePaymentRefunded` (crypto refunds are manual)

---

## 6. Estimated Effort

| Task | Complexity | Est. Hours |
|------|-----------|-----------|
| New `nowpayments-client.ts` | High | 4h |
| IPN handler + signature verification | High | 3h |
| Subscription + payment handlers | High | 4h |
| API routes (checkout, webhook) | Medium | 3h |
| Frontend component updates | Low | 1h |
| DB migration (schema changes) | Medium | 2h |
| Test rewrites | Medium | 4h |
| Manual subscription tracking (renewal reminders) | Medium | 3h |
| Env var updates (Vercel + Wrangler) | Low | 0.5h |
| E2E testing on staging | Medium | 3h |

**Total estimated:** ~27.5 hours (3-4 developer days)

---

## 7. Implementation Order (Recommended)

1. Create `lib/billing/nowpayments-client.ts` (new client, new tier config)
2. Create `migrations/0008-nowpayments.sql` (schema changes)
3. Update `lib/db/types.ts` (TypeScript types)
4. Rewrite `app/api/webhooks/nowpayments/route.ts` (new IPN endpoint)
5. Rewrite `app/api/billing/checkout/route.ts` (invoice redirect)
6. Update `lib/billing/mcu-pricing.ts` (`getTierByInvoiceId`)
7. Update `lib/pricing-config.ts` (import change)
8. Update frontend components (import swaps)
9. Rewrite tests
10. Update Vercel + Wrangler env vars
11. Register IPN URL in NOWPayments dashboard: `https://sophia-ai-factory.vercel.app/api/webhooks/nowpayments`
12. End-to-end test with small payment on staging

---

## 8. NOWPayments API Reference

| Action | Endpoint |
|--------|----------|
| Create payment | `POST https://api.nowpayments.io/v1/payment` |
| Get payment status | `GET https://api.nowpayments.io/v1/payment/{id}` |
| Create invoice | `POST https://api.nowpayments.io/v1/invoice` |
| List currencies | `GET https://api.nowpayments.io/v1/currencies` |
| IPN webhook | Configured in NOWPayments dashboard |

**IPN URL to register:** `https://sophia-ai-factory.vercel.app/api/webhooks/nowpayments`

**Pre-built invoice URLs** (customer-facing checkout pages):
- Starter ($49): `https://nowpayments.io/payment/?iid=6075842741`
- Growth ($149): `https://nowpayments.io/payment/?iid=5213459112`
- Premium ($499): `https://nowpayments.io/payment/?iid=5321792819`
- Master ($999): `https://nowpayments.io/payment/?iid=4407373589`

---

## 9. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| No auto-recurring = churn risk | HIGH | Build renewal reminder system + clear UX |
| Crypto volatility | MEDIUM | USDT TRC20 is stable (pegged to USD) |
| Underpayments (wrong crypto amount) | MEDIUM | Handle `partially_paid` status, hold MCU |
| IPN delivery failure | MEDIUM | Idempotency via `payment_id` in D1 |
| Customer confusion (crypto onboarding) | HIGH | Clear payment instructions + support docs |
| CLAUDE.md still references Polar pricing | LOW | Update in same PR |

---

## 10. Files NOT Requiring Changes

- `app/api/billing/subscription/route.ts` — reads from DB only, provider-agnostic
- `app/api/referral/*` — referral system is independent
- `components/pricing/pricing-cards.tsx` — calls API only, no direct Polar refs
- `app/(marketing)/pricing/page.tsx` — uses `PricingCards`, no direct Polar refs
- All non-billing API routes
- All D1 migration files 0001–0007 (add new 0008)

---

*Report generated: 2026-03-26*
*Author: fullstack-developer agent*
*Source codebase: /Users/macbookprom1/mekong-cli/apps/sophia-proposal*
*No files were modified during this research.*
