---
name: ml-retrain
description: "Automated retraining triggers"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /ml:retrain — Auto Retrain

**IC super command** — Automated retraining triggers

## Pipeline

```
SEQUENTIAL: check-triggers → prepare-data → retrain → validate
```

## Trigger

Runs recipe `recipes/ml/retrain.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:retrain [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
