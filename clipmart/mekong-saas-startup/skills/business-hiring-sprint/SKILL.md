---
name: business-hiring-sprint
description: "End-to-end recruiting — JD, sourcing, interview kit, comp benchmarking. 4 commands, ~20 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# Hiring Sprint

> Trigger: `/business:hiring-sprint $ARGUMENTS`
> Estimated: ~20 min

## Execution

Load recipe: `recipes/business/hiring-sprint.json`

Run the DAG workflow:

### Job Preparation (parallel)
- `hr-management`
- `budget`

### Sourcing & Screening (sequential)
- `leadgen`
- `schedule`


## Instructions

1. Read recipe DAG definition
2. Execute groups in dependency order
3. Parallel groups run simultaneously
4. Write outputs to `reports/hiring`
5. Report completion with summary

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
