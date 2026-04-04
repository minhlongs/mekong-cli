---
name: release-ship
description: "Changelog → version bump → test → tag → deploy production release"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /release:ship — Ship Release

**Super command** — chains 5 commands via DAG pipeline.

## Pipeline

```
[docs-changelog] ══╗
[test --all]     ══╝ (parallel)
                    ▼
             [git-tag]
                    │
                    ▼
                 [ship]
                    │
                    ▼
            [deploy-prod]
```

## Estimated: 15 credits, 25 minutes

## Execution

Load recipe: `recipes/release/ship.json`

Execute DAG groups in dependency order:
- If mode = "parallel": spawn multiple subagents simultaneously via Task tool
- If mode = "sequential": run commands one after another
- Wait for group completion before starting dependent groups

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
