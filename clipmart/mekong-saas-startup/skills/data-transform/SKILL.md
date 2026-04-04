---
name: data-transform
description: "dbt run/test with lineage tracking"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "dbt run/test with lineage tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:transform — Data Transform

**IC super command** — dbt run/test with lineage tracking

## Pipeline

```
SEQUENTIAL: dbt-run → dbt-test → update-lineage
OUTPUT: reports/data/transform/
```

## Trigger

Runs recipe `recipes/data/transform.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:transform [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
