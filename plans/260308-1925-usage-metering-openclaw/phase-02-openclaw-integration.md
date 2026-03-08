---
phase: 2
title: "OpenClaw Worker Integration"
status: pending
effort: 2h
---

# Phase 2: OpenClaw Worker Integration

## Overview

Modify OpenClaw Worker to forward requests to RaaS Gateway with proper API key authentication, enabling automatic usage tracking.

## Key Insights

From research, OpenClaw Worker currently:
- Uses Telegram-based auth (user IDs)
- Has `BRIDGE_URL` for backend communication
- Does NOT have usage metering

**Recommended approach (Option A):**
- OpenClaw sends requests to RaaS Gateway (not directly to backend)
- RaaS Gateway tracks usage in KV (already implemented)
- Backend receives tenant context via headers (`X-Tenant-Id`, `X-Tenant-Role`)

## Requirements

### Functional
1. OpenClaw Worker sends requests to RaaS Gateway with `Authorization: Bearer mk_xxx`
2. RaaS Gateway validates API key and tracks usage
3. Backend receives tenant context headers for billing

### Non-Functional
1. Maintain backward compatibility with existing Telegram auth
2. Support both service-level and user-specific API keys
3. Handle RaaS Gateway unavailable gracefully

## Related Code Files

### Files to Modify
- `apps/openclaw-worker/src/index.ts` — Add RaaS forwarding logic
- `apps/openclaw-worker/wrangler.jsonc` — Add RAAS_GATEWAY_URL var

### Files to Create
- None (reuse existing RaaS Gateway metering)

## Architecture

### Current Flow (BEFORE)
```
Telegram → OpenClaw → BRIDGE_URL (FastAPI)
                      ↓
                 No usage tracking
```

### New Flow (AFTER)
```
Telegram → OpenClaw → RAAS_GATEWAY_URL → BRIDGE_URL (FastAPI)
                      ↓
                 Usage tracked in
                 RAAS_USAGE_KV
```

## Implementation Steps

### Step 1: Update Env Interface

Add `RAAS_GATEWAY_URL` to `Env` interface in `src/index.ts`:

```typescript
interface Env {
  TELEGRAM_BOT_TOKEN: string;
  ALLOWED_USER_IDS: string;
  AI: Ai;
  BRIDGE_URL?: string;
  RAAS_GATEWAY_URL?: string;  // NEW
  RAAS_SERVICE_TOKEN?: string; // NEW
}
```

### Step 2: Add RaaS Proxy Function

Create helper function in `src/index.ts`:

```typescript
/**
 * Proxy request to RaaS Gateway with API key auth
 * @param {Request} request
 * @param {Env} env
 * @param {string} tenantId
 * @returns {Promise<Response>}
 */
async function proxyToRaaS(
  request: Request,
  env: Env,
  tenantId: string
): Promise<Response> {
  const raasUrl = env.RAAS_GATEWAY_URL || env.BRIDGE_URL;
  if (!raasUrl) {
    return new Response('RaaS Gateway not configured', { status: 503 });
  }

  const targetUrl = `${raasUrl}${new URL(request.url).pathname}`;
  const apiKey = env.RAAS_SERVICE_TOKEN || 'mk_default_service';

  const headers = new Headers(request.headers);
  headers.set('Authorization', `Bearer ${apiKey}`);
  headers.set('X-Forwarded-For', tenantId);
  headers.set('X-RaaS-Source', 'openclaw-worker');

  const init: RequestInit = {
    method: request.method,
    headers,
    redirect: 'follow',
  };

  if (!['GET', 'HEAD'].includes(request.method)) {
    init.body = request.body;
    init.duplex = 'half';
  }

  return fetch(targetUrl, init);
}
```

### Step 3: Update /delegate Command

Modify `/delegate` handler to route through RaaS Gateway:

