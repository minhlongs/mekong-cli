---
name: revops-handoff
description: "SLA-governed lead and opportunity handoff"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "SLA-governed lead and opportunity handoff"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /revops:handoff — Lead Handoff

**IC super command** — SLA-governed lead and opportunity handoff

## Pipeline

```
SEQUENTIAL: qualify-lead → match-ae → handoff → track-sla
```

## Trigger

Runs recipe `recipes/revops/handoff.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:handoff [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
