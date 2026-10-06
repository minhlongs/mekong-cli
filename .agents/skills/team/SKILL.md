---
name: team
description: >-
  Orchestrate Agent Teams for parallel multi-session collaboration. Use for research, implementation, review, and debug workflows requiring independent teammates.
argument-hint: "<template|subcommand> <context> [--members|--devs|--researchers|--reviewers N] [--delegate] [--json]"
---

# /team — Agent Teams Orchestration Engine

Orchestrate Agent Teams for parallel multi-session collaboration. Use for research, implementation (cook), code review, and debug workflows requiring independent teammates.

## Execution
```bash
mekong team $ARGUMENTS
```

## Subcommands & Workflows

### 1. Operational Management
- **Dashboard**: `mekong team dashboard [--json]`
- **List Teams**: `mekong team list [--status active|idle|archived] [--json]`
- **Create Team**: `mekong team create <name> [--members N] [--roles ROLES] [--desc DESC]`
- **Assign Task**: `mekong team assign <team> <task> [--priority low|normal|high|critical] [--owner OWNER]`
- **Team Status**: `mekong team status [team] [--json]`
- **List Members**: `mekong team members <team> [--json]`
- **List Tasks**: `mekong team tasks [team] [--status pending|in_progress|completed] [--json]`
- **Delete Team**: `mekong team delete <team> [--force]`

### 2. Multi-Agent Templates
- **Research**: `mekong team research <topic> [--researchers N] [--delegate] [--json]`
  - Decomposes into market, architecture, regulatory, and ROI research tracks.
  - Produces synthesis report in `plans/reports/research-<slug>.md`.
- **Cook (Feature Build)**: `mekong team cook <goal> [--devs N] [--delegate] [--worktree/--no-worktree] [--json]`
  - Spawns parallel developers with git worktree isolation and automated test verification.
  - Produces build report in `plans/reports/cook-<slug>.md`.
- **Review (Multi-angle)**: `mekong team review <scope> [--reviewers N] [--delegate] [--json]`
  - Audits security, performance, and test coverage with severity-rated findings.
  - Produces report in `plans/reports/review-<slug>.md`.
- **Debug (Root Cause)**: `mekong team debug <issue> [--debuggers N] [--delegate] [--json]`
  - Generates competing adversarial hypotheses to isolate root causes.
  - Produces diagnostic report in `plans/reports/debug-<slug>.md`.
- **Generic Orchestrate**: `mekong team orchestrate <template> <context> [--count N] [--delegate] [--json]`
