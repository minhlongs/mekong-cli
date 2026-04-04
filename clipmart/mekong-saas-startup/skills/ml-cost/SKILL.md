---
name: ml-cost
description: "Per-request cost tracking and budget alerting"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /ml:cost — Inference Cost

**IC super command** — Per-request cost tracking and budget alerting

## Pipeline

```
SEQUENTIAL: collect-usage → allocate-costs → set-alerts
```

## Trigger

Runs recipe `recipes/ml/cost.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:cost [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
