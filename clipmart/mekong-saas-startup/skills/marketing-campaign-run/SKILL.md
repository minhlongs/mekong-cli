---
name: marketing-campaign-run
description: "Audience targeting, ad creatives, channel strategy, campaign launch checklist. 4 commands, ~25 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /marketing:campaign-run — Campaign Execution

**Super command** — chains 4 commands via DAG pipeline.

## Pipeline

```
PARALLEL: /marketing-plan + /customer-research (~10 min)
    |
PARALLEL: /ads + /campaign                     (~15 min)
    |
OUTPUT: reports/marketing/campaign/
```

## Estimated: 15 credits, 25 minutes

## Execution

Load recipe: `recipes/marketing/campaign-run.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
