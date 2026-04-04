---
name: ml-governance
description: "Audit trail, EU AI Act compliance, model cards"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /ml:governance — AI Governance

**IC super command** — Audit trail, EU AI Act compliance, model cards

## Pipeline

```
SEQUENTIAL: generate-model-card → audit-trail → compliance-check
```

## Trigger

Runs recipe `recipes/ml/governance.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:governance [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
