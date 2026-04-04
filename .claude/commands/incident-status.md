---
description: "Public and internal status page management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /incident:status — Status Page
**IC super command** — Public and internal status page management
## Pipeline
```
SEQUENTIAL: check-services → update-status → notify-subscribers
```
## Trigger
Runs recipe `recipes/incident/status.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/incident:status [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
