---
name: esg-report
description: "Sustainability reporting with GRI/SASB frameworks"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Sustainability reporting with GRI/SASB frameworks"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /esg:report — ESG Report

**IC super command** — Sustainability reporting with GRI/SASB frameworks

## Pipeline

```
PARALLEL: collect-environmental + collect-social + collect-governance\n    |\nSEQUENTIAL: compile-report
```

## Trigger

Runs recipe `recipes/esg/report.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/esg:report [goal]
```

## Estimated: 3 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
