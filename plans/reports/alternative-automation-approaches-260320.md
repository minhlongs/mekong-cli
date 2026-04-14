# Alternative Automation Approaches — OpenClaw

**Date:** 2026-03-20
**Context:** Context 92% — Session compaction needed

---

## 🔍 Research Findings

### Polar.sh API Limitation

**Discovery:** Polar.sh **does not have** a `POST /v1/products` endpoint.

**Available Endpoints:**
```
✅ GET  /v1/products          — List products
✅ GET  /v1/products/{id}     — Get product
✅ POST /v1/checkouts         — Create checkout
✅ GET  /v1/subscriptions     — List subscriptions
✅ POST /v1/benefit_grants    — Grant benefits
❌ POST /v1/products          — NOT AVAILABLE
```

**Reference:** https://docs.polar.sh/api-reference

---

## 🎯 Alternative Approaches

### Option 1: Manual Dashboard (CURRENT)

**Pros:**
- Works immediately
- No code needed
- Visual confirmation

**Cons:**
- ~1 hour manual work
- Error-prone (typos possible)
- Not reproducible

**Time:** 1.5 hours

---

### Option 2: Browser Automation (Playwright)

**Approach:** Use Playwright to automate dashboard clicks

**Pros:**
- Reproducible
- Can re-run for new tiers/apps
- Records audit trail

**Cons:**
- Brittle (UI changes break script)
- Requires login session
- Complex to maintain

**Time to Build:** 2-3 hours
**Time to Run:** 5 minutes

**Implementation:**
```typescript
// scripts/create-polar-products-playwright.ts
import { test, expect } from '@playwright/test';

test('create 12 Polar products', async ({ page }) => {
  await page.goto('https://polar.sh/dashboard/login');
  await page.fill('[name=email]', process.env.POLAR_EMAIL!);
  await page.fill('[name=password]', process.env.POLAR_PASSWORD!);
  await page.click('button[type=submit]');

  for (const product of PRODUCTS) {
    await page.click('text=New Product');
    await page.fill('[name=name]', product.name);
    await page.fill('[name=price]', String(product.priceAmount));
    // ... more fields
    await page.click('button[type=submit]');
    await expect(page).toContainText('Product created');
  }
});
```

---

### Option 3: Terraform/Pulumi (Infrastructure as Code)

**If Polar supports Terraform provider:**

```hcl
resource "polar_product" "raas_gateway_starter" {
  name               = "RaaS Gateway - Starter"
  description        = "50 MCU/month"
  price_amount       = 2900
  price_currency     = "USD"
  recurring_interval = "month"
}
```

**Status:** ❌ Polar.sh Terraform provider does not exist (checked)

---

### Option 4: CSV Bulk Import (IF AVAILABLE)

Check if Polar supports CSV import:
1. Go to Products page
2. Look for "Import" button
3. Upload CSV with product definitions

**CSV Format:**
```csv
name,description,price_amount,price_currency,recurring_interval
"RaaS Gateway - Starter","50 MCU/month",2900,USD,month
"RaaS Gateway - Pro","200 MCU/month",9900,USD,month
...
```

**Status:** ❓ Need to verify with Polar dashboard

---

### Option 5: Polar Support Request

**Action:** Contact Polar.sh support to request:
1. Bulk import feature
2. API endpoint for product creation
3. Partner/agency tools

**Contact:** hello@polar.sh or Discord

---

## 📊 Recommendation

### Immediate (This Week)
**Use Option 1 — Manual Dashboard**
- Fastest path to GTM
- One-time effort
- Blocks on human action only

### Medium-Term (Next Month)
**Build Option 2 — Playwright Automation**
- Useful for future product launches
- Can share with other agencies
- Marketing content opportunity ("How we automated SaaS pricing")

### Long-Term (Q3 2026)
**Advocate for Option 4/5**
- Request Polar to add bulk import
- Contribute to Terraform provider if community starts one

---

## 🚀 Action Items

| Priority | Action | Owner | Time |
|----------|--------|-------|------|
| P0 | Manual create 12 products | Human | 1.5h |
| P1 | Verify CSV import availability | CC CLI | 10m |
| P2 | Build Playwright automation | CC CLI | 3h |
| P3 | Contact Polar support | Human | 30m |

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `scripts/create-polar-products.ts` | Guidance script (shows config) |
| `plans/reports/polar-product-creation-guide-260320.md` | Manual steps |
| `plans/reports/alternative-automation-approaches-260320.md` | This report |

---

## 💡 Key Insight

**Lesson:** Not everything can/will be automated. Some tasks require human touch.

**Binh Pháp Principle:** 形勢 (Energy) — Adapt to terrain, don't fight reality.

**Action:** Human creates products → CC CLI tests flows → Both win.

---

**Report:** `/plans/reports/alternative-automation-approaches-260320.md`
