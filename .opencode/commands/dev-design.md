---
description: "Dev design command. Delegates to worker level."
argument-hint: [feature or context]
allowed-tools: Read, Write, Bash, Task
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

<goal>$INPUT</goal>
