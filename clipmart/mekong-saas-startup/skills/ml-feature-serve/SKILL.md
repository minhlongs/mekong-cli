---
name: ml-feature-serve
description: "Serve features for real-time inference"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

# /ml:feature-serve — Feature Serve
**IC super command** — Serve features for real-time inference
## Pipeline
```
SEQUENTIAL: load-features → cache → serve-api
```
## Trigger
Runs recipe `recipes/ml/feature-serve.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/ml:feature-serve [goal]
```
## Estimated: 2 credits, 5 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
