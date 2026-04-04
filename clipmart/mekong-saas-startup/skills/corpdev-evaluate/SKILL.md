---
name: corpdev-evaluate
description: "Acqui-hire and acquisition evaluation"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /corpdev:evaluate — Acquisition Eval

**IC super command** — Acqui-hire and acquisition evaluation

## Pipeline

```
PARALLEL: financial-model + team-assess + tech-assess\n    |\nSEQUENTIAL: recommendation
```

## Trigger

Runs recipe `recipes/corpdev/evaluate.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/corpdev:evaluate [goal]
```

## Estimated: 5 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
