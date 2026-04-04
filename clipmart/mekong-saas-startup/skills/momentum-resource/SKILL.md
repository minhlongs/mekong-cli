---
name: momentum-resource
description: "Allocate resources by momentum score — invest in winners"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Allocate resources by momentum score — invest in winners"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /momentum:resource — Resource Allocation

**IC super command** — Allocate resources by momentum score — invest in winners

## Pipeline

```
SEQUENTIAL: score-projects → rank-by-momentum → allocate-budget
```

## Trigger

Runs recipe `recipes/momentum/resource.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/momentum:resource [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
