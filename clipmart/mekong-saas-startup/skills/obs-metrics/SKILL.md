---
name: obs-metrics
description: "Metrics collection, dashboards, and alerting"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Metrics collection, dashboards, and alerting"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /obs:metrics — Metrics Dashboard
**IC super command** — Metrics collection, dashboards, and alerting
## Pipeline
```
SEQUENTIAL: collect-metrics → build-dashboard → configure-alerts
```
## Trigger
Runs recipe `recipes/obs/metrics.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/obs:metrics [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
