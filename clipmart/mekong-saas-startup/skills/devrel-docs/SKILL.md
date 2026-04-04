---
name: devrel-docs
description: "API reference generation and versioning"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "API reference generation and versioning"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /devrel:docs — API Docs

**IC super command** — API reference generation and versioning

## Pipeline

```
SEQUENTIAL: extract-openapi → generate-docs → version-publish
```

## Trigger

Runs recipe `recipes/devrel/docs.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/devrel:docs [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
