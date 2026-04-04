---
name: sales-deal-close
description: "Research buyer, build proposal, pricing strategy, closing playbook. 4 commands, ~20 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sales:deal-close — Deal Closer

**Super command** — chains 4 commands via DAG pipeline.

## Pipeline

```
PARALLEL: /customer-research + /competitor     (~8 min)
    |
SEQUENTIAL: /proposal → /close                 (~12 min)
    |
OUTPUT: reports/sales/deal/
```

## Estimated: 15 credits, 20 minutes

## Execution

Load recipe: `recipes/sales/deal-close.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
