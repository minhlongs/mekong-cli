---
name: dealflow-term-sheet
description: "Generate term sheet draft from deal data and studio defaults. 1 command, ~8 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Generate term sheet draft from deal data and studio defaults. 1 command, ~8 min."
argument-hint: [deal-id]
allowed-tools: Bash
---

# /dealflow:term-sheet — Generate Term Sheet

## Engine command

```bash
mekong dealflow advance --to-stage term_sheet $ARGUMENTS
```

## Fallback

If engine not ready, run `mekong --help` to check installation, then retry.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
