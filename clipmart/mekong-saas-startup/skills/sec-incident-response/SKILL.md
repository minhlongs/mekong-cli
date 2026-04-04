---
name: sec-incident-response
description: "Full incident response — SOC triage, incident workflow, postmortem"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Full incident response — SOC triage, incident workflow, postmortem"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:incident-response — Incident Response

**Super command** — chains multiple commands via DAG pipeline.

## Pipeline

```
SEQUENTIAL: /sec:soc → /sec:incident
    |
OUTPUT: reports/sec/incident-response/
```

## Trigger

Runs recipe `recipes/sec/incident-response.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Spawn parallel subagents via Task tool
3. Wait for all groups to complete
4. Compile into summary report

## Usage

```
/sec:incident-response [goal]
```

## Estimated: 7 credits, 20 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
