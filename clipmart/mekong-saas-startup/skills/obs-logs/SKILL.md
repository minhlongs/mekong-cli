---
name: obs-logs
description: "Centralized log aggregation and search"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
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

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
