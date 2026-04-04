---
name: portfolio-create
description: "Create new portfolio company with OpenClaw CTO instance. 1 command, ~5 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Create new portfolio company with OpenClaw CTO instance. 1 command, ~5 min."
argument-hint: [company-name --sector=ai --stage=idea --equity=30]
allowed-tools: Bash
---

# /portfolio:create — Create Portfolio Company

## Engine command

```bash
mekong portfolio create $ARGUMENTS
```

## Fallback

If engine not ready, run `mekong --help` to check installation, then retry.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
