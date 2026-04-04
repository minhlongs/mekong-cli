---
name: sec-incident
description: "Security incident response workflow"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Security incident response workflow"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:incident — Incident Response

**IC super command** — Security incident response workflow

## Pipeline

```
PARALLEL: detect + triage
    |
SEQUENTIAL: contain → remediate → postmortem
    |
OUTPUT: reports/sec/incident/
```

## Trigger

Runs recipe `recipes/sec/incident.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:incident [goal]
```

## Estimated: 5 credits, 15 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
