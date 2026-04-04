---
name: incident-escalate
description: "Automated escalation policy execution"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /incident:escalate — Escalation Engine
**IC super command** — Automated escalation policy execution
## Pipeline
```
SEQUENTIAL: detect-sla-breach → escalate → notify
```
## Trigger
Runs recipe `recipes/incident/escalate.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/incident:escalate [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
