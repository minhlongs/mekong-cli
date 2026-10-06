---
name: bootstrap-auto-fast
description: Fast Autonomous Project Bootstrap — high-speed workspace scaffolding with smoke verification profile and maximum parallel concurrency.
---

# /bootstrap-auto-fast — Fast Autonomous Project Bootstrap

The `/bootstrap-auto-fast` skill executes high-speed autonomous project scaffolding. It leverages the Autonomous Parallel Bootstrap Engine pinned to the `smoke` verification profile and maximized concurrency to minimize latency while guaranteeing atomic checkpoint safety.

## CLI Invocation

```bash
// turbo
mekong bootstrap-auto-fast [GOAL] [OPTIONS]
```

### Arguments

- `[GOAL]` *(string, optional)*: High-level goal or mission description (defaults to `"Fast project bootstrap"`).

### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--template` | `-t` | `string` | `default` | Domain template preset: `default`, `vas`, `fintech`, or `agent`. |
| `--target`, `--path` | | `path` | `.` | Target directory for the workspace root. |
| `--dry-run` | | `boolean` | `false` | Preview planned tasks without disk mutations. |
| `--json` | `-j` | `boolean` | `false` | Machine-readable JSON output for CI/CD pipelines. |
| `--force` | `-f` | `boolean` | `false` | Overwrite existing files. |

## Highlights

- **Fast Execution**: Automatically selects the `smoke` verification profile to bypass heavy telemetry and slow integrity steps.
- **Parallel Acceleration**: Dispatches independent scaffolding tasks concurrently across available worker threads.
- **Safety First**: Full atomic rollback protection remains active — if an error occurs, the workspace is cleanly restored.

## Examples

```bash
# Rapid bootstrap for testing
mekong bootstrap-auto-fast "Test sandbox environment"

# Rapid bootstrap with Fintech template
mekong bootstrap-auto-fast --template fintech

# Headless CI rapid scaffold
mekong bootstrap-auto-fast --dry-run --json
```
