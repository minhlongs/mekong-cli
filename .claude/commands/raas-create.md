---
description: "Create full RaaS SaaS product — scaffold, build features, deploy. 5 commands, ~45 min."
argument-hint: [project-name]
allowed-tools: Read, Write, Bash, Task
---

# /raas:create — Full RaaS Product Pipeline

**Super command** — chains 5 commands via DAG pipeline.

## Pipeline

```
[scaffold] -- SEQUENTIAL
  raas-scaffold project
         |
         v
[features] -- SEQUENTIAL
  cook "Landing page"
  cook "Dashboard + auth"
  cook "Billing integration"
         |
         v
[deploy] -- SEQUENTIAL
  test --all
  deploy --to cloudflare
```

## Estimated: 30 credits, 45 minutes

## Execution

Load recipe: `recipes/raas/create.json`

Execute DAG groups in dependency order. Each sub-command MUST run via `mekong` CLI engine.

## CRITICAL

This command creates ACTUAL CODE in apps/{project}/. Not reports.
Output is a deployable Next.js SaaS application, not analysis documents.

## Goal context

<goal>$ARGUMENTS</goal>
