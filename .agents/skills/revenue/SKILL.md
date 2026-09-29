---
name: revenue
description: >-
  Revenue operations and financial management
---

# /revenue — Revenue Operations & Financial Intelligence Suite

Executive financial economics, MRR/ARR waterfall metrics, multi-tier subscription lifecycle management, payment reconciliation, and multi-scenario revenue forecasting.

---

## Subscription Tier Pricing

| Tier | Price (USD) | Price (VND) | Included MCU Credits | Best For |
|---|---|---|---|---|
| **Free** | $0/mo | 0 VND | 50 credits | Exploration & basic CLI tools |
| **Starter** | $49/mo | ~1,244,600 VND | 300 credits | Solo founder / single agent workflow |
| **Growth** | $149/mo | ~3,784,600 VND | 1,200 credits | High-velocity team / multi-agent pipelines |
| **Scale** | $299/mo | ~7,594,600 VND | 3,500 credits | Autonomous swarm execution |
| **Pro** | $499/mo | ~12,674,600 VND | 7,000 credits | Full agency OS & background daemons |
| **Enterprise** | $999/mo | ~25,374,600 VND | 15,000 credits | Dedicated on-prem & hybrid compute |

---

## Typer CLI Commands

```bash
# Revenue operations & financial health overview
mekong revenue [--json]

# Compute financial economics (MRR, ARR, ARPU, LTV, churn rate, NRR)
mekong revenue metrics [--period month|quarter|year] [--json]

# Record payment transaction into revenue ledger
mekong revenue record <customer_id> --amount <amount> [--name <customer_name>] [--tier starter|growth|scale|pro|enterprise] [--type subscription|one_time|addon|refund] [--gateway stripe|polar|bank_transfer|manual] [--currency USD|VND] [--notes <text>] [--no-auto-sub] [--json]

# Reconcile expected subscription dues against collected transactions
mekong revenue reconcile [--auto-fix] [--json]

# Project future MRR, ARR, and cumulative cash flows across scenarios
mekong revenue forecast [--months 3|6|12] [--scenario conservative|base|aggressive] [--json]

# View official tier pricing catalog
mekong revenue catalog [--currency USD|VND] [--json]

# Manage customer subscriptions
mekong revenue subscription create <customer_id> [--tier starter] [--amount 49] [--name <company>] [--cycle monthly|annual] [--json]
mekong revenue subscription list [--status active|cancelled|past_due|all] [--json]
mekong revenue subscription cancel <sub_id> [--reason "Plan downgraded"] [--json]
```

---

## Native MCP Tools

| MCP Tool | Description | Arguments |
|---|---|---|
| `mekong_revenue_metrics` | Calculate current MRR, ARR, ARPU, LTV, churn, and MRR waterfall | `period: str = "month"` |
| `mekong_revenue_record` | Record payment transaction into ledger and update subscriptions | `customer_id: str, amount: float, tier: str = "starter", txn_type: str = "subscription", currency: str = "USD"` |
| `mekong_revenue_forecast` | Forecast revenue and ARR over specified horizon and scenario | `months: int = 6, scenario: str = "base"` |
