# Finance Operations — Mekong CLI

## Overview
Mekong CLI's finance operations cover revenue recognition, expense management, invoicing, cash flow, and monthly close — all executable via CLI commands. As a bootstrapped SaaS with Polar.sh as sole payment processor and Cloudflare as primary infrastructure, the finance stack is lean by design.

---

## Revenue Recognition

### MCU Credit Model
- Revenue recognized when MCU credits are *consumed* (delivery), not when purchased
- Deferred revenue: prepaid credits sitting in customer wallets (D1 ledger)
- Refund policy: unused credits refundable within 30 days (Polar.sh webhook reversal)

### Revenue Streams
| Stream | Recognition | Frequency |
|--------|------------|-----------|
| Starter $49 subscription | Monthly on renewal | Recurring |
| Pro $149 subscription | Monthly on renewal | Recurring |
| Enterprise $499 subscription | Monthly on renewal | Recurring |
| Annual prepay (20% discount) | Amortized monthly | Annual |
| Affiliate commissions (expense) | On referred conversion | Variable |

---

## Monthly Financial Close (command: `mekong finance-monthly-close`)

### Close Checklist (runs on last business day of month)
```
Day -5: mekong accounting-daily       → Reconcile all Polar.sh transactions
Day -3: mekong finance-collections    → Chase any failed renewals (Polar.sh retry)
Day -2: mekong expense                → Categorize and approve all expenses
Day -1: mekong invoice-gen            → Generate Enterprise customer invoices
Day 0:  mekong finance-monthly-close  → Full P&L, balance sheet, cash flow
Day +1: mekong business-financial-close → Board-ready summary + MRR waterfall
```

### Monthly Close Outputs
- P&L statement (MRR, expenses, net margin)
- MRR waterfall: new + expansion − churn − contraction
- Cash position (Polar.sh balance + bank)
- Runway calculation (`mekong finance/runway`)
- Expense categorization by department

---

## P&L Structure (Bootstrap Phase)

### Revenue
| Line | Month 3 | Month 6 | Month 12 |
|------|---------|---------|----------|
| Starter subscriptions | $2,450 | $7,350 | $19,600 |
| Pro subscriptions | $1,490 | $5,960 | $22,350 |
| Enterprise subscriptions | $998 | $3,992 | $14,970 |
| **Total MRR** | **$4,938** | **$17,302** | **$56,920** |

### Cost of Revenue (COGS)
| Item | Monthly Cost | Notes |
|------|-------------|-------|
| LLM API costs | ~$200-500 | Per MCU consumption, varies by provider |
| Cloudflare Workers/D1/KV | $0-50 | Within free tier at early scale |
| Polar.sh transaction fees | ~2.9% + $0.30 | Per transaction |
| **Total COGS** | **~$300-700** | Gross margin ~85-90% |

### Operating Expenses
| Item | Monthly | Annual |
|------|---------|--------|
| Hosting (Cloudflare) | $0 | $0 |
| LLM inference (production) | $200-500 | $2,400-6,000 |
| Email / newsletter tool | $0 (Mekong CLI handles) | $0 |
| Legal (annual) | $0-100 | $500-1,200 |
| Accounting (CPA) | $200 | $2,400 |
| Marketing (content) | $0 (AI-generated) | $0 |
| Conference/travel | $500/quarter | $2,000 |
| **Total OpEx** | **~$900-1,300** | **~$10,800-15,600** |

### Unit Economics at Scale
| Metric | Value |
|--------|-------|
| Gross margin | ~87% |
| CAC (PLG) | ~$10 (content cost amortized) |
| CAC (SDR-assisted) | ~$150-300 |
| LTV Starter | $49 × 18mo avg = $882 |
| LTV Pro | $149 × 24mo avg = $3,576 |
| LTV Enterprise | $499 × 36mo avg = $17,964 |
| LTV:CAC ratio | >10x (Starter PLG) |

---

## Expense Management (commands: `mekong expense`, `mekong finance/expense`)

### Expense Categories
- **Infrastructure**: Cloudflare, domain, SSL
- **LLM inference**: OpenRouter, Anthropic, Qwen API costs
- **People**: Contractors (dev, content, design)
- **Marketing**: Ads, conference, swag
- **Legal & compliance**: Contracts, IP, privacy
- **Tools**: Any SaaS (minimize — eat our own dogfood)

### Approval Policy
- <$100: Auto-approved, log in daily accounting
- $100-500: Founder approval required
- >$500: Board-level awareness (documented in `finance-monthly-close`)

Daily accounting command: `mekong accounting-daily` — reviews transactions, flags anomalies, posts to ledger.

---

## Invoicing (commands: `mekong invoice`, `mekong invoice-gen`)

### Invoice Workflow
- Starter/Pro: Automated via Polar.sh (no manual invoice)
- Enterprise: Manual invoice generated via `mekong invoice-gen`
  - Net 30 payment terms
  - Wire transfer or Polar.sh payment link
  - Follow-up via `mekong finance-collections` if overdue

### Collections Process (`mekong finance-collections`)
```
Day 1 overdue:  Automated email reminder (Polar.sh)
Day 7 overdue:  mekong finance-collections → Personal email from founder
Day 14 overdue: Suspend account (HTTP 402), final notice
Day 30 overdue: Collections escalation, account termination
```

---

## Cash Flow Management

### Cash Runway Model (`mekong finance/runway`)
At bootstrap (Month 0):
- Starting cash: $0 (bootstrapped from revenue)
- Monthly burn: ~$1,000-1,300
- Break-even MRR needed: ~$1,200
- Break-even timeline: Month 1-2 with first paying customers

### Cash Flow Levers
- Annual prepay: 10 Enterprise annual = +$59,880 upfront cash
- Minimize SaaS spend: Use Mekong CLI for everything
- LLM cost optimization: Route to cheapest provider per task
- Polar.sh payout schedule: Configure weekly payouts

---

## Financial Controls

| Control | Mechanism |
|---------|-----------|
| Revenue tracking | Polar.sh webhook → D1 ledger |
| MCU deduction | Atomic DB transaction (no double-spend) |
| Refund handling | Polar.sh webhook reversal → credit restore |
| Expense approval | Manual review + `accounting-daily` audit |
| Fraud prevention | Rate limiting + HTTP 402 at zero balance |
| Tax compliance | Polar.sh handles VAT/sales tax collection |

---

## Budget Planning (command: `mekong finance-budget-plan`)

### Annual Budget 2026
| Quarter | Revenue Target | Expense Budget | Net Income |
|---------|--------------|----------------|------------|
| Q1 2026 | $5,000 | $3,000 | $2,000 |
| Q2 2026 | $20,000 | $5,000 | $15,000 |
| Q3 2026 | $60,000 | $12,000 | $48,000 |
| Q4 2026 | $150,000 | $25,000 | $125,000 |
| **FY 2026** | **$235,000** | **$45,000** | **$190,000** |

Note: Budget scales with revenue (marketing spend activated post-break-even).
