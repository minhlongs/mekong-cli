---
name: intl-compliance
description: "Country-specific regulatory requirements"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /intl:compliance — Country Compliance

**IC super command** — Country-specific regulatory requirements

## Pipeline

```
SEQUENTIAL: identify-regs → gap-analysis → remediation-plan
```

## Trigger

Runs recipe `recipes/intl/compliance.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/intl:compliance [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
