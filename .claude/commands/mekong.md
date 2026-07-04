---
description: "Run any mekong-cli command — passthrough wrapper for the full RaaS Agency OS CLI"
argument-hint: "[mekong subcommand] [options]"
allowed-tools: Bash
---

# /mekong — Mekong CLI Passthrough

Invoke the **mekong-cli** binary directly. Every argument you pass after `/mekong` is forwarded as-is to the `mekong` command (via `poetry run mekong`).

## Usage

```bash
/mekong <subcommand> [args...]
```

## Examples

```bash
/mekong --help                          # Show all available commands
/mekong cook "Add JWT auth to /api/users"   # Cook a feature
/mekong plan "Refactor payment module"      # Plan only
/mekong goal "Launch VN-Hub phase 9"        # Run a persistent goal
/mekong status                              # License / quota status
/mekong agi status                           # AGI daemon health
/mekong dash                                 # Open action menu
```

## Notes

- The `mekong` binary is resolved via `poetry run mekong` from the project root.
- Optional components (`mem0ai`, `qdrant-client`) produce non-fatal warnings on startup; they do not block execution.
- For long-running or autonomous commands (`goal`, `cook-auto`, `cook-auto-parallel`), use the `--profile` flag to control verification depth.
- Command reference: run `mekong --help` or `mekong <subcommand> --help`.
