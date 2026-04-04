---
description: "Pipeline orchestration with Fivetran/Airbyte connectors"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:ingest — Data Ingestion

**IC super command** — Pipeline orchestration with Fivetran/Airbyte connectors

## Pipeline

```
SEQUENTIAL: configure-connectors → extract-load → verify-landing
OUTPUT: reports/data/ingest/
```

## Trigger

Runs recipe `recipes/data/ingest.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:ingest [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
