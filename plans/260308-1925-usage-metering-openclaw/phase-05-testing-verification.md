---
phase: 5
title: "Testing & Verification"
status: pending
effort: 1h 30m
---

# Phase 5: Testing & Verification

## Overview

End-to-end testing of OpenClaw → RaaS Gateway → Backend flow with usage tracking verification.

## Key Insights

Test scenarios:
1. Local dev: `wrangler dev` for both workers
2. Production: Deployed Workers with real KV
3. Usage verification: Check KV storage after requests

## Requirements

### Functional
1. Test OpenClaw `/delegate` command routes through RaaS
2. Verify usage appears in `RAAS_USAGE_KV`
3. Test rate limiting enforcement
4. Test suspension check blocks unauthorized tenants

### Non-Functional
1. Test without production API keys (use test keys)
2. Document test results for future reference

## Related Code Files

### Test Files to Create
- `apps/raas-gateway/tests/openclaw-integration.test.js` — Integration tests

### Files to Verify
- `apps/openclaw-worker/src/index.ts` — Compiled JS works
- `apps/raas-gateway/index.js` — Routes correctly

## Test Scenarios

### Scenario 1: Basic Usage Tracking

```
1. Send /delegate command via OpenClaw
2. RaaS Gateway receives request with mk_ API key
3. RaaS tracks usage in KV: usage:mk_test:2026-03-08-19
4. Verify KV contains request count = 1
```

### Scenario 2: Rate Limiting

```
1. Send 100+ requests in 1 minute (free tier limit)
2. RaaS should return 429 Too Many Requests
3. Verify rate limit headers present
```

### Scenario 3: Suspension Check

```
1. Mark tenant as SUSPENDED in SUSPENSION_CACHE
2. Send request from suspended tenant
3. RaaS should return 403 Forbidden
```

## Implementation Steps

### Step 1: Local Dev Test

```bash
# Terminal 1: Start RaaS Gateway
cd apps/raas-gateway
wrangler dev

# Terminal 2: Start OpenClaw Worker
cd apps/openclaw-worker
wrangler dev

# Terminal 3: Test OpenClaw
curl -X POST http://localhost:8788/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"message":{"from":{"id":123456,"first_name":"Test"},"chat":{"id":123456},"text":"/delegate test task"}}'
```

### Step 2: Verify KV Storage

```bash
# List KV keys for usage
wrangler kv:key list --namespace-id=RAAS_USAGE_KV_ID

# Should see: usage:mk_test:2026-03-08-19

# Get usage data
wrangler kv:key get --namespace-id=RAAS_USAGE_KV_ID "usage:mk_test:2026-03-08-19"

# Should return JSON with requestCount, payloadSize, etc.
```

### Step 3: Integration Test Script

Create `apps/raas-gateway/tests/openclaw-integration.test.js`:

```javascript
import { describe, it, expect, beforeEach } from 'vitest';
import worker from '../index.js';

describe('OpenClaw Integration', () => {
  let mockEnv;

  beforeEach(() => {
    mockEnv = {
      RAAS_USAGE_KV: {
        get: vi.fn(),
        put: vi.fn(),
        list: vi.fn(),
      },
      RATE_LIMIT_KV: {
        get: vi.fn(),
        put: vi.fn(),
      },
      SERVICE_TOKEN: 'mk_test_token',
      MK_API_KEYS: 'mk_test:tenant1:free',
    };
  });

  it('tracks usage for valid API key', async () => {
    const request = new Request('http://localhost/v1/extension/test', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer mk_test' },
    });

    const response = await worker.fetch(request, mockEnv);
    expect(response.status).toBe(200);
    expect(mockEnv.RAAS_USAGE_KV.put).toHaveBeenCalled();
  });
});
```

### Step 4: Run Tests

```bash
cd apps/raas-gateway
npm test -- --run tests/openclaw-integration.test.js
```

## Success Criteria

- [ ] Local dev: Both workers start without errors
- [ ] OpenClaw → RaaS → Backend flow works
- [ ] Usage data stored in KV with correct format
- [ ] Rate limiting enforced at configured limits
- [ ] Suspension check blocks suspended tenants
- [ ] Integration tests pass

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Test pollution in production KV | Low — use test keys | Prefix test keys with `test:` |
| Missing edge cases | Medium — prod bugs | Test rate limit boundary (100 requests) |
| KV not cleaned up | Low — TTL handles cleanup | 24-hour TTL ensures auto-deletion |

## Next Steps

Proceed to [Phase 6: Documentation](./phase-06-documentation.md)
