---
name: finops-cost
description: "Cloud cost allocation per customer and feature"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Cloud cost allocation per customer and feature"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /finops:cost — Cloud Cost

**IC super command** — Cloud cost allocation per customer and feature

## Pipeline

```
SEQUENTIAL: collect-usage → tag-allocate → report
```

## Trigger

Runs recipe `recipes/finops/cost.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/finops:cost [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
