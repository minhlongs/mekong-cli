---
name: treasury-invest
description: "Short-term investment policy management"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /treasury:invest — Investment Policy

**IC super command** — Short-term investment policy management

## Pipeline

```
SEQUENTIAL: review-policy → assess-options → allocate
```

## Trigger

Runs recipe `recipes/treasury/invest.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/treasury:invest [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
