---
description: "Rate limit rule configuration per tier"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /gateway:rate-limit — Rate Limiting
**IC super command** — Rate limit rule configuration per tier
## Pipeline
```
SEQUENTIAL: define-tiers → set-limits → monitor
```
## Trigger
Runs recipe `recipes/gateway/rate-limit.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/gateway:rate-limit [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
