---
name: worker-build
description: "Worker compile atomic command. 1 credit."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Worker compile atomic command. 1 credit."
argument-hint: [target or args]
allowed-tools: Read, Write, Bash
---

# /worker:build — Atomic Compile & Bundle

**Atomic command** — executes directly, no delegation. Leaf node in ROIaaS hierarchy.

## Execution

Direct execution — no recipe loading. Single atomic operation.

1. Parse arguments from goal context
2. Execute the compile/bundle operation directly
3. Report results

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
