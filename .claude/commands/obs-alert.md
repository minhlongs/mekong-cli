---
description: "Alert rule creation, routing, and silencing"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /obs:alert — Alert Management
**IC super command** — Alert rule creation, routing, and silencing
## Pipeline
```
SEQUENTIAL: list-rules → evaluate → route
```
## Trigger
Runs recipe `recipes/obs/alert.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/obs:alert [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
