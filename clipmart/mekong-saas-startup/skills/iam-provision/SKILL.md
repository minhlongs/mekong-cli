---
name: iam-provision
description: "Automated user provisioning via SCIM/SSO"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /iam:provision — User Provisioning

**IC super command** — Automated user provisioning via SCIM/SSO

## Pipeline

```
PARALLEL: create-account + assign-roles
    |
SEQUENTIAL: verify-access
    |
OUTPUT: reports/iam/provision/
```

## Trigger

Runs recipe `recipes/iam/provision.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/iam:provision [goal]
```

## Estimated: 2 credits, 5 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
