---
name: finops-budget
description: "Cost alerts and approval workflows"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /finops:budget — Cloud Budget

**IC super command** — Cost alerts and approval workflows

## Pipeline

```
SEQUENTIAL: set-budgets → configure-alerts → approval-flow
```

## Trigger

Runs recipe `recipes/finops/budget.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/finops:budget [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
