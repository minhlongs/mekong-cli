---
name: terrain-position
description: "Competitive positioning analysis per terrain type"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /terrain:position — Competitive Position

**IC super command** — Competitive positioning analysis per terrain type

## Pipeline

```
SEQUENTIAL: map-competitors → assess-position → recommend-moves
```

## Trigger

Runs recipe `recipes/terrain/position.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:position [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
