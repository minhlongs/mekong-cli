---
description: "Automated user provisioning via SCIM/SSO"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
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
