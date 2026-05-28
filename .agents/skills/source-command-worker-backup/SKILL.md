---
name: "source-command-worker-backup"
description: "Backup project state: git stash, export configs, snapshot data"
---

# source-command-worker-backup

Use this skill when the user asks to run the migrated source command `worker-backup`.

## Command Template

# /worker-backup — Worker Operation

Backup current project state before risky operations.

1. `git stash` uncommitted changes
2. Export critical configs
3. Create timestamped backup in `.mekong/backups/`
