---
name: pm-feature-flag
description: "Progressive rollout and kill switches"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /pm:feature-flag — Feature Flags

**IC super command** — Progressive rollout and kill switches

## Pipeline

```
SEQUENTIAL: create-flag → configure-rollout → monitor-metrics
```

## Trigger

Runs recipe `recipes/pm/feature-flag.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/pm:feature-flag [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
