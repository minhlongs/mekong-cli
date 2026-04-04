---
name: dev-review
description: "Dev review command. Delegates to worker level."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Dev review command. Delegates to worker level."
argument-hint: [feature or context]
allowed-tools: Read, Write, Bash, Task
---

# /dev:review — Developer Level

**Developer execution command** — code generation and quality.

## Pipeline

DELEGATION: dev:review → worker:*
OUTPUT: reports/dev/review/

## Execution

Load recipe: recipes/dev/review.json

Execute DAG groups in dependency order.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
