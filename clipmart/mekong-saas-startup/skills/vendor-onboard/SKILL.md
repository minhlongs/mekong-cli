---
name: vendor-onboard
description: "Vendor onboarding with security questionnaire"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /vendor:onboard — Vendor Onboard

**IC super command** — Vendor onboarding with security questionnaire

## Pipeline

```
SEQUENTIAL: intake-form → security-review → approve → setup-access
```

## Trigger

Runs recipe `recipes/vendor/onboard.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/vendor:onboard [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
