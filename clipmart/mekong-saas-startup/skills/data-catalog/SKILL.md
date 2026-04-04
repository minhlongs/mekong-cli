---
name: data-catalog
description: "Data discovery and lineage tracking"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Data discovery and lineage tracking"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /data:catalog — Data Catalog

**IC super command** — Data discovery and lineage tracking

## Pipeline

```
SEQUENTIAL: crawl-sources → classify-pii → publish-catalog
OUTPUT: reports/data/catalog/
```

## Trigger

Runs recipe `recipes/data/catalog.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/data:catalog [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
