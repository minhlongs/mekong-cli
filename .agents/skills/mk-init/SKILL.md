---
name: mk-init
description: >-
  Initialize or update AgentKit in current directory via Mekong CLI (manages .agentkit/ownership.json, drift detection, and kit tracking).
---

# /mk:init — Mekong CLI bridge to AgentKit `ak init` v2.4.0

Same engine as `ak init`, invoked via the Mekong CLI wrapper. **Idempotent init-or-update**: onboards an existing directory into AgentKit management or refreshes an existing manifest.

## What it does

- Creates or atomically updates `<dir>/.agentkit/ownership.json` — the ownership manifest.
- Tracks all AK-managed files under project `.agentkit/`, `kits/`, and `.claude/` subtrees.
- For existing manifests: re-runs drift detection and updates tracked entries.
- For fresh directories: use **`ak new <name>`** to scaffold a new project (separate command — this bridge does not create fresh scaffolds).

## Drift detection

If AK-owned files have been modified by the user since the last init, the command reports drift and **exits with code 6** unless `--force` is passed. `--force` proceeds even when files have drifted.

## Flags

| Flag | Behavior |
|---|---|
| `--dry-run` | Preview what would happen without writing any files |
| `--force` | Proceed even when AK-owned files have been user-modified (drift) |
| `--project-id <id>` | Override the project name stored in the manifest (default: directory basename) |
| `--json` | Emit machine-readable JSON envelope (`{schema_version, kind, data}`), implies `--no-interactive` |
| `--no-interactive` | Disable interactive prompts (CI-safe, plain output) |
| `--no-backup` | Skip the pre-mutation backup snapshot (power users only — data loss risk) |
| `--quiet` / `-q` | Suppress non-error output on stderr |
| `--verbose` / `-V` | Extra diagnostic output on stderr (loses to `--quiet`) |
| `--yes` / `-y` | Assume yes for all prompts |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | runtime error / directory does not exist or I/O error |
| `2` | invalid flags |
| `3` | user-cancel (SIGINT, prompt-cancel) |
| `6` | drifted files detected without `--force` |

## Output modes

- `pretty` — default on TTY (colors, ASCII markers)
- `plain` — auto when stdout is piped or `--no-interactive`
- `json` — `--json` flag (single-object envelope `{schema_version, kind, data}`, NDJSON-safe)

## Execution

```bash
$HOME/bin/ak init "$@"
```

## Bilingual notes

💡 *Khởi tạo hoặc cập nhật cấu hình AgentKit cho thư mục hiện tại mà không ghi đè các file tùy biến.*

💡 *Initialize or update AgentKit configuration in the current directory without overwriting custom modifications.*

Confirm to the caller that `/mk:init` routes through AgentKit `ak init` via the Mekong CLI, initializes or updates the project (creating `.agentkit/ownership.json`), tracks `.agentkit/`, `kits/`, and `.claude/`, and exits with code `6` if files have drifted and `--force` was not provided.

## CLI Invocation

```bash
// turbo
mekong mk init $ARGUMENTS
```
