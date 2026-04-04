---
name: risk-assess
description: "Enterprise risk library and scoring"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Enterprise risk library and scoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /risk:assess — Risk Assessment

**IC super command** — Enterprise risk library and scoring

## Pipeline

```
PARALLEL: catalog-processes + identify-risks
    |
SEQUENTIAL: map-controls → score-residual
    |
OUTPUT: reports/risk/assess/
```

## Trigger

Runs recipe `recipes/risk/assess.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/risk:assess [goal]
```

## Estimated: 5 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
