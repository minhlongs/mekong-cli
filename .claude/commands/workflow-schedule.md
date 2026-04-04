---
description: "Cron and scheduled job management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /workflow:schedule — Scheduled Jobs
**IC super command** — Cron and scheduled job management
## Pipeline
```
SEQUENTIAL: define-schedule → register-job → monitor
```
## Trigger
Runs recipe `recipes/workflow/schedule.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/workflow:schedule [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
