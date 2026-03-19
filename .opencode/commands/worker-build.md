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

<goal>$INPUT</goal>
