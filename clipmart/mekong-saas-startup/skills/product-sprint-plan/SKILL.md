---
name: product-sprint-plan
description: "Backlog grooming → sprint scope → task breakdown → assignments. 4 commands, ~20 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# Sprint Planning

> Trigger: `/product:sprint-plan $ARGUMENTS`
> Estimated: ~20 min

## Execution

Load recipe: `recipes/product/sprint-plan.json`

Run the DAG workflow:

### Backlog Grooming (parallel)
- `feedback`
- `roadmap`

### Sprint Definition (sequential)
- `sprint`
- `estimate`


## Instructions

1. Read recipe DAG definition
2. Execute groups in dependency order
3. Parallel groups run simultaneously
4. Write outputs to `reports/sprint`
5. Report completion with summary

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
