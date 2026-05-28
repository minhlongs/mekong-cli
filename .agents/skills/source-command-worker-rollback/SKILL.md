---
name: "source-command-worker-rollback"
description: "Rollback to previous known-good state"
---

# source-command-worker-rollback

Use this skill when the user asks to run the migrated source command `worker-rollback`.

## Command Template

# /worker-rollback — Worker Operation

Safely rollback changes.

1. Identify rollback target
2. Create backup of current state
3. `git revert` or `git reset` (prefer revert)
4. Verify build passes after rollback
