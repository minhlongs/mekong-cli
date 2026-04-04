---
name: vendor-contract
description: "Centralized repository and SLA tracking"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /vendor:contract — Vendor Contracts

**IC super command** — Centralized repository and SLA tracking

## Pipeline

```
SEQUENTIAL: import-contract → extract-terms → track-slas
```

## Trigger

Runs recipe `recipes/vendor/contract.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:contract [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
