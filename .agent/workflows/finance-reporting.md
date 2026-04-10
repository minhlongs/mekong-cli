---
description: How to track P&L and financial performance for agencies
---

# 📊 Finance Reporting Workflow

Set up comprehensive financial tracking and reporting for your agency.

## 🤖 Quick Execute
```bash
Execute workflow: https://mekongmind.com/docs/workflows/finance-reporting
```

## ⚡ Step-by-Step Execution

### Step 1: Initialize Finance Module (2 min)
// turbo
```bash
# Set up finance tracking
mekong finance:init --currency USD

# Expected: ✅ Finance module initialized
```

### Step 2: Configure Revenue Streams (3 min)
// turbo
```bash
# Define revenue categories
mekong finance:streams --add retainer,project,equity,success-fee

# Stream Types:
# - retainer: Monthly recurring
# - project: One-time projects
# - equity: Startup equity stakes
# - success-fee: Performance bonuses
```

### Step 3: Set Up Expense Categories (3 min)
// turbo
```bash
# Configure expense tracking
mekong finance:expenses --categories payroll,tools,marketing,office,contractors

# Category allocation:
# - Payroll: ~50-60%
# - Tools: ~10-15%
# - Marketing: ~5-10%
# - Office: ~5-10%
# - Contractors: ~10-20%
```

### Step 4: Generate P&L Report (2 min)
// turbo
```bash
# Create profit & loss statement
mekong finance:pnl --period this-month

# Output:
# ┌─────────────────────────────────┐
# │ REVENUE                         │
# │   Retainer: $XX,XXX             │
# │   Project: $X,XXX               │
# │ EXPENSES                        │
# │   Payroll: $XX,XXX              │
# │   Tools: $X,XXX                 │
# │ NET PROFIT: $X,XXX              │
# │ MARGIN: XX%                     │
# └─────────────────────────────────┘
```

### Step 5: Set Up Cash Flow Alerts (2 min)
// turbo
```bash
# Configure runway alerts
mekong finance:alerts --runway-warning 3m --low-cash 10000

# Alerts:
# - Runway < 3 months: WARNING
# - Cash < $10,000: CRITICAL
```

### Step 6: Schedule Monthly Close (2 min)
// turbo
```bash
# Automate monthly financial close
mekong finance:schedule --monthly-close "last-friday"

# Expected: ✅ Monthly close scheduled
```

## 📋 Financial Templates

### P&L Categories
```yaml
revenue:
  - retainer_mrr
  - project_revenue
  - equity_exits
  - success_fees
  - training_workshops

expenses:
  - payroll
  - contractor_fees
  - software_tools
  - office_space
  - marketing
  - professional_services
  - travel
```

### Key Metrics
```yaml
financial_kpis:
  gross_margin: Target > 70%
  net_margin: Target > 20%
  revenue_per_employee: Target > $150K
  cash_runway: Target > 6 months
```

## ✅ Success Criteria
- [ ] Finance module initialized
- [ ] Revenue streams configured
- [ ] Expense categories set up
- [ ] P&L report generating
- [ ] Cash flow alerts active
- [ ] Monthly close scheduled

## 🔗 Next Workflow
After finance reporting: `/vc-readiness` or `/hr-hiring`

## 🏯 Binh Pháp Alignment
"兵馬未動，糧草先行" (Before troops move, supplies go first) - Cash is the oxygen of business.
