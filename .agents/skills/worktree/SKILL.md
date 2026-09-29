---
name: worktree
description: >-
  Create, inspect, and clean isolated git worktrees. Use for feature isolation, worktree health audits, stale cleanup, and monorepo or submodule workflows.
---

# /worktree — Isolated Git Worktree Mesh

Create, inspect, and clean isolated git worktrees. Eliminates branch checkout churn, stashing, and workspace conflicts for parallel agent swarms.

## Subcommands

```
mekong worktree create <feature>   # Create isolated worktree branching from base
mekong worktree list               # List all active worktree workspaces
mekong worktree status [target]    # Inspect dirty state and commit divergence
mekong worktree remove <target>    # Remove worktree workspace and tracking
mekong worktree prune              # Clean stale worktree administrative records
mekong worktree info               # Inspect repo topology and worktree paths
```

## Options & Flags

### `create`
| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--prefix` | `-p` | auto | Branch prefix (`feat`, `fix`, `refactor`, `docs`, `test`, `perf`, `chore`) |
| `--base` | `-b` | auto | Base branch to branch from (`main` or `master`) |
| `--no-prefix` | | false | Do not prepend prefix; use feature string directly |
| `--root` | `-r` | sibling | Custom directory to host worktrees |
| `--dry-run` | | false | Calculate branch name and path without mutating git |
| `--json` | `-j` | false | Machine-readable JSON output |

### `list`, `status`, `remove`, `prune`, `info`
| Subcommand | Flag | Description |
|------------|------|-------------|
| `list` | `--json` | Output JSON array of worktrees |
| `status` | `[target]`, `--json` | Inspect divergence and uncommitted files |
| `remove` | `--force`, `-f`, `--json` | Force removal even if dirty/untracked files exist |
| `prune` | `--dry-run`, `--json` | Prune stale worktrees |
| `info` | `--json` | Output repository topology and paths |

## Examples

```bash
# Auto-detect prefix 'feat' and slugify branch
mekong worktree create "user authentication"

# Auto-detect prefix 'fix' for bug fixes
mekong worktree create "fix checkout timeout bug"

# Inspect status of current or specified worktree
mekong worktree status

# List all active worktrees
mekong worktree list --json

# Remove worktree after merge or completion
mekong worktree remove feat-user-authentication --force
```

## Execution
```bash
// turbo
mekong worktree $ARGUMENTS
```
