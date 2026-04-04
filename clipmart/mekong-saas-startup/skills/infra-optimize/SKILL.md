---
name: infra-optimize
description: "Infrastructure cost and performance optimization"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Infrastructure cost and performance optimization"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /infra:optimize — Infra Optimize

**IC super command** — Infrastructure cost and performance optimization

## Pipeline

```
SEQUENTIAL: benchmark-current → identify-waste → recommend-changes
```

## Trigger

Runs recipe `recipes/infra/optimize.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/infra:optimize [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
