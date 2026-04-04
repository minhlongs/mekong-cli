---
name: ml-eval
description: "Prompt regression testing and semantic evaluation"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /ml:eval — Prompt Evaluation

**IC super command** — Prompt regression testing and semantic evaluation

## Pipeline

```
SEQUENTIAL: load-suite → run-evals → compare-baseline → report
```

## Trigger

Runs recipe `recipes/ml/eval.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:eval [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
