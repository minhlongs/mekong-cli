# Accountant Report — Mekong CLI
*Role: Accountant | Date: 2026-03-11*

---

## Entity Structure

Operating entity: **Binh Phap Venture Studio**
Product: Mekong CLI (MIT open source + RaaS commercial layer)
Payment processor: Polar.sh (handles merchant of record obligations)

As Polar.sh acts as merchant of record for subscription billing, Binh Phap Venture
Studio receives net payouts after Polar.sh fees — simplifying VAT/GST obligations
significantly for international sales.

---

## Chart of Accounts

```
ASSETS
  1000 - Cash (bank accounts)
  1010 - Stripe/Polar.sh pending payouts
  1020 - Accounts receivable (Enterprise invoices)

LIABILITIES
  2000 - Deferred revenue (prepaid MCU credits)
  2010 - Accounts payable (LLM API invoices)
  2020 - Payment processing fees payable

EQUITY
  3000 - Owner's equity
  3010 - Retained earnings

REVENUE
  4000 - Subscription revenue - Starter ($49/mo)
  4010 - Subscription revenue - Pro ($149/mo)
  4020 - Subscription revenue - Enterprise ($499/mo)
  4030 - Custom development revenue (add-on services)

COST OF REVENUE
  5000 - LLM API costs (OpenRouter/DeepSeek/Anthropic)
  5010 - Payment processing fees (Polar.sh ~2.9% + $0.30)
  5020 - Cloudflare overage charges (if any)

OPERATING EXPENSES
  6000 - Domain and tooling ($3/mo)
  6010 - Software subscriptions (GitHub, design tools)
  6020 - Personnel costs (future hires)
  6030 - Marketing spend
  6040 - Legal and professional fees
  6050 - Contractor payments
```

---

## Polar.sh Revenue Reconciliation

Polar.sh pays out on a rolling basis (typically weekly or monthly depending on settings).
Reconciliation process:

1. **Daily:** Export Polar.sh transaction log via API or dashboard CSV
2. **Weekly:** Match Polar.sh payouts to bank deposits
3. **Monthly:** Reconcile deferred revenue (MCU credits sold vs consumed)

Key Polar.sh data points needed per transaction:
- `subscription_id` — links to customer
- `amount_paid` — gross charge to customer
- `platform_fee` — Polar.sh fee amount
- `net_amount` — payout to Binh Phap Venture Studio
- `currency` — USD assumed, watch for international
- `created_at` — for revenue recognition date

---

## Revenue Recognition Policy

**MCU credits = prepaid service obligation (deferred revenue)**

When customer pays $49 for 200 Starter credits:
```
Dr. Cash / Polar.sh receivable    $49.00
  Cr. Deferred Revenue            $49.00
```

As MCU credits are consumed (tracked via D1 database):
```
Dr. Deferred Revenue              $X.XX (per MCU consumed)
  Cr. Subscription Revenue        $X.XX
```

**ASC 606 / IFRS 15 compliance:** Revenue recognized when performance obligation
satisfied = when MCU credit successfully executes a mission.

Unused credits at month-end remain as deferred revenue on balance sheet.
No-refund policy means deferred revenue will be recognized over time as credits expire
(typical SaaS policy: recognize expired credits as revenue at expiry date).

---

## LLM API Cost Tracking

Variable cost tracking is critical as LLM pricing changes frequently.

| Provider | Billing Method | Tracking |
|----------|---------------|---------|
| OpenRouter | Per token, monthly invoice | API usage dashboard |
| DeepSeek | Per token, prepaid credits | Credit balance monitoring |
| Anthropic | Per token, monthly invoice | Console usage page |
| Ollama | Free (local) | $0 — no tracking needed |

**Cost per MCU estimate:**
- Average mission = ~50 LLM calls × ~500 tokens = 25,000 tokens
- DeepSeek at $0.001/1K tokens = $0.025 per MCU (cost)
- Starter tier: 200 MCU × $0.025 = $5.00 LLM cost vs $49 revenue = 90% gross margin

Track monthly: total tokens consumed per provider → map to actual invoice.

---

## Tax Considerations

**Vietnam (Binh Phap Venture Studio domicile):**
- Corporate income tax: 20% on net profit
- VAT: 10% on services — Polar.sh as merchant of record handles collection
- Software/SaaS typically qualifies for preferential tech enterprise rates

**US Sales Tax / International VAT:**
- Polar.sh as merchant of record = they collect and remit sales tax/VAT
- Binh Phap Venture Studio does NOT need to register for sales tax in each US state
- Confirm with Polar.sh: verify they hold merchant of record status explicitly

**Contractor payments:**
- Future contractors in US: issue 1099-NEC if paid >$600/year
- International contractors: W-8BEN on file, no 1099 required

---

## Monthly Close Checklist

- [ ] Export Polar.sh transactions CSV for the month
- [ ] Reconcile payouts to bank statement
- [ ] Calculate MCU consumed vs credits sold (D1 query)
- [ ] Book deferred revenue → earned revenue journal entry
- [ ] Pull LLM API invoices (OpenRouter, DeepSeek, Anthropic)
- [ ] Calculate gross margin: (Revenue - LLM costs - Polar.sh fees) / Revenue
- [ ] Update MRR tracker: new subscriptions, upgrades, cancellations, net new MRR
- [ ] Review cash position: runway calculation

---

## Key Financial KPIs to Report Monthly

| KPI | Formula |
|-----|---------|
| Gross Margin | (Revenue - COGS) / Revenue |
| MRR | Sum of all active subscription monthly values |
| ARR | MRR × 12 |
| LTV | ARPU × (1 / Monthly Churn Rate) |
| CAC | Total Sales + Marketing Spend / New Paying Customers |
| LTV:CAC | LTV / CAC (target: >3x) |
| Months to Recover CAC | CAC / (ARPU × Gross Margin %) |
| Runway | Cash Balance / Monthly Burn Rate |

---

## Q2 Accounting Actions

- [ ] Open dedicated business bank account for Binh Phap Venture Studio
- [ ] Configure Polar.sh payout schedule (weekly recommended for cash flow)
- [ ] Set up accounting software (Wave free, or Xero at $15/mo)
- [ ] Build Polar.sh → accounting reconciliation script (Python + Polar.sh API)
- [ ] Confirm Polar.sh merchant-of-record status for tax obligations
- [ ] Create monthly close checklist and schedule (last business day of month)
