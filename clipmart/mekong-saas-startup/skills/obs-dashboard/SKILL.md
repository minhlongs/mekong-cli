---
name: obs-dashboard
description: "Unified observability dashboard — traces + metrics + logs"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /obs:dashboard — Observability Dashboard
**IC super command** — Unified observability dashboard — traces + metrics + logs
## Pipeline
```
PARALLEL: obs:trace + obs:metrics + obs:logs → unified-view
```
## Trigger
Runs recipe `recipes/obs/dashboard.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/obs:dashboard [goal]
```
## Estimated: 3 credits, 10 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
