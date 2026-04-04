---
name: compliance-sox-cycle
description: "Full SOX cycle — SOX testing, ITGC, risk assessment, risk report"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /compliance:sox-cycle — SOX Compliance Cycle

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
PARALLEL: /audit:sox + /audit:itgc + /risk:assess
    |
SEQUENTIAL: /risk:report
    |
OUTPUT: reports/compliance/sox-cycle/
```

## Trigger

Runs recipe `recipes/compliance/sox-cycle.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/compliance:sox-cycle [goal]
```

## Estimated: 16 credits, 30 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
