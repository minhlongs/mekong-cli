---
name: vendor-spend
description: "License optimization and usage tracking"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /vendor:spend — Vendor Spend

**IC super command** — License optimization and usage tracking

## Pipeline

```
SEQUENTIAL: collect-invoices → analyze-usage → optimize
```

## Trigger

Runs recipe `recipes/vendor/spend.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:spend [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
