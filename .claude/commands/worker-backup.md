---
description: "Backup project state: git stash, export configs, snapshot data"
argument-hint: [project-name]
---

# /worker-backup — Worker Operation

Backup current project state before risky operations.

1. `git stash` uncommitted changes
2. Export critical configs
3. Create timestamped backup in `.mekong/backups/`
