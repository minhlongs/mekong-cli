---
name: risk-monitor
description: "Continuous controls monitoring"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Continuous controls monitoring"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /risk:monitor — Controls Monitoring

**IC super command** — Continuous controls monitoring

## Pipeline

```
SEQUENTIAL: monitor-controls → alert-failures
    |
OUTPUT: reports/risk/monitor/
```

## Trigger

Runs recipe `recipes/risk/monitor.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/risk:monitor [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
