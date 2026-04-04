---
name: intl-localize
description: "i18n pipeline and translation management"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /intl:localize — Localization

**IC super command** — i18n pipeline and translation management

## Pipeline

```
SEQUENTIAL: extract-strings → translate → review → deploy
```

## Trigger

Runs recipe `recipes/intl/localize.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/intl:localize [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
