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

<goal>$INPUT</goal>
