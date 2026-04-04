---
description: "Event-driven workflow trigger management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /workflow:trigger — Event Triggers
**IC super command** — Event-driven workflow trigger management
## Pipeline
```
SEQUENTIAL: define-events → create-triggers → test
```
## Trigger
Runs recipe `recipes/workflow/trigger.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/workflow:trigger [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
