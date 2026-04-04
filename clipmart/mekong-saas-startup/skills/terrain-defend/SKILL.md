---
name: terrain-defend
description: "Maintain and strengthen defensive market position"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /terrain:defend — Defensive Position

**IC super command** — Maintain and strengthen defensive market position

## Pipeline

```
SEQUENTIAL: audit-moat → identify-threats → reinforce-defenses
```

## Trigger

Runs recipe `recipes/terrain/defend.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:defend [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
