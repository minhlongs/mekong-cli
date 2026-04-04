---
description: "Serve features for real-time inference"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /ml:feature-serve — Feature Serve
**IC super command** — Serve features for real-time inference
## Pipeline
```
SEQUENTIAL: load-features → cache → serve-api
```
## Trigger
Runs recipe `recipes/ml/feature-serve.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/ml:feature-serve [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
