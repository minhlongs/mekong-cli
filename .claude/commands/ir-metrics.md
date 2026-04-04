---
description: "Automated SaaS metrics for investors — ARR, NRR, Rule of 40"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /ir:metrics — Investor Metrics

**IC super command** — Automated SaaS metrics for investors — ARR, NRR, Rule of 40

## Pipeline

```
PARALLEL: pull-revenue-data + pull-retention-data
    |
SEQUENTIAL: calculate-metrics → format-deck
OUTPUT: reports/governance/ir-metrics/
```

## Trigger

Runs recipe `recipes/ir/metrics.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/ir:metrics [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
