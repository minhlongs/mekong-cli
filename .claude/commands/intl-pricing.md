---
description: "Geo-specific pricing and PPP adjustments"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /intl:pricing — Geo Pricing

**IC super command** — Geo-specific pricing and PPP adjustments

## Pipeline

```
SEQUENTIAL: benchmark-market → calculate-ppp → set-tiers
```

## Trigger

Runs recipe `recipes/intl/pricing.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/intl:pricing [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
