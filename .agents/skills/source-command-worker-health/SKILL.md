---
name: "source-command-worker-health"
description: "Health check: build status, test results, dependency audit"
---

# source-command-worker-health

Use this skill when the user asks to run the migrated source command `worker-health`.

## Command Template

# /worker-health — Worker Operation

Run comprehensive health check.

1. `npm run build` — check for errors
2. `npm test` — check pass rate
3. `npm audit` — security check
4. Report: Build/Tests/Security status
