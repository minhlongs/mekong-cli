# RaaS Gateway — Cloud API Gateway

> **第二篇 作戰 (Zuo Zhan)** — Waging war requires supply lines and logistics
>
> This file governs CC CLI behavior ONLY when working inside `apps/raas-gateway/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Role:** Cloud-to-Local bridge — connects Telegram/API commands to the Mekong ecosystem
**Function:** Routes Antigravity strategic commands to Tôm Hùm task queue

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Cloudflare Workers |
| Language | JavaScript (ES Modules) |
| Auth | Service token (`SERVICE_TOKEN` env) |
| Target | OpenClaw bridge URL or local Mekong gateway |

## Architecture

```
apps/raas-gateway/
├── index.js          # Main worker: route handler (fetch event)
└── wrangler.toml     # Cloudflare Workers config (secrets, routes)
```

### API Routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/jobs/:id` | Fetch job status from engine |
| POST | `/v1/jobs` | Submit new job to engine |
| POST | `/webhook/telegram` | Telegram bot webhook handler |

### Environment Variables (wrangler.toml secrets)

- `SERVICE_TOKEN` — Auth token for engine API
- `BRIDGE_URL` / `OPENCLAW_URL` — Target backend URL
- `TELEGRAM_BOT_TOKEN` — Telegram bot authentication

## Development Rules (Domain-Specific)

### Security (軍形)
- Zero Trust model — every request must be authenticated
- All endpoints rate-limited
- No secrets in code — use `wrangler.toml` secrets or Cloudflare dashboard
- Validate all incoming webhook payloads

### Deployment
- Deploy via `wrangler deploy` (NOT git push for this Worker)
- Test locally with `wrangler dev`
- Never expose internal engine URLs in responses

### Code Standards
- ES Module syntax (`export default { fetch() {} }`)
- Keep worker under 100 lines (edge compute, minimal logic)
- Error responses: `{ error: string, details?: string }`
- Always set `Content-Type: application/json`

## Quality Gates

- All routes must return proper HTTP status codes
- Error handling must never leak internal URLs or tokens
- Test all webhook flows end-to-end before deploy
