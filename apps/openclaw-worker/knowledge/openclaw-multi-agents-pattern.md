# OpenClaw Multi-Agents Pattern — Reference Intel

> Source: github.com/hoangnb24/storage/openclaw/multi-agents-setup.md
> Assessment: LEARN — Validate Tôm Hùm architecture
> Date: 2026-02-18

## Core Pattern: 3 Homes

```
Workspace = SOUL.md + IDENTITY.md + MEMORY.md (personality + knowledge)
AgentDir  = auth-profiles.json (credentials, API keys)
Sessions  = conversation history (short-term memory)
```

## Agent-to-Agent Protocol

```json
{
  "tools": { "agentToAgent": { "enabled": true, "allow": ["main", "agent2"] } },
  "session": { "agentToAgent": { "maxPingPongTurns": 3 } }
}
```

Tool: `sessions_send` → route to `agent:<id>:<channel>:<identifier>`
Pitfall: `ANNOUNCE_SKIP` — agent might hide response. Fix in SOUL.md.

## Tôm Hùm Mapping

| Pattern | Status | Upgrade |
|:--------|:-------|:--------|
| SOUL.md | ✅ BINH_PHAP_MASTER.md | Already superior |
| IDENTITY.md | ✅ DOANH_TRAI.md | Already has roles |
| MEMORY.md | ⏳ File-based | → Mem0 (HIGH task) |
| sessions_send | ⏳ File locks | → Agent Teams (HIGH task) |
| maxPingPongTurns | ❌ No limit | → Add to config |
| ANNOUNCE_SKIP | ❌ No concept | → Add to dispatcher |
