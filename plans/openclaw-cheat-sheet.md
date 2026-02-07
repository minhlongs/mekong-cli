# OpenClaw Hybrid Commander: Cheat Sheet

> **Date:** 2026-02-07
> **Role:** Supreme Commander Manual

## 1. Quick Checks

| Command         | Description                     |
| :-------------- | :------------------------------ |
| `!status`       | Check if Bridge & T1 are alive. |
| `!ping`         | Test latency to Local Machine.  |
| `!echo "Hello"` | Test simple shell execution.    |

## 2. GitHub Operations (Skill: `github-cli`)

_Use natural language via `/cmd` or the `gh` tool directly._

- **List Repos:**
  `/cmd mekong List my top 5 repositories`
- **Create Issue:**
  `/cmd mekong Create an issue in "agencyos-landing" about "Fix mobile menu"`
- **Check PRs:**
  `/cmd mekong List open PRs in "sophia-ai-factory"`

## 3. Vercel Operations (Skill: `vercel-cli`)

- **Deploy Production:**
  `/cmd mekong Deploy agencyos-landing to production`
- **Check Deployments:**
  `/cmd mekong List recent deployments for sophia`

## 4. Advanced "Giao Việc" (Delegation)

You can chain commands or ask for complex reasoning:

- **Audit & Fix:**

  > "/cmd mekong Audit apps/AgencyOS for any type errors and fix them using senior-backend skill."

- **Market Research (VPN):**
  > "/cmd 84tea Rotate VPN and scrape competitor prices for 'Red Tea'."

## 5. Troubleshooting

If T1 doesn't respond:

1.  Check `apps/openclaw-worker/watcher.log` (on Mac).
2.  Restart Bridge: `cd apps/openclaw-worker && ./openclaw-service.sh`.
