---
name: cdp-profile
description: "Unified customer profile across all touchpoints"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Unified customer profile across all touchpoints"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /cdp:profile — Customer 360
**IC super command** — Unified customer profile across all touchpoints
## Pipeline
```
SEQUENTIAL: merge-sources → resolve-identity → build-profile
```
## Trigger
Runs recipe `recipes/cdp/profile.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/cdp:profile [goal]
```
## Estimated: 3 credits, 10 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
