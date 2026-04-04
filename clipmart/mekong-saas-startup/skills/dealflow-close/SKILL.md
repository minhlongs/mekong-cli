---
name: dealflow-close
description: "Close deal — finalize investment, onboard company to portfolio. 1 command, ~5 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Close deal — finalize investment, onboard company to portfolio. 1 command, ~5 min."
argument-hint: [deal-id]
allowed-tools: Bash
---

# /dealflow:close — Close Deal & Onboard

## Engine command

```bash
mekong dealflow advance --to-stage closed $ARGUMENTS
```

## Fallback

If engine not ready, run `mekong --help` to check installation, then retry.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
