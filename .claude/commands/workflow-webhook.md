---
description: "Incoming and outgoing webhook management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /workflow:webhook — Webhook Management
**IC super command** — Incoming and outgoing webhook management
## Pipeline
```
SEQUENTIAL: register → verify → monitor
```
## Trigger
Runs recipe `recipes/workflow/webhook.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/workflow:webhook [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
