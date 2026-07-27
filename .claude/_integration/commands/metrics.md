---
description: "AARRR Metrics Dashboard — acquisition, activation, retention, revenue, referral"
argument-hint: "[--json]"
---

# /metrics — AARRR Dashboard

## Usage
```
/metrics              # Show terminal dashboard
/metrics --json       # Raw JSON output
```

## Metrics

| Stage | What | Source |
|-------|------|--------|
| Acquisition | Installs, unique users | `~/.mekong/trial.json` |
| Activation | Trials started, configured | Trial data |
| Retention | D7, D30, active users | Trial data |
| Revenue | MRR, subscribers, ARPU | Stripe (future) |
| Referral | Invites, conversion | Invite data |
| North Star | Workflows per day | Credit usage |

## Score: 0-100
- 🟢 70+ — Healthy
- 🟡 40-69 — Needs work
- 🔴 < 40 — Critical

## Implementation
Runs: `node scripts/metrics.cjs` or `node scripts/metrics.cjs --json`
