---
name: finops-optimize
description: "Reserved instance management and rightsizing"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /finops:optimize — Cloud Optimize

**IC super command** — Reserved instance management and rightsizing

## Pipeline

```
PARALLEL: ri-analysis + rightsizing-scan\n    |\nSEQUENTIAL: recommendations
```

## Trigger

Runs recipe `recipes/finops/optimize.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/finops:optimize [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
