# 🐈 nanobot — Ultra-Lightweight OpenClaw — 知己知彼 Architecture Intel

> Source: github.com/HKUDS/nanobot (Hong Kong University)
> Assessed: 2026-02-18 | Status: NOTE — Learn Message Bus pattern
> Action: Ghi nhận architecture patterns

## What
- "Ultra-Lightweight OpenClaw" — 4K lines Python core
- Personal AI assistant with 7+ chat channels
- MCP native, multi-provider, scheduled tasks
- Educational/research focus

## Architecture Worth Studying
- bus/ — Message routing (centralized bus pattern)
- heartbeat/ — Proactive wake-up (similar to brain-supervisor)
- 4K lines = proof that lean agents work

## vs Tôm Hùm
- nanobot = lightweight personal assistant
- Tôm Hùm = enterprise AGI engine (11 daemons)
- Different scope, no competition

## 1 Pattern Worth Learning
**Message Bus**: Centralized routing between channels
- nanobot routes: Telegram ↔ Discord ↔ Slack ↔ Email via bus/
- Tôm Hùm could add: tmux ↔ Telegram ↔ webhook via central bus
- P4 future: when adding more channels

## Skip Reason
- Khác scope: personal vs enterprise
- Tôm Hùm đã mạnh hơn ở orchestration/planning
- Multi-channel gap sẽ được fill bằng Postiz (social) + gogcli (Google)
