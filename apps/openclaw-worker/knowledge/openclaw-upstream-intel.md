# 🧬 OpenClaw Upstream — DNA Core of Tôm Hùm CTO

> Source: github.com/openclaw/openclaw
> Relationship: PARENT DNA — Tôm Hùm built ON TOP of OpenClaw
> Status: CRITICAL — MUST track every release
> Action: Cherry-pick features from each release

## What
- OpenClaw = open-source AI agent platform
- Tôm Hùm CTO = custom fork/extension of OpenClaw
- Every OpenClaw release = potential upstream features to merge

## v2026.2.17 Key Changes (2026-02-17)

### CRITICAL (merge now)
1. **1M Context Header**: `params.context1m: true` → `anthropic-beta: context-1m-2025-08-07`
2. **Sonnet 4.6 Support**: `anthropic/claude-sonnet-4-6` model mapping

### HIGH (merge soon)
3. **Context Overflow Guard**: Pre-call truncation of oversized tool-results
4. **Cron Usage Telemetry**: Token usage per job logging
5. **Security OC-09**: Credential theft via env injection fix
6. **Auto-paging Read**: Read tool auto-pages, budget scales with contextWindow

### MEDIUM (backlog)
7. **Skill Routing**: "Use when" / "NOT for" guidance
8. **Cron Stagger**: Anti-thundering herd for scheduled tasks
9. **llms.txt Discovery**: Auto-discover LLM capabilities

## Tracking Protocol
- Watch: github.com/openclaw/openclaw/releases
- Frequency: Check weekly or on major releases
- Task: Create HIGH_mission_openclaw_upstream_sync.txt for each notable release

## Binh Pháp
- 知己知彼: Know your own DNA = know OpenClaw upstream
- 因糧於敵: Free features from upstream = zero development cost
- 軍形: Stay current with parent → stronger defense
