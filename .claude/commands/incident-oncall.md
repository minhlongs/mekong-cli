---
description: "On-call rotation management and scheduling"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /incident:oncall — On-Call Rotation
**IC super command** — On-call rotation management and scheduling
## Pipeline
```
SEQUENTIAL: define-rotation → assign → notify
```
## Trigger
Runs recipe `recipes/incident/oncall.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/incident:oncall [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
