---
name: dev-scaffold
description: "Dev scaffold command. Delegates to worker level."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Dev scaffold command. Delegates to worker level."
argument-hint: [feature or context]
allowed-tools: Read, Write, Bash, Task
---

# /dev:scaffold — Developer Level

**Developer execution command** — code generation and quality.

## Pipeline

DELEGATION: dev:scaffold → worker:*
OUTPUT: reports/dev/scaffold/

## Execution

Load recipe: recipes/dev/scaffold.json

Execute DAG groups in dependency order.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
