---
name: terrain-retreat
description: "Strategic retreat and market exit criteria"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /terrain:retreat — Strategic Retreat

**IC super command** — Strategic retreat and market exit criteria

## Pipeline

```
SEQUENTIAL: assess-viability → define-triggers → exit-plan
```

## Trigger

Runs recipe `recipes/terrain/retreat.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:retreat [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
