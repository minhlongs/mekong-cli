---
name: data-access
description: "Row-level security and audit logging"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /data:access — Data Access Control

**IC super command** — Row-level security and audit logging

## Pipeline

```
SEQUENTIAL: scan-policies → enforce-rls → audit-log-report
OUTPUT: reports/data/access/
```

## Trigger

Runs recipe `recipes/data/access.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:access [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
