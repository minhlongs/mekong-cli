---
description: "Rollback to previous known-good state"
argument-hint: [commit-hash or steps]
---

# /worker-rollback — Worker Operation

Safely rollback changes.

1. Identify rollback target
2. Create backup of current state
3. `git revert` or `git reset` (prefer revert)
4. Verify build passes after rollback
