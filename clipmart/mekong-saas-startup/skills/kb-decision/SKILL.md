---
name: kb-decision
description: "Log and track important business and technical decisions"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /kb:decision — Decision Log
**IC super command** — Log and track important business and technical decisions
## Pipeline
```
SEQUENTIAL: log-decision → assign-owner → set-review-date
```
## Trigger
Runs recipe `recipes/kb/decision.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/kb:decision [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
