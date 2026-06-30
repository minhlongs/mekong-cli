---
description: "Automated escalation policy execution"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /incident:escalate — Escalation Engine
**IC super command** — Automated escalation policy execution
## Pipeline
```
SEQUENTIAL: detect-sla-breach → escalate → notify
```
## Trigger
Runs recipe `recipes/incident/escalate.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/incident:escalate [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
