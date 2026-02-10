# Phase 02 — Production Health Verification

> Secure the perimeter. Every system must respond before handover.

## Context Links

- [Plan Overview](plan.md)
- [Phase 01 — Commit](phase-01-commit-uncommitted-work.md) (dependency)
- Production: `sophia.agencyos.network`
- Vercel project: `sophia-ai-factory`

## Overview

- **Priority**: P1
- **Status**: Pending (blocked by Phase 01)
- **Description**: Verify all production systems are healthy — HTTP endpoints, env vars, Supabase, Inngest, Telegram webhook, URL resolution.

## Key Insights

- 3 production URLs exist: sophia.agency, sophia.agencyos.network, sophia-ai-factory.vercel.app
- Inngest cron (auto-discovery) runs daily 8AM UTC — verify it's registered
- Telegram webhook must point to production URL, not localhost
- All env vars must be set in Vercel production environment

## Requirements

### Functional
- All HTTP endpoints return expected status codes
- Supabase connection healthy (auth + database)
- Inngest functions registered and cron scheduled
- Telegram webhook responding

### Non-functional
- Response times < 2s for health endpoints
- SSL valid on all URLs

## Architecture

```
Browser → sophia.agencyos.network → Vercel Edge → Next.js App
                                       ├── /api/health → 200 OK
                                       ├── /api/webhooks/polar → POST only
                                       ├── /api/webhooks/telegram → POST only
                                       └── /api/inngest → Inngest SDK
                                              └── Supabase (Postgres + Auth)
```

## Related Code Files

- `apps/sophia-ai-factory/src/app/api/health/route.ts`
- `apps/sophia-ai-factory/src/app/api/webhooks/polar/route.ts`
- `apps/sophia-ai-factory/src/app/api/webhooks/telegram/route.ts`
- `apps/sophia-ai-factory/src/app/api/inngest/route.ts`

## Implementation Steps

### 1. HTTP Endpoint Checks
```bash
# Health check
curl -sI https://sophia.agencyos.network/api/health | head -3

# Landing page
curl -sI https://sophia.agencyos.network | head -3

# Dashboard (should redirect to login)
curl -sI https://sophia.agencyos.network/en/dashboard | head -5

# All 3 URLs resolve
curl -sI https://sophia.agency | head -3
curl -sI https://sophia-ai-factory.vercel.app | head -3
```

### 2. Vercel Environment Variables
```bash
# Check via Vercel CLI or dashboard
# Required env vars:
# NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY
# SUPABASE_SERVICE_ROLE_KEY
# POLAR_ACCESS_TOKEN, POLAR_WEBHOOK_SECRET
# OPENROUTER_API_KEY, ELEVENLABS_API_KEY, HEYGEN_API_KEY
# TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID
# API_ENCRYPTION_KEY
# ADMIN_USER, ADMIN_PASS
# INNGEST_EVENT_KEY, INNGEST_SIGNING_KEY
```

### 3. Supabase Connection
```bash
# Verify via /api/health (should include DB status)
curl -s https://sophia.agencyos.network/api/health | jq .
```

### 4. Inngest Functions
- Open Inngest dashboard, verify `auto-discover-affiliates` cron registered
- Verify `generate-campaign` function registered
- Check last execution status

### 5. Telegram Webhook
```bash
# Check webhook info
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo" | jq .
# Should show url pointing to sophia.agencyos.network/api/webhooks/telegram
```

### 6. SSL Certificate Validity
```bash
echo | openssl s_client -connect sophia.agencyos.network:443 2>/dev/null | openssl x509 -noout -dates
```

## Todo List

- [ ] Verify /api/health returns 200 with healthy status
- [ ] Verify landing page loads (200)
- [ ] Verify dashboard redirects to login (302/307)
- [ ] Verify all 3 URLs resolve correctly
- [ ] Confirm all env vars set in Vercel production
- [ ] Verify Supabase connection (auth + DB)
- [ ] Verify Inngest cron registered (8AM UTC)
- [ ] Verify Telegram webhook pointing to production
- [ ] Verify SSL certificates valid and auto-renewing
- [ ] Document any missing or misconfigured systems

## Success Criteria

- All HTTP endpoints respond with expected codes
- No missing env vars in Vercel production
- Inngest cron scheduled and last run successful
- Telegram webhook active and pointing to production URL
- SSL valid on all URLs

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Missing env vars in Vercel | Medium | High | Cross-reference .env.example vs Vercel settings |
| Telegram webhook stale | Medium | Medium | Re-register via API call |
| Inngest not connected | Low | Medium | Re-deploy Inngest route |
| sophia.agency DNS not configured | Low | High | Check DNS records, add if missing |

## Security Considerations

- Never expose env var VALUES in logs or reports
- Only verify env vars EXIST, not their content
- Telegram bot token must not be logged

## Next Steps

- Phase 03: E2E Checkout Verification (depends on all systems healthy)
