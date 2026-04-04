---
description: "Centralized log aggregation and search"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /obs:logs — Log Aggregation
**IC super command** — Centralized log aggregation and search
## Pipeline
```
SEQUENTIAL: configure-shipping → aggregate → index
```
## Trigger
Runs recipe `recipes/obs/logs.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/obs:logs [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
