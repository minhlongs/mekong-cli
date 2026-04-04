---
name: ml-feature-backfill
description: "Backfill historical features for training"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Backfill historical features for training"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---
# /ml:feature-backfill — Feature Backfill
**IC super command** — Backfill historical features for training
## Pipeline
```
SEQUENTIAL: define-window → compute → store
```
## Trigger
Runs recipe `recipes/ml/feature-backfill.json` through DAGScheduler.
## Execution
1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report
## Usage
```
/ml:feature-backfill [goal]
```
## Estimated: 3 credits, 12 minutes
## Goal context
<goal>$ARGUMENTS</goal>
Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
