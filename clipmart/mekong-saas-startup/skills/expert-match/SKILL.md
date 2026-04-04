---
name: expert-match
description: "AI-powered expert matching — find best expert for portfolio company need. 1 command, ~5 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "AI-powered expert matching — find best expert for portfolio company need. 1 command, ~5 min."
argument-hint: [company-slug --need="description of need"]
allowed-tools: Bash
---

# /expert:match — Expert Matching

## Engine command

```bash
mekong expert match $ARGUMENTS
```

## Fallback

If engine not ready, run `mekong --help` to check installation, then retry.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
