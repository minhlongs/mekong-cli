---
name: revops-forecast
description: "Pipeline-weighted forecast and scenario modeling"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /revops:forecast — Revenue Forecast

**IC super command** — Pipeline-weighted forecast and scenario modeling

## Pipeline

```
SEQUENTIAL: pull-pipeline → weight-stages → model-scenarios → report
```

## Trigger

Runs recipe `recipes/revops/forecast.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:forecast [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
