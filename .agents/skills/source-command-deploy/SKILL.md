---
name: "source-command-deploy"
description: "Deployment execution — pre-flight checks, deploy, smoke test, rollback plan. 4 steps, ~15 min."
---

# source-command-deploy

Use this skill when the user asks to run the migrated source command `deploy`.

## Command Template

# /devops:deploy — Deploy

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── pre-flight              → checklist.md
  ├── deploy-execute          → deploy-log.md
  ├── smoke-test              → test-results.md
  └── rollback-plan           → rollback.md
```

## Output directory: reports/devops/deploy/
