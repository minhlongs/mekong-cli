---
description: "API gateway route configuration and management"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /gateway:route — Route Config
**IC super command** — API gateway route configuration and management
## Pipeline
```
SEQUENTIAL: scan-openapi → generate-routes → deploy
```
## Trigger
Runs recipe `recipes/gateway/route.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/gateway:route [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
