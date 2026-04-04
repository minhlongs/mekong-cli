---
name: business-financial-close
description: "Monthly/quarterly close — reconcile, report, forecast, tax prep. 5 commands, ~25 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# Financial Close

> Trigger: `/business:financial-close $ARGUMENTS`
> Estimated: ~25 min

## Execution

Load recipe: `recipes/business/financial-close.json`

Run the DAG workflow:

### Reconciliation (parallel)
- `revenue`
- `expense`
- `invoice`

### Financial Statements (sequential)
- `financial-report`
- `tax`


## Instructions

1. Read recipe DAG definition
2. Execute groups in dependency order
3. Parallel groups run simultaneously
4. Write outputs to `reports/financial-close`
5. Report completion with summary

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
