---
name: revops-attribution
description: "Multi-touch attribution and channel ROI"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Multi-touch attribution and channel ROI"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /revops:attribution — Attribution Analysis

**IC super command** — Multi-touch attribution and channel ROI

## Pipeline

```
SEQUENTIAL: collect-touchpoints → model-attribution → calculate-roi
```

## Trigger

Runs recipe `recipes/revops/attribution.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/revops:attribution [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
