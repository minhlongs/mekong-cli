---
name: ml-feature-register
description: "Register ML features with metadata and lineage"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /ml:feature-register — Feature Register
**IC super command** — Register ML features with metadata and lineage
## Pipeline
```
SEQUENTIAL: define-schema → validate → publish
```
## Trigger
Runs recipe `recipes/ml/feature-register.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/ml:feature-register [goal]
```
## Estimated: 2 credits, 8 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
