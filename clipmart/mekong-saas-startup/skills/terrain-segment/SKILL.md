---
name: terrain-segment
description: "Classify market segments using Sun Tzu terrain types"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Classify market segments using Sun Tzu terrain types"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /terrain:segment — Market Segmentation

**IC super command** — Classify market segments using Sun Tzu terrain types

## Pipeline

```
SEQUENTIAL: identify-segments → classify-terrain → strategic-implications
```

## Trigger

Runs recipe `recipes/terrain/segment.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/terrain:segment [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
