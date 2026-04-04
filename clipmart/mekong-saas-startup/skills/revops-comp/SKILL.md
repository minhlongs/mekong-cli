---
name: revops-comp
description: "Commission calculation and SPIFs"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /revops:comp — Commission Calc

**IC super command** — Commission calculation and SPIFs

## Pipeline

```
SEQUENTIAL: pull-bookings → apply-plan → calculate-comp → approve
```

## Trigger

Runs recipe `recipes/revops/comp.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:comp [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
