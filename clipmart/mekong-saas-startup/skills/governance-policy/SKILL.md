---
name: governance-policy
description: "Code of ethics, whistleblower, corporate guidelines"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Code of ethics, whistleblower, corporate guidelines"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /governance:policy — Corporate Policy

**IC super command** — Code of ethics, whistleblower, corporate guidelines

## Pipeline

```
SEQUENTIAL: draft-policies → legal-review → publish-distribute
OUTPUT: reports/governance/policy/
```

## Trigger

Runs recipe `recipes/governance/policy.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/governance:policy [goal]
```

## Estimated: 3 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
