---
name: cdp-segment
description: "Dynamic customer segmentation by behavior and value"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /cdp:segment — Customer Segmentation
**IC super command** — Dynamic customer segmentation by behavior and value
## Pipeline
```
SEQUENTIAL: define-criteria → compute-segments → activate
```
## Trigger
Runs recipe `recipes/cdp/segment.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/cdp:segment [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
