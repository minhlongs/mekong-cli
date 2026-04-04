---
name: esg-dei
description: "Diversity metrics and reporting"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /esg:dei — DEI Metrics

**IC super command** — Diversity metrics and reporting

## Pipeline

```
SEQUENTIAL: collect-data → analyze-gaps → action-plan → report
```

## Trigger

Runs recipe `recipes/esg/dei.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/esg:dei [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
