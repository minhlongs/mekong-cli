---
name: sdr-prospect
description: "Prospecting sprint — ICP match + lead research in parallel. 2 commands, ~10 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /sdr:prospect — Prospecting Sprint

**IC super command** — chains 2 commands via DAG pipeline.

## Pipeline

```
PARALLEL: /customer-research --icp + /leadgen
    |
OUTPUT: reports/sdr/prospect/
        icp-matches.md
        lead-list.md
        PROSPECT-SUMMARY.md
```

## Trigger

Runs recipe `recipes/sdr/sdr-prospect.json` through DAGScheduler.

## Execution

1. Read recipe DAG definition
2. Spawn both subagents simultaneously via Task tool (mode: parallel)
3. Wait for both to complete
4. Compile outputs into PROSPECT-SUMMARY.md with prioritized contact list

## Usage

```
/sdr:prospect [target-market-or-icp-description]
```

## Estimated: 5 credits, 10 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
