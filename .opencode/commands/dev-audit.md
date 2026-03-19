---
description: "Dev audit command. Delegates to worker level."
argument-hint: [feature or context]
allowed-tools: Read, Write, Bash, Task
---

# /dev:audit — Developer Level

**Developer execution command** — code generation and quality.

## Pipeline

DELEGATION: dev:audit → worker:*
OUTPUT: reports/dev/audit/

## Execution

Load recipe: recipes/dev/audit.json

Execute DAG groups in dependency order.

## Goal context

<goal>$INPUT</goal>