```typescript
'/delegate': async (args, env, chatId) => {
  if (!args) {
    return '❌ Usage: /delegate <task for Antigravity>';
  }

  try {
    await sendTelegramAction(env.TELEGRAM_BOT_TOKEN, chatId, 'typing');

    // Create request for RaaS Gateway
    const request = new Request(`${env.RAAS_GATEWAY_URL}/v1/extension/${encodeURIComponent(args)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task: args, chatId, timestamp: new Date().toISOString() }),
    });

    // Proxy through RaaS Gateway (usage tracked automatically)
    const response = await proxyToRaaS(request, env, `telegram:${chatId}`);

    if (!response.ok) {
      return `❌ RaaS Gateway error: ${response.status}`;
    }

    const result = await response.json();
    return `✅ Task sent to Antigravity!

🔑 Tenant: telegram:${chatId}
📊 Status: ${result.status || 'queued'}

Usage tracked via RaaS Gateway.`;

  } catch (error) {
    return `❌ Error: ${error instanceof Error ? error.message : 'Unknown'}`;
  }
},
```

### Step 4: Add New /raas Command

Add command to check usage and tenant status:

```typescript
'/raas': async (args, env, chatId) => {
  if (!env.RAAS_GATEWAY_URL) {
    return '⚠️ RaaS Gateway not configured';
  }

  const apiKey = env.RAAS_SERVICE_TOKEN || 'mk_default_service';

  try {
    // Get tenant status
    const statusResponse = await fetch(`${env.RAAS_GATEWAY_URL}/v1/status`, {
      headers: { 'Authorization': `Bearer ${apiKey}` },
    });

    if (!statusResponse.ok) {
      return `❌ RaaS status check failed: ${statusResponse.status}`;
    }

    const status = await statusResponse.json();

    return `📊 **RaaS Gateway Status**

🟢 Gateway: ${status.status}
👤 Tenant: ${status.tenant || 'service'}
📈 Rate Limit: ${status.rateLimit?.remaining || 'N/A'} / ${status.rateLimit?.limit || 'N/A'}
⏰ ${new Date().toISOString()}`;

  } catch (error) {
    return `❌ Error: ${error instanceof Error ? error.message : 'Unknown'}`;
  }
},
```

### Step 5: Update /status Command

Add RaaS Gateway status to existing `/status` command:

```typescript
'/status': async (_, env) => {
  const bridgeStatus = env.BRIDGE_URL ? '🟢 Connected' : '🔴 Offline';
  const raasStatus = env.RAAS_GATEWAY_URL ? '🟢 Connected' : '🔴 Offline';

  return `📊 **System Status**

🟢 Worker: Online (v3.0)
🟢 AI: Llama 3.1 Active
${bridgeStatus} Bridge: ${env.BRIDGE_URL?.slice(0, 40) || 'Not configured'}
${raasStatus} RaaS Gateway: ${env.RAAS_GATEWAY_URL?.slice(0, 40) || 'Not configured'}
⏰ ${new Date().toISOString()}`;
},
```

## Success Criteria

- [ ] OpenClaw Worker compiles without TypeScript errors
- [ ] `/delegate` commands route through RaaS Gateway
- [ ] Usage appears in RaaS Gateway KV for each delegated task
- [ ] `/raas` command returns tenant status
- [ ] `/status` shows RaaS Gateway connection status
- [ ] Backward compatible: existing commands still work

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| RaaS Gateway unavailable | High — OpenClaw broken | Fallback to direct BRIDGE_URL if RaaS fails |
| API key exposure | Critical — security breach | Use wrangler secrets, never log tokens |
| Usage tracking overhead | Low — slight latency increase | KV operations are async, non-blocking |

## Security Considerations

- **API Key Storage**: Use `wrangler secret put RAAS_SERVICE_TOKEN`
- **Tenant ID Mapping**: Telegram chat IDs → tenant IDs (e.g., `telegram:123456`)
- **Header Injection**: RaaS Gateway strips original Authorization, adds `X-Tenant-Id`

## Next Steps

After integration complete, proceed to [Phase 3: RaaS Gateway Enhancement](./phase-03-raas-enhancement.md)
