---
name: sec-vuln
description: "Vulnerability management lifecycle"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Vulnerability management lifecycle"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /sec:vuln — Vulnerability Management

**IC super command** — Vulnerability management lifecycle

## Pipeline

```
SEQUENTIAL: scan → prioritize → assign-sla → track
    |
OUTPUT: reports/sec/vuln/
```

## Trigger

Runs recipe `recipes/sec/vuln.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/sec:vuln [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
