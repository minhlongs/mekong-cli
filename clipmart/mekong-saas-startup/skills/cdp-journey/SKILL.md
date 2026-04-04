---
name: cdp-journey
description: "Customer journey mapping and optimization"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Customer journey mapping and optimization"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /cdp:journey — Journey Mapping
**IC super command** — Customer journey mapping and optimization
## Pipeline
```
SEQUENTIAL: track-events → build-journey → identify-dropoffs
```
## Trigger
Runs recipe `recipes/cdp/journey.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/cdp:journey [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
