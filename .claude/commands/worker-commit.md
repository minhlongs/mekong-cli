---
description: "Stage, validate, and commit changes with conventional message"
argument-hint: [scope] [message]
---

# /worker-commit — Worker Operation

Create a clean commit.

1. `git diff` review changes
2. Stage relevant files (never `git add -A`)
3. Conventional commit: feat/fix/refactor/docs
4. Verify no secrets committed
