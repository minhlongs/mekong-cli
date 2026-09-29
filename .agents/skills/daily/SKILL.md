---
name: daily
description: >-
  Daily status report — revenue, pending approvals, system health, today's focus.
---

# /daily — Autonomous Daily Executive Briefing & Standup

Quick executive standup summarizing git activity, uncommitted files, open codebase technical debt (TODO/FIXME), mesh queue depth, and prioritized daily focus recommendations.

## Execution

```bash
# Standard daily briefing (past 24h activity + technical debt)
mekong daily

# Extended lookback window (e.g. past 7 days)
mekong daily --since "7 days ago"

# Quick standup omitting debt markers
mekong daily --no-todos

# Machine-readable JSON output for automated agent standups
mekong daily --json

# Export briefing summary to markdown
mekong daily --export .mekong/daily/today.md
```

## Options & Flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--since` | `-s` | `24 hours ago` | Time window for git commit velocity |
| `--todos / --no-todos` | | `true` | Scan codebase for open action markers (TODO, FIXME, HACK, XXX) |
| `--export` | `-e` | `none` | Export daily briefing report to markdown file |
| `--json` | `-j` | `false` | Machine-readable JSON report output |

## Report Sections

```
1. EXECUTIVE STANDUP  → Repository name, current branch, commits count, uncommitted changes
2. RECENT ACTIVITY    → SHA, author, age, and commit message for recent commits
3. CODEBASE DEBT      → File, line number, and details for open TODOs and FIXMEs
4. TODAY'S FOCUS      → 3-5 prioritized recommendations synthesized from project signals
```

## CLI Invocation

```bash
// turbo
mekong daily $ARGUMENTS
```
