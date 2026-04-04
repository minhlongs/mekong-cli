---
name: risk-report
description: "Board-ready risk reports"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /risk:report — Risk Report

**IC super command** — Board-ready risk reports

## Pipeline

```
SEQUENTIAL: heat-map → deficiency-track → remediation-status
    |
OUTPUT: reports/risk/report/
```

## Trigger

Runs recipe `recipes/risk/report.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/risk:report [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
