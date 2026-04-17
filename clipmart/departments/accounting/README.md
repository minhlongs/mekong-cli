# Accounting Department as a Service

> Replace a $5k/mo bookkeeper + accounting firm with AI agents that handle daily books, invoices, and month-end close.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Bookkeeper ($5k/mo) | $60,000/yr | $49/mo floor |
| Accounting firm (tax/close) | $12,000/yr | $0.50/transaction |
| QuickBooks | $1,200/yr | Included |
| Bill.com | $1,500/yr | Included |
| **Total replaced** | **$74,700/yr** | **~$2,400/yr** |

## What This Department Does

1. **Daily Bookkeeping** — Categorize transactions, reconcile bank feeds, flag anomalies
2. **Invoice Processing** — Generate, send, track, and follow-up on invoices
3. **Month-End Close** — Reconciliation, accruals, financial statement generation
4. **AP/AR Management** — Aging reports, payment runs, collections triggers
5. **Tax Prep Support** — Organize documents, categorize expenses, 1099 prep

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Daily bookkeeping run | $5 |
| Invoice batch processed (50) | $10 |
| Month-end reconciliation | $40 |
| AP/AR aging report | $15 |
| Annual tax prep package | $100 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong accounting-daily           # Daily bookkeeping
mekong accounting-invoice-batch   # Invoice batch processing
mekong finance-monthly-close      # Month-end close
mekong finance-collections        # Collections automation
mekong business-financial-close   # Business financial close
```

## Install

```bash
mekong install dept-accounting
```

## Configuration

```bash
# .mekong/.env.dept-accounting
DEPT_ACCOUNTING_SYSTEM=quickbooks  # quickbooks|xero|freshbooks
DEPT_ACCOUNTING_API_KEY=your_key
DEPT_ACCOUNTING_BANK=mercury  # mercury|brex|chase
DEPT_ACCOUNTING_BANK_FEED_TOKEN=your_token
DEPT_ACCOUNTING_DEFAULT_CURRENCY=USD
DEPT_ACCOUNTING_CLOSE_DAY=5  # day of month to run close
```

## Comparison

| Metric | Traditional Bookkeeper | Accounting Dept SaS |
|--------|----------------------|---------------------|
| Monthly cost | $3,000-8,000 | $49 floor |
| Close cycle | 15-20 days | 3-5 days |
| Invoice processing | Manual | Automated |
| Anomaly detection | Weekly review | Real-time |
