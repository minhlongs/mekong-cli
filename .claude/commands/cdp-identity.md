---
description: "Cross-device identity resolution and graph"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /cdp:identity — Identity Resolution
**IC super command** — Cross-device identity resolution and graph
## Pipeline
```
SEQUENTIAL: collect-signals → match → merge-graph
```
## Trigger
Runs recipe `recipes/cdp/identity.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/cdp:identity [goal]
```
## Estimated: 3 credits, 10 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
