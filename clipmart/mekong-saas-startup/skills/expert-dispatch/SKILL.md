---
name: expert-dispatch
description: "Dispatch expert to portfolio company — create engagement record. 1 command, ~3 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Dispatch expert to portfolio company — create engagement record. 1 command, ~3 min."
argument-hint: [expert-id --company=slug --scope="engagement scope" --type=advisory]
allowed-tools: Bash
---

# /expert:dispatch — Dispatch Expert

## Engine command

```bash
mekong expert dispatch $ARGUMENTS
```

## Fallback

If engine not ready, run `mekong --help` to check installation, then retry.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
