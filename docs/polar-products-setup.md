# Polar.sh Products Setup Guide

**Last updated:** 2026-03-20
**Owner:** CMO/Revenue Agent
**Status:** Ready to execute

---

## Overview

Create 12 Polar.sh products for 3 apps:
- **Mekong CLI:** 4 products (Starter, Pro, Enterprise, Free)
- **WellNexus:** 3 products (Basic, Clinic, Enterprise)
- **AlgoTrader:** 4 products (Hobbyist, Pro, Institution, Enterprise)

---

## Step 1: Mekong CLI Products

### Product 1: Starter ($49/mo)

1. Go to [Polar Dashboard → Products](https://polar.sh/mekong-cli/products)
2. Click **Create Product**
3. Fill in:
   - **Name:** Mekong CLI - Starter
   - **Price:** $49/month
   - **Description:** For solo founders running their first AI agency
   - **Benefits:** 200 MCU credits/month
4. Save and copy `product_id` → Update `.env`:
   ```bash
   POLAR_STARTER_PRODUCT_ID=prod_xxx
   ```

### Product 2: Pro ($149/mo)

1. Click **Create Product**
2. Fill in:
   - **Name:** Mekong CLI - Pro
   - **Price:** $149/month
   - **Description:** For teams shipping at scale with parallel AI agents
   - **Benefits:** 1,000 MCU credits/month, Tom Hum daemon
3. Save and copy `product_id`:
   ```bash
   POLAR_PRO_PRODUCT_ID=prod_xxx
   ```

### Product 3: Enterprise ($499/mo)

1. Click **Create Product**
2. Fill in:
   - **Name:** Mekong CLI - Enterprise
   - **Price:** $499/month
   - **Description:** Unlimited AI power for serious engineering teams
   - **Benefits:** Unlimited MCU credits, custom agents, SLA
3. Save and copy `product_id`:
   ```bash
   POLAR_ENTERPRISE_PRODUCT_ID=prod_xxx
   ```

### Product 4: Free ($0)

- No Polar product needed (GitHub link)

---

## Step 2: WellNexus Products

### Product 1: Basic ($99/mo)

1. Go to [Polar Dashboard → WellNexus](https://polar.sh/wellnexus/products)
2. Create product:
   - **Name:** WellNexus Basic
   - **Price:** $99/month
   - **Description:** For small clinics (1-3 doctors)
   - **Benefits:** EMR core, booking, basic billing

### Product 2: Clinic ($299/mo)

1. Create product:
   - **Name:** WellNexus Clinic
   - **Price:** $299/month
   - **Description:** Growing clinics (5-20 staff)
   - **Benefits:** Full EMR, pharmacy, telemedicine, analytics

### Product 3: Enterprise ($999/mo)

1. Create product:
   - **Name:** WellNexus Enterprise
   - **Price:** $999/month
   - **Description:** Hospital chains (20+ staff)
   - **Benefits:** Multi-location, custom integrations, SLA

---

## Step 3: AlgoTrader Products

### Product 1: Hobbyist ($29/mo)

1. Go to [Polar Dashboard → AlgoTrader](https://polar.sh/algo-trader/products)
2. Create product:
   - **Name:** AlgoTrader Hobbyist
   - **Price:** $29/month
   - **Description:** Personal trading automation
   - **Benefits:** 1 exchange, basic strategies, community support

### Product 2: Pro ($99/mo)

1. Create product:
   - **Name:** AlgoTrader Pro
   - **Price:** $99/month
   - **Description:** Serious traders
   - **Benefits:** 3 exchanges, advanced strategies, priority support

### Product 3: Institution ($499/mo)

1. Create product:
   - **Name:** AlgoTrader Institution
   - **Price:** $499/month
   - **Description:** Professional trading firms
   - **Benefits:** Unlimited exchanges, custom strategies, SLA

### Product 4: Enterprise (Custom)

1. Create product:
   - **Name:** AlgoTrader Enterprise
   - **Price:** Contact sales
   - **Description:** White-label trading platform
   - **Benefits:** Full customization, dedicated support

---

## Verification Checklist

After creating all 12 products:

- [ ] All products visible in Polar dashboard
- [ ] Product IDs copied to respective `.env` files
- [ ] Checkout links tested (see [TESTING.md](./TESTING.md))
- [ ] Webhook endpoints configured

---

## Checkout Links (After Creation)

### Mekong CLI
- Starter: `https://polar.sh/mekong-cli/checkout?product=starter`
- Pro: `https://polar.sh/mekong-cli/checkout?product=pro`
- Enterprise: `https://polar.sh/mekong-cli/checkout?product=enterprise`

### WellNexus
- Basic: `https://polar.sh/wellnexus/checkout?product=basic`
- Clinic: `https://polar.sh/wellnexus/checkout?product=clinic`
- Enterprise: `https://polar.sh/wellnexus/checkout?product=enterprise`

### AlgoTrader
- Hobbyist: `https://polar.sh/algo-trader/checkout?product=hobbyist`
- Pro: `https://polar.sh/algo-trader/checkout?product=pro`
- Institution: `https://polar.sh/algo-trader/checkout?product=institution`
- Enterprise: `https://polar.sh/algo-trader/checkout?product=enterprise`

---

## Next Steps

1. **Test Checkout Flows:** Run `/cook test-checkout-flows`
2. **Configure Webhooks:** Set webhook URL to `https://agencyos.network/api/webhooks/polar`
3. **Verify MCU Allocation:** Test that purchase allocates credits correctly

---

**Related docs:**
- [MCU Billing System](../src/core/mcu_billing.py)
- [Polar Webhooks](../src/core/webhooks.py)
- [Testing Guide](./TESTING.md)
