---
name: product-discovery
description: "Problem → persona → solution → validation. 5 commands, ~30 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Problem → persona → solution → validation. 5 commands, ~30 min."
argument-hint: [product context or goal]
---

# Product Discovery Sprint

> Trigger: `/product:discovery $ARGUMENTS`
> Estimated: ~30 min

## Execution

Load recipe: `recipes/product/discovery.json`

Run the DAG workflow:

### Understand Problem Space (parallel)
- `persona`
- `competitor`
- `brainstorm`

### Define Solution (sequential)
- `scope`
- `estimate`


## Instructions

1. Read recipe DAG definition
2. Execute groups in dependency order
3. Parallel groups run simultaneously
4. Write outputs to `reports/discovery`
5. Report completion with summary

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
