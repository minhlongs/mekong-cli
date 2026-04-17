# Finance Department as a Service

> Replace a part-time CFO + bookkeeper with autonomous agents. Monthly close in hours, not weeks.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Part-time CFO ($8k/mo) | $96,000/yr | $49/mo floor |
| Bookkeeper ($3k/mo) | $36,000/yr | $10/deliverable |
| FP&A tools | $5,000/yr | Included |
| **Total replaced** | **$137,000/yr** | **~$1,800/yr** |

## What This Department Does

1. **Monthly Close** — Automated reconciliation, accruals, journal entries, financial statements
2. **Budget Planning** — Annual budget with variance tracking vs actuals
3. **Collections** — AR aging, automated dunning, escalation workflows
4. **Forecasting** — Rolling 13-week cash flow, revenue forecasts by segment
5. **Investor Reporting** — Monthly investor updates with financial metrics

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Monthly financial close | $50 |
| Annual budget plan | $60 |
| Collections workflow run | $20 |
| Investor financial report | $40 |
| Rolling cash flow forecast | $25 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong finance-budget-plan      # Annual budget build
mekong finance-monthly-close    # Month-end close workflow
mekong finance-collections      # AR collections automation
mekong business-financial-close # Business-side close coordination
mekong analyst-forecast-update  # Forecast model update
mekong analyst-report           # Financial analysis report
```

## Install

```bash
mekong install dept-finance
```

## Configuration

```bash
# .mekong/.env.dept-finance
DEPT_FINANCE_ACCOUNTING_SYSTEM=quickbooks  # quickbooks|xero|netsuite
DEPT_FINANCE_API_KEY=your_key
DEPT_FINANCE_BANK_FEED=mercury  # mercury|brex|stripe
DEPT_FINANCE_FISCAL_YEAR_END=12
DEPT_FINANCE_CURRENCY=USD
DEPT_FINANCE_CLOSE_TARGET_DAYS=5  # target business days for monthly close
```

## Example Workflow: Month-End Close

```
Day 1 of new month:
  mekong finance-monthly-close --month 2026-03 --dry-run
  → Identifies reconciliation gaps, missing invoices

Day 2: Human reviews gap list, fixes anomalies

Day 3: mekong finance-monthly-close --month 2026-03 --execute
  → Runs automated journal entries, closes period

Day 4: mekong analyst-report --month 2026-03
  → P&L, balance sheet, cash flow statement ready for review

Day 5: Human approves + distributes to investors
```

## Comparison: Traditional vs SaS

| Metric | Traditional CFO | Finance Dept SaS |
|--------|----------------|-----------------|
| Monthly cost | $8,000+ | $49 floor |
| Close cycle | 10-15 business days | 3-5 days |
| Forecast accuracy | ±20% | ±10% (with data feeds) |
| Investor report prep | 2 days | 2 hours |
