---
name: ml-monitor
description: "Drift detection, latency, hallucination rates, cost per inference"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /ml:monitor — Model Monitor

**IC super command** — Drift detection, latency, hallucination rates, cost per inference

## Pipeline

```
PARALLEL: drift-check + latency-check + hallucination-check + cost-check\n    
```

## Trigger

Runs recipe `recipes/ml/monitor.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ml:monitor [goal]
```

## Estimated: \nSEQUENTIAL: alert-report credits, 2 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
