---
name: dev-debug
description: "Dev debug command. Delegates to worker level."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Dev debug command. Delegates to worker level."
argument-hint: [feature or context]
allowed-tools: Read, Write, Bash, Task
---

# /dev:debug — Developer Level

**Developer execution command** — code generation and quality.

## Pipeline

DELEGATION: dev:debug → worker:*
OUTPUT: reports/dev/debug/

## Execution

Load recipe: recipes/dev/debug.json

Execute DAG groups in dependency order.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
