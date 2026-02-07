# Phase 4: CLI Integration & Reporting

**Priority:** Medium
**Status:** Pending

## Overview
Expose the analytics engine via the `vibe` CLI. Create a user-friendly command that runs the analysis and outputs a report.

## Requirements
- New CLI command: `vibe metrics`.
- Arguments: `repo` (optional, defaults to current git origin), `period` (default 30d).
- Output: Console Table (human readable) and JSON (machine readable).
- Error handling: Graceful exit if GITHUB_TOKEN is missing or repo not found.

## Architecture
- **`src/cli/index.ts`**: Entry point for CLI commands.
- **`src/cli/commands/metrics.ts`**: The metrics command implementation.
- **`src/lib/formatters.ts`**: Helpers for console output (colors, tables).

## Implementation Steps

1.  **Define Command**
    - Use `commander` (or existing framework) to define `metrics`.
    - Flags: `--owner`, `--repo`, `--days <number>`, `--json`.

2.  **Implement Handler**
    - Resolve Owner/Repo from current directory git config if not provided.
    - Check for `GITHUB_TOKEN` env var.
    - Instantiate `GitHubClient` and fetch data.
    - Pass data to `MetricsEngine`.

3.  **Output Formatting**
    - **Human Mode**: Print a summary table.
      ```
      DORA Metrics (Last 30 Days)
      ---------------------------
      Deployment Freq:  0.5/day
      Lead Time:        2 days
      ...
      ```
    - **JSON Mode**: `console.log(JSON.stringify(report))`.

4.  **Integration**
    - Register the command in the main `vibe-dev` CLI (or expose it if `vibe-analytics` is standalone).

## Success Criteria
- Running `vibe metrics` in a repo prints accurate stats.
- Running `vibe metrics --json` outputs valid JSON.
- Handles auth errors gracefully with instructions.
