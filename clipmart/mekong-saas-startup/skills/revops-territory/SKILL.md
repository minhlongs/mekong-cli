---
name: revops-territory
description: "Territory planning and quota allocation"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Territory planning and quota allocation"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /revops:territory — Territory Planning

**IC super command** — Territory planning and quota allocation

## Pipeline

```
SEQUENTIAL: segment-market → assign-territories → set-quotas
```

## Trigger

Runs recipe `recipes/revops/territory.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:territory [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
