---
name: bootstrap-auto
description: Autonomous Project Bootstrap — sequential and standard workspace scaffolding with dependency DAG execution and atomic rollback.
---

# /bootstrap-auto — Autonomous Project Bootstrap

The `/bootstrap-auto` skill runs autonomous project bootstrap and workspace scaffolding. It delegates to the Autonomous Bootstrap Engine with standard DAG task orchestration, atomic failure checkpointing, and automatic rollback.

## CLI Invocation

```bash
// turbo
mekong bootstrap-auto [GOAL] [OPTIONS]
```

### Arguments

- `[GOAL]` *(string, optional)*: High-level goal or mission description (defaults to `"Autonomous project bootstrap"`).

### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--profile` | `-p` | `string` | `standard` | Scaffolding profile: `smoke`, `standard`, or `full`. |
| `--template` | `-t` | `string` | `default` | Domain template: `default`, `vas`, `fintech`, or `agent`. |
| `--target`, `--path` | | `path` | `.` | Target directory for the workspace root. |
| `--dry-run` | | `boolean` | `false` | Preview planned tasks without disk mutations. |
| `--json` | `-j` | `boolean` | `false` | Machine-readable JSON output for CI/CD pipelines. |
| `--force` | `-f` | `boolean` | `false` | Overwrite existing files. |

## Relationship to Parallel Bootstrap

- `/bootstrap-auto`: Sequential or standard baseline autonomous bootstrap.
- `/bootstrap-auto-parallel`: High-throughput concurrent execution using multi-worker `ThreadPoolExecutor`.
- `/bootstrap-auto-fast`: Rapid bootstrap pinned to `smoke` profile for maximum speed.

## Examples

```bash
# Standard project bootstrap
mekong bootstrap-auto "Initialize new client workspace"

# Bootstrap VAS template with JSON output
mekong bootstrap-auto --template vas --json

# Dry-run preview
mekong bootstrap-auto --dry-run
```
