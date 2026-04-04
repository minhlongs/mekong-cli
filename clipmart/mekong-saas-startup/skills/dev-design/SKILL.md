---
name: dev-design
description: "Dev design command. Delegates to worker level."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /dev:design — Developer Level

**Developer execution command** — code generation and quality.

## Pipeline

DELEGATION: dev:design → worker:*
OUTPUT: reports/dev/design/

## Execution

Load recipe: recipes/dev/design.json

Execute DAG groups in dependency order.

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
