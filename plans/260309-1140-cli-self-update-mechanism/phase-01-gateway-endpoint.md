---
title: "Phase 1: RaaS Gateway Version Endpoint"
description: "Add /v1/cli/version endpoint to RaaS Gateway for version checking"
status: pending
priority: P1
effort: 2h
branch: master
tags: [phase-6, raas-gateway, endpoint]
created: 2026-03-09
---

# Phase 1: RaaS Gateway Version Endpoint

## Overview

Add new endpoint to RaaS Gateway (Cloudflare Worker) that returns latest CLI version info with enforcement flags.

## Requirements

1. New endpoint: `GET /v1/cli/version`
2. Response includes: version, download_url, checksum_url, is_critical, release_notes
3. Auth: API key (mk_) or JWT required
4. Rate limiting: Per tenant
5. Usage tracking: Log version check events

## Context Links

- Gateway: `/Users/macbookprom1/mekong-cli/apps/raas-gateway/index.js`
- Gateway CLAUDE.md: `/Users/macbookprom1/mekong-cli/apps/raas-gateway/CLAUDE.md`
- Existing endpoints: `/v1/usage`, `/v1/overage/calculate`

## Key Insights

From reading `apps/raas-gateway/index.js`:
- Gateway uses Cloudflare Workers
- Auth via `authenticate()` function (JWT + mk_ API keys)
- Rate limiting via `checkRateLimit()` (KV-based)
- Usage tracking via `trackUsage()` (KV-based monthly aggregation)
- KV store for state: `RATE_LIMIT_KV`, `RAAS_USAGE_KV`

## Architecture

### New Route in index.js

```javascript
// --- ROUTE: GET /v1/cli/version (CLI version check) ---
if (path === '/v1/cli/version' && request.method === 'GET') {
  // Return latest CLI version info
  return getCliVersionInfo(env, tenantId, role);
}
```

### Response Format

```json
{
  "latest_version": "3.0.1",
  "current_version": "3.0.0",
  "download_url": "https://github.com/.../mekong-cli-3.0.1.tar.gz",
  "checksum_url": "https://github.com/.../sha256sum.txt",
  "signature_url": "https://github.com/.../signature.sig",
  "is_critical": false,
  "is_security_update": false,
  "release_notes": "Bug fixes and improvements",
  "released_at": "2026-03-09T12:00:00Z"
}
```

## Implementation Steps

1. **Add route handler function** to `apps/raas-gateway/index.js`
2. **Store version config** in KV or environment variables
3. **Track usage** of version check endpoint
4. **Add rate limiting** (separate from API rate limits)

## Related Code Files

**To Create:**
- `apps/raas-gateway/src/cli-version-handler.js` — Version check handler

**To Modify:**
- `apps/raas-gateway/index.js` — Add route + import handler
- `apps/raas-gateway/wrangler.toml` — Add version env vars

## Todo List

- [ ] Create `cli-version-handler.js` with `getCliVersionInfo()` function
- [ ] Add route to `index.js` main fetch handler
- [ ] Add version config to wrangler.toml (or KV)
- [ ] Integrate usage tracking (`trackUsage()`)
- [ ] Add rate limiting for version checks
- [ ] Test endpoint locally with `wrangler dev`
- [ ] Deploy to production with `wrangler deploy`

## Success Criteria

- [ ] `GET /v1/cli/version` returns valid JSON with auth
- [ ] Returns 401 without auth
- [ ] Rate limiting works (100 checks/hour per tenant)
- [ ] Usage events tracked in KV
- [ ] `is_critical` flag can be set via config

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| KV read latency | Medium | Cache version in memory |
| Rate limit too strict | Low | Adjust limits per feedback |
| Version config stale | Medium | Add manual trigger for updates |

## Security Considerations

- Auth required (same as other `/v1/*` routes)
- Rate limiting per tenant
- No sensitive data in response
- Signature URL points to HTTPS-only GitHub Releases

## Next Steps

After Phase 1 complete:
- Phase 2: CLI-side integration for startup check
