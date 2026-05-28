---
name: "source-command-raas-status"
description: "Check system status and metrics. 1 command, ~5-10 min."
---

# source-command-raas-status

Use this skill when the user asks to run the migrated source command `raas-status`.

## Command Template

# /status — Status Check

**Ops** — single command.

## Estimated: 1 credit, 5-10 minutes

## Workflow

[Query Metrics] → [Check Uptime] → [Review Errors] → [Display Dashboard] → [Alert if Anomalies]

## Status Output

- Service health (green/yellow/red)
- Active users/sessions
- Error rate (24h)
- Latency p50/p95/p99
- Database connection status
