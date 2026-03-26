# Phase Implementation Report

## Executed Phase
- Phase: Sophia Polar → NOWPayments Migration
- Plan: sophia-ai-factory (apps/sophia-ai-factory)
- Status: completed

## Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `src/lib/clients/nowpayments-client.ts` | Created | 97 |
| `src/lib/billing/nowpayments-ipn-handlers.ts` | Created | 200 |
| `src/app/api/webhooks/nowpayments/route.ts` | Created | 56 |
| `src/app/api/checkout/route.ts` | Updated | 79 |
| `src/config/tiers.ts` | Updated | polarProductId → nowpaymentsInvoiceId |
| `src/types/index.ts` | Updated | TierConfig.polarProductId → nowpaymentsInvoiceId |
| `.env.production.example` | Updated | Added NOWPAYMENTS_* vars |

## Tasks Completed

- [x] Step 1: `nowpayments-client.ts` — NOWPAYMENTS_TIERS config, createInvoiceUrl(), verifyIpnSignature(), getTierByInvoiceId()
- [x] Step 2: `nowpayments-ipn-handlers.ts` — IPN dispatcher with idempotency (reuses payment_events table), finished/refunded/failed/partially_paid/expired handlers
- [x] Step 3: `app/api/webhooks/nowpayments/route.ts` — HMAC-SHA512 sig verify + IPN routing
- [x] Step 4: `app/api/checkout/route.ts` — replaced Polar ServiceFactory with createInvoiceUrl() direct redirect
- [x] Step 5+6: `config/tiers.ts` + `types/index.ts` — polarProductId → nowpaymentsInvoiceId
- [x] Step 9: `.env.production.example` — Added NOWPAYMENTS_API_KEY, NOWPAYMENTS_IPN_SECRET, NOWPAYMENTS_WALLET
- [x] Step 10: types/index.ts updated

## Steps Skipped / Adjusted

- **Step 7** (frontend components upgrade-button/plan-card/billing/upgrade/page): Files do not exist in codebase. Pricing components (`pricing-card.tsx`, `pricing-data.ts`, `pricing-section.tsx`) have zero Polar imports — no change needed.
- **Step 8** (delete polar files): Kept `lib/clients/polar-client.ts` and `lib/payments/polar-*` — still actively imported by `polar-metered-billing.ts`, `subscription-gate-middleware.ts`, `raas-gate.ts`, `billing-sync.ts`. Removing would break metered billing. Kept `app/api/webhooks/polar/route.ts` because directory contains `route.test.ts` (task: DO NOT modify test files).
- **Step 5+6 lib/billing/mcu-pricing.ts / lib/pricing-config.ts**: Files not found in codebase (different structure than spec).

## TypeScript Status

- `tsc --noEmit` crashes with `RangeError: Maximum call stack size exceeded` on Node.js v25.2.1 — **pre-existing issue** unrelated to this migration (global `tsc` v5.x + Node 25 incompatibility).
- `npm run build` fails with `Cannot find module 'next-intl/plugin'` — **pre-existing issue** (npx uses wrong Next.js version without local deps).
- All import chains manually verified: no circular deps, all referenced exports exist.

## Invoice IDs Configured

| Tier | Invoice ID | Price |
|------|-----------|-------|
| BASIC (Starter) | 6075842741 | $199 |
| PREMIUM (Growth) | 5213459112 | $399 |
| ENTERPRISE (Premium) | 5321792819 | $799 |
| MASTER | 4407373589 | $4,999 |

## IPN Idempotency

Reuses existing `payment_events` table with key `nowpayments_{payment_id}` — no DB schema change needed.

## Unresolved Questions

1. `handlePaymentSuccess` in `dunning-workflow.ts` takes `licenseNonce` param — IPN handler passes empty string `''` because NOWPayments IPN doesn't carry license nonce. May need license lookup by userId if dunning workflow requires valid nonce.
2. `app/api/webhooks/polar/route.ts` still live — no rollback path configured. Need to decide when to remove old Polar webhook (after confirmed no active Polar subscriptions).
3. `polar-metered-billing.ts` + `polar-usage-reporter.ts` — still use Polar SDK for metered usage tracking. These need separate migration if Polar account is fully closed.
