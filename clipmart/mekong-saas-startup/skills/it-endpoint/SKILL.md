---
name: it-endpoint
description: "Device compliance and encryption verification"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Device compliance and encryption verification"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /it:endpoint — Endpoint Compliance

**IC super command** — Device compliance and encryption verification

## Pipeline

```
SEQUENTIAL: check-compliance → verify-encryption → report
    |
OUTPUT: reports/it/endpoint/
```

## Trigger

Runs recipe `recipes/it/endpoint.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/it:endpoint [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
