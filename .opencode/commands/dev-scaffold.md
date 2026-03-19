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

<goal>$INPUT</goal>
