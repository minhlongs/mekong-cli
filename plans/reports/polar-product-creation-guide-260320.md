# Polar.sh Product Creation Guide

**Date:** 2026-03-20
**Status:** Manual action required (Polar API limitation)

---

## ⚠️ API Limitation

Polar.sh **does not expose** a public API endpoint for creating products programmatically.

**Reference:** https://docs.polar.sh/api-reference

Available API endpoints:
- `GET /v1/products` — List products ✅
- `GET /v1/products/{id}` — Get product ✅
- `POST /v1/checkouts` — Create checkout ✅
- `GET /v1/subscriptions` — List subscriptions ✅
- ❌ `POST /v1/products` — **NOT AVAILABLE**

---

## 📋 Manual Creation Steps

### Step 1: Login to Polar Dashboard

```bash
open https://polar.sh/dashboard
```

### Step 2: Navigate to Products

1. Click **"Products"** in sidebar
2. Click **"New Product"** button

### Step 3: Create Each Product

For each of the 12 products below:

| # | Product Name | Price/mo | MCU Included |
|---|--------------|----------|--------------|
| 1 | RaaS Gateway - Starter | $29 | 50 MCU |
| 2 | RaaS Gateway - Pro | $99 | 200 MCU |
| 3 | RaaS Gateway - Agency | $199 | 500 MCU |
| 4 | RaaS Gateway - Master | $399 | 1,000 MCU |
| 5 | WellNexus - Starter | $49 | 50 MCU |
| 6 | WellNexus - Pro | $199 | 200 MCU |
| 7 | WellNexus - Agency | $499 | 500 MCU |
| 8 | WellNexus - Master | $999 | 1,000 MCU |
| 9 | Algo Trader - Starter | $49 | 50 MCU |
| 10 | Algo Trader - Pro | $199 | 200 MCU |
| 11 | Algo Trader - Agency | $499 | 500 MCU |
| 12 | Algo Trader - Master | $999 | 1,000 MCU |

### Step 4: Configure Each Product

For each product:

1. **Name:** Use exact name from table above
2. **Description:** `{App Name} — {Tier} tier with {MCU} MCU/month`
3. **Price:** Enter monthly recurring price
4. **Type:** Subscription (recurring)
5. **Save** and copy the **Product ID** (format: `pro_xxxxx`)

### Step 5: Update Environment Files

After creating all products, update `.env` files:

```bash
# apps/raas-gateway/.env
POLAR_STARTER_PRODUCT_ID=pro_xxx
POLAR_PRO_PRODUCT_ID=pro_xxx
POLAR_AGENCY_PRODUCT_ID=pro_xxx
POLAR_MASTER_PRODUCT_ID=pro_xxx

# apps/well/.env
POLAR_STARTER_PRODUCT_ID=pro_xxx
POLAR_PRO_PRODUCT_ID=pro_xxx
POLAR_AGENCY_PRODUCT_ID=pro_xxx
POLAR_MASTER_PRODUCT_ID=pro_xxx

# apps/algo-trader/.env
POLAR_STARTER_PRODUCT_ID=pro_xxx
POLAR_PRO_PRODUCT_ID=pro_xxx
POLAR_AGENCY_PRODUCT_ID=pro_xxx
POLAR_MASTER_PRODUCT_ID=pro_xxx
```

---

## 🔧 Automation Script

A helper script is available at `scripts/create-polar-products.ts`:

```bash
# Run the script (shows product config + guidance)
npx tsx scripts/create-polar-products.ts
```

The script:
1. ✅ Validates `POLAR_API_KEY` is set
2. ✅ Lists existing products
3. ✅ Displays all 12 products to create
4. ❌ Cannot create products (API limitation)

---

## ⏱️ Time Estimate

- **Per Product:** ~5 minutes
- **Total for 12 Products:** ~1 hour
- **Plus .env updates:** ~15 minutes
- **Total:** ~1 hour 15 minutes

---

## ✅ Verification

After creating products, verify:

```bash
# List products via API
curl -H "Authorization: Bearer $POLAR_API_KEY" \
  https://api.polar.sh/v1/products \
  | jq '.items[] | {name, price_amount}'
```

Should return 12 products with correct prices.

---

## 📝 Notes

- Polar.sh may add product creation API in the future
- For now, manual dashboard creation is the only option
- Consider bulk import CSV if Polar supports it

---

**Related Files:**
- `scripts/create-polar-products.ts` — Guidance script
- `packages/mekong-cli-core/src/payments/polar-client.ts` — Polar API client
