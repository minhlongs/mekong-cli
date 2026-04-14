# Polar.sh Product Setup Guide

**Date:** 2026-03-20
**Priority:** P0 (Blocking GTM Launch)

---

## Quick Start

1. Go to https://polar.sh/dashboard
2. Create 12 products using the specs below
3. Copy product IDs to environment files
4. Test checkout flows

---

## Products to Create

### algo-trader (4 products)

| Product | Price/mo | Description | Suggested ID |
|---------|----------|-------------|--------------|
| Starter | $49 | 200 MCU, core commands | `algo-trader-starter` |
| Pro | $199 | 1,000 MCU, priority support | `algo-trader-pro` |
| Agency | $499 | 5,000 MCU, custom agents | `algo-trader-agency` |
| Master | $999 | Unlimited MCU, white-label | `algo-trader-master` |

### well (WellNexus) (4 products)

| Product | Price/mo | Description | Suggested ID |
|---------|----------|-------------|--------------|
| Starter | $49 | 200 MCU, EMR + Booking | `well-starter` |
| Pro | $199 | 1,000 MCU, + Insurance | `well-pro` |
| Agency | $499 | 5,000 MCU, multi-clinic | `well-agency` |
| Master | $999 | Unlimited MCU, API access | `well-master` |

### raas-gateway (4 products)

| Product | Price/mo | Description | Suggested ID |
|---------|----------|-------------|--------------|
| Starter | $29 | 50 MCU, API access | `raas-gateway-starter` |
| Pro | $99 | 200 MCU, + Analytics | `raas-gateway-pro` |
| Agency | $199 | 500 MCU, custom routes | `raas-gateway-agency` |
| Master | $399 | 1,000 MCU, SLA | `raas-gateway-master` |

---

## Step-by-Step Instructions

### Step 1: Create Products in Polar Dashboard

1. Login to https://polar.sh/dashboard
2. Click "New Product"
3. Fill in:
   - **Name:** algo-trader-starter
   - **Price:** $49/month
   - **Description:** 200 MCU, core commands
   - **Type:** Subscription
4. Click "Create Product"
5. Copy the **Product ID** (e.g., `prod_abc123xyz`)
6. Repeat for all 12 products

### Step 2: Update Environment Files

After creating products, update the product IDs in your environment files:

#### algo-trader (`apps/algo-trader/.env`)
```env
POLAR_PRODUCT_STARTER=prod_xxx
POLAR_PRODUCT_PRO=prod_xxx
POLAR_PRODUCT_AGENCY=prod_xxx
POLAR_PRODUCT_MASTER=prod_xxx
```

#### well (`apps/well/.env`)
```env
POLAR_PRODUCT_STARTER=prod_xxx
POLAR_PRODUCT_PRO=prod_xxx
POLAR_PRODUCT_AGENCY=prod_xxx
POLAR_PRODUCT_MASTER=prod_xxx
```

#### raas-gateway (`apps/raas-gateway/.env`)
```env
POLAR_PRODUCT_STARTER=prod_xxx
POLAR_PRODUCT_PRO=prod_xxx
POLAR_PRODUCT_AGENCY=prod_xxx
POLAR_PRODUCT_MASTER=prod_xxx
```

### Step 3: Set raas-gateway Secrets

```bash
cd apps/raas-gateway

# Set secrets
wrangler secret put JWT_SECRET
wrangler secret put POLAR_WEBHOOK_SECRET
wrangler secret put SERVICE_TOKEN
```

### Step 4: Test Checkout Flows

Test all 9 checkout flows:

```bash
# algo-trader
open "https://algo-trader.agencyos.network/upgrade?tier=starter"
open "https://algo-trader.agencyos.network/upgrade?tier=pro"
open "https://algo-trader.agencyos.network/upgrade?tier=agency"

# well
open "https://wellnexus.pages.dev/upgrade?tier=starter"
open "https://wellnexus.pages.dev/upgrade?tier=pro"
open "https://wellnexus.pages.dev/upgrade?tier=agency"

# raas-gateway
open "https://raas-gateway.agencyos-openclaw.workers.dev/billing/checkout?tier=starter"
open "https://raas-gateway.agencyos-openclaw.workers.dev/billing/checkout?tier=pro"
open "https://raas-gateway.agencyos-openclaw.workers.dev/billing/checkout?tier=agency"
```

**Verify:**
- Redirects to `buy.polar.sh` checkout
- Correct product/price displayed
- Checkout completes successfully
- Webhook received and credits allocated

---

## Webhook Configuration

### Polar.sh Webhook Settings

1. Go to Polar Dashboard → Settings → Webhooks
2. Add webhook endpoint for each app:

| App | Webhook URL |
|-----|-------------|
| algo-trader | `https://algo-trader.agencyos.network/api/webhooks/polar` |
| well | `https://wellnexus.pages.dev/api/webhooks/polar` |
| raas-gateway | `https://raas-gateway.agencyos-openclaw.workers.dev/billing/webhook` |

3. Copy **Webhook Secret** and set in environment files

---

## Verification Checklist

- [ ] 12 products created in Polar.sh
- [ ] Product IDs added to all 3 apps' .env files
- [ ] raas-gateway secrets set via wrangler
- [ ] Webhook endpoints configured
- [ ] 9 checkout flows tested
- [ ] Webhooks received and processed
- [ ] Credits allocated correctly

---

## Estimated Time

- Product creation: 30-45 minutes
- Environment config: 15 minutes
- Secret setup: 5 minutes
- Checkout testing: 30 minutes

**Total:** ~1.5 hours

---

## Troubleshooting

### Product not found
- Check product ID is correct (starts with `prod_`)
- Verify product is active in Polar dashboard

### Webhook not received
- Check webhook URL is publicly accessible
- Verify webhook secret matches
- Check Polar.sh webhook logs

### Checkout fails
- Ensure product is active
- Check Polar.sh account is in test mode (for testing)
- Verify redirect URLs are correct

---

**Next Step After Completion:** Update `plans/260319-1954-mekong-raas-gtm-roadmap/plan.md` with product IDs and mark Phase 1 complete.
