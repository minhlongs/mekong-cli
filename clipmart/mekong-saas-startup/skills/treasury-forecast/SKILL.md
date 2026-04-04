---
name: treasury-forecast
description: "13-week rolling cash forecast"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "13-week rolling cash forecast"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /treasury:forecast — Cash Forecast

**IC super command** — 13-week rolling cash forecast

## Pipeline

```
SEQUENTIAL: pull-actuals → project-inflows → project-outflows → model
```

## Trigger

Runs recipe `recipes/treasury/forecast.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/treasury:forecast [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
