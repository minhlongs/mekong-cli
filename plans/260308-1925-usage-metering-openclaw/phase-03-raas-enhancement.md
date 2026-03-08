---
phase: 3
title: "RaaS Gateway Enhancement"
status: pending
effort: 1h
---

# Phase 3: RaaS Gateway Enhancement (Optional)

## Overview

Add OpenClaw-specific endpoints to RaaS Gateway if needed for advanced features like usage queries or custom rate limits.

**Note:** This phase is OPTIONAL. RaaS Gateway already has all core functionality.

## Key Insights

RaaS Gateway already supports:
- `/v1/usage` — Get usage metrics
- `/v1/overage/calculate` — Calculate overage costs
- `/v1/extension/status` — Extension eligibility
- `/internal/sync-suspension` — Sync suspension status

May need:
- `/v1/usage/telegram` — Telegram-specific usage endpoint

## Requirements

### Functional
1. Add optional Telegram-specific usage endpoint
2. Support chat ID-based tenant lookup

### Non-Functional
1. Maintain backward compatibility
2. Keep worker under 200 lines per module

## Related Code Files

### Files to Modify
- `apps/raas-gateway/index.js` — Add optional endpoints
- `apps/raas-gateway/src/kv-usage-meter.js` — Add Telegram helper (optional)

### Files to Create
- None (existing modules sufficient)

## Implementation Steps

### Step 1: Add Telegram Tenant Mapping (Optional)

If mapping Telegram chat IDs to tenant IDs:

```javascript
// In index.js, add helper function
function mapTelegramToTenant(telegramChatId) {
  // Option A: Direct mapping (telegram:123456 → tenant ID)
  return `telegram:${telegramChatId}`;

  // Option B: Lookup table (store in KV)
  // return env.TELEGRAM_TENANT_KV.get(telegramChatId);
}
```

### Step 2: Add /v1/usage/telegram Endpoint

Add to `index.js` route handling:

```javascript
// --- ROUTE: GET /v1/usage/telegram (Telegram-specific usage) ---
if (path === '/v1/usage/telegram' && request.method === 'GET') {
  const { authenticated, tenantId, role, licenseKey, error: authError } = authenticate(request, env);

  if (!authenticated) {
    return jsonResponse({ error: 'Unauthorized', details: authError }, 401, corsHeaders);
  }

  const url = new URL(request.url);
  const chatId = url.searchParams.get('chat_id') || tenantId.replace('telegram:', '');
  const targetLicenseKey = licenseKey || `mk_telegram_${chatId}`;

  return getUsageMetrics(env, targetLicenseKey, null, null, 10, 0).then(result => {
    return jsonResponse({
      telegram_chat_id: chatId,
      tenant_id: tenantId,
      metrics: result.metrics,
      total: result.total,
      has_more: result.hasMore
    }, 200, corsHeaders);
  });
}
```

## Success Criteria

- [ ] Optional endpoints return correct data
- [ ] No breaking changes to existing endpoints
- [ ] Worker deploys without errors

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-engineering | Medium — unnecessary complexity | Skip this phase if not needed |
| Tenant mapping conflicts | Low — wrong tenant charged | Use consistent mapping strategy |

## Next Steps

Proceed to [Phase 4: KV Namespace Configuration](./phase-04-kv-configuration.md)
