---
description: "OpenTelemetry distributed tracing setup and analysis"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /obs:trace — Distributed Tracing
**IC super command** — OpenTelemetry distributed tracing setup and analysis
## Pipeline
```
SEQUENTIAL: configure-otel → collect-traces → analyze
```
## Trigger
Runs recipe `recipes/obs/trace.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/obs:trace [goal]
```
## Estimated: 3 credits, 10 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.
