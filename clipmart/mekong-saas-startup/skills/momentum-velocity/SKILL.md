---
name: momentum-velocity
description: "Track MRR growth rate, user acquisition speed, feature ship rate"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /momentum:velocity — Scaling Velocity

**IC super command** — Track MRR growth rate, user acquisition speed, feature ship rate

## Pipeline

```
SEQUENTIAL: pull-metrics → calculate-velocity → trend-report
```

## Trigger

Runs recipe `recipes/momentum/velocity.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/momentum:velocity [goal]
```

## Estimated: 3 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
