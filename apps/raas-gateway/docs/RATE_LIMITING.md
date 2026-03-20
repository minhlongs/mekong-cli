# Rate Limiting Implementation

## Overview

Token bucket rate limiting per tenant using Cloudflare KV storage.

## Architecture

### Token Bucket Algorithm

```
┌─────────────────────────────────────────────────────────┐
│  Token Bucket Rate Limiter                              │
├─────────────────────────────────────────────────────────┤
│  • Bucket capacity = max requests per minute            │
│  • Refill rate = tokens added per second                │
│  • Each request consumes 1 token                        │
│  • Requests denied when bucket empty                    │
│  • Tokens refill continuously over time                 │
└─────────────────────────────────────────────────────────┘
```

## Tier Limits

| Tier       | Requests/Min | Tokens/Second | Burst Capacity |
|------------|-------------:|--------------:|---------------:|
| starter    |          100 |    ~1.67/sec  |  100 requests  |
| pro        |          500 |    ~8.33/sec  |  500 requests  |
| enterprise |         2000 |   ~33.33/sec  | 2000 requests  |

## Implementation

### Files Created

- `src/services/rate-limit-service.ts` — Token bucket service with KV storage
- `src/middleware/rate-limiter.ts` — Hono middleware wrapper
- `tests/rate-limit.test.ts` — Unit tests (10 tests, 100% pass)

### Files Modified

- `src/middleware/index.ts` — Export rate limiter middleware
- `src/routes/api.ts` — Apply rate limiter after auth
- `src/types/auth.ts` — Add RateLimitTier interface
- `src/index.ts` — Export app for testing

### KV Storage Format

```json
{
  "key": "ratelimit:{tenantId}",
  "value": {
    "tokens": 95,
    "lastRefill": 1710837600000
  },
  "ttl": 120
}
```

**Auto-expiry:** 2 minutes of inactivity

## Response Headers

All authenticated responses include:

```
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1710837660
```

When rate limited (429):

```
HTTP/1.1 429 Too Many Requests
Retry-After: 36
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1710837660

{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "retryAfter": 36,
  "remaining": 0
}
```

## Middleware Order

```
Request → Logger → CORS → Auth → RateLimit → Handler
```

**Important:** Rate limiter MUST come after auth middleware (requires tenant context).

## Usage

```typescript
import { rateLimit } from './middleware/rate-limiter';

// Apply to protected routes (after auth)
api.use('/*', auth());
api.use('/*', rateLimit());

api.get('/data', (c) => {
  // Rate limit automatically applied
  return c.json({ data: '...' });
});
```

## Testing

```bash
# Run rate limit tests
npm test -- tests/rate-limit.test.ts

# All tests pass:
# ✓ checkLimit - allows requests under limit
# ✓ checkLimit - denies requests when exhausted
# ✓ checkLimit - refills tokens over time
# ✓ getStatus - returns status without consuming
# ✓ reset - clears rate limit bucket
```

## Error Handling

**KV Failure:** Fails open (allows request) to prevent false positives.

```typescript
try {
  return await checkLimit();
} catch (error) {
  console.error('[RateLimitService] Error:', error);
  return { allowed: true, ... }; // Fail open
}
```

## Production Considerations

1. **KV Cost:** Each request = 1 KV read + 1 KV write
   - At 100 RPM: ~144,000 ops/day = ~$0.50/month
2. **Edge Caching:** KV is globally replicated (<50ms latency)
3. **Burst Handling:** Token bucket allows controlled bursts up to capacity

## Future Enhancements

- [ ] Add rate limit bypass for internal services
- [ ] Implement sliding window for smoother limiting
- [ ] Add rate limit analytics dashboard
- [ ] Support custom rate limits per API endpoint
