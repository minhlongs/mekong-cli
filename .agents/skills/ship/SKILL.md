---
name: ship
description: >-
  Ship code to production — lint, test, commit, push, deploy. One workflow to rule them all.
---

# 🚀 Ship Command

One workflow to test, commit, push, and deploy. Eliminates forgotten linter errors, failing tests, unpushed branches, and inconsistent commit messages.

## Execution

```bash
# Full automated ship (lint -> test -> stage -> commit -> push)
mekong ship "add OAuth2 login flow"

# Dry-run validation & commit message synthesis
mekong ship --dry-run

# Run preflight inspection only
mekong ship --preflight-only

# Ship without pushing to remote (local commit only)
mekong ship "refactor user repository" --no-push

# Machine-readable JSON output for agent swarms and CI/CD
mekong ship --json
```

## Flags & Options

| Flag | Default | Description |
|------|---------|-------------|
| `[message]` | auto-synthesized | Optional commit description (e.g. 'fix payment webhook timeout') |
| `--lint / --no-lint` | true | Run project linters before staging |
| `--test / --no-test` | true | Run automated test suite before staging |
| `--push / --no-push` | true | Push committed branch to remote upstream |
| `--preflight-only` | false | Execute repository topology pre-flight check only |
| `--dry-run` | false | Simulate validation and commit synthesis without git mutations |
| `--json / -j` | false | Machine-readable JSON report output |
| `--verbose / -v` | false | Print detailed test and linter output diagnostics |

## Steps

```
0. PREFLIGHT  → Verify git root, branch, upstream remote, and dirty files
1. VALIDATE   → Run ruff / pytest / npm lint / npm test
2. STAGE      → Atomic git add -A
3. COMMIT     → Conventional commit synthesis (feat:, fix:, docs:, etc.)
4. PUSH       → Push current branch to origin
```

## CLI Invocation

```bash
// turbo
mekong ship $ARGUMENTS
```
