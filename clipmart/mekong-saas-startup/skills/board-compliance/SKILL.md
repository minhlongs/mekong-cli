---
name: board-compliance
description: "Committee composition tracking vs exchange rules"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /board:compliance — Board Compliance

**IC super command** — Committee composition tracking vs exchange rules

## Pipeline

```
SEQUENTIAL: extract-composition → check-requirements → gap-report
OUTPUT: reports/governance/board-compliance/
```

## Trigger

Runs recipe `recipes/board/compliance.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/board:compliance [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
