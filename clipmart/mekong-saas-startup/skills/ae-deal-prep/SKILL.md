---
name: ae-deal-prep
description: "Deal prep — company research + competitive positioning, then proposal talking points. 3 commands, ~12 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Deal prep — company research + competitive positioning, then proposal talking points. 3 commands, ~12 min."
argument-hint: [company-name-or-deal-description]
allowed-tools: Read, Write, Bash, Task
---

# /ae:deal-prep — Deal Prep

**IC super command** — chains 3 commands via DAG pipeline.

## Pipeline

```
PARALLEL: /customer-research --deep + /competitor --vs
    |
SEQUENTIAL: /proposal
    |
OUTPUT: reports/ae/deal-prep/
        company-research.md
        competitive-positioning.md
        proposal-talking-points.md
        DEAL-PREP-SUMMARY.md
```

## Trigger

Runs recipe `recipes/ae/ae-deal-prep.json` through DAGScheduler.

## Execution

1. Read recipe DAG definition
2. Spawn research + competitor subagents simultaneously via Task tool (mode: parallel)
3. Wait for both to complete
4. Run /proposal sequentially using research outputs as context
5. Compile into DEAL-PREP-SUMMARY.md battle card

## Usage

```
/ae:deal-prep [company-name-or-deal-description]
```

## Estimated: 8 credits, 12 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
