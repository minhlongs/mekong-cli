# Rate Limiting

Rate limiting policies for Mekong CLI APIs.

---

## Overview

Rate limits protect the platform from abuse and ensure fair usage. Limits vary by subscription tier.

---

## Tier-Based Limits

| Tier | Requests / minute | Burst | Concurrent connections |
|------|-------------------|-------|------------------------|
| Starter | 60 | 10 | 5 |
| Growth | 300 | 50 | 20 |
| Pro | 1000 | 200 | 50 |
| Enterprise | Custom | Custom | Custom |

**What counts toward limit:**

- All authenticated API requests
- `/api/v1/commands/execute` (each execution counts as 1)
- `/api/v1/plugins/*` endpoints
- `/api/v1/billing/*` endpoints
- Webhook deliveries (outgoing)

**What does NOT count:**

- `/health`, `/ready` (liveness/readiness probes)
- `/metrics` (Prometheus)
- Static assets from CDN

---

## Response Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 60           # Requests allowed per minute
X-RateLimit-Remaining: 45      # Requests remaining in current window
X-RateLimit-Reset: 1624267200  # Unix timestamp when window resets
```

**Example:**

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1624267200
```

---

## When Rate Limited (HTTP 429)

Exceeding the limit returns `429 Too Many Requests`:

```json
{
  "detail": "Rate limit exceeded. Limit: 60 requests/minute, retry after: 12 seconds",
  "code": "RATE_LIMIT_EXCEEDED",
  "request_id": "req_abc123",
  "retry_after": 12
}
```

Response headers:

```
Retry-After: 12  # Seconds to wait before retrying
```

**Client action:** Wait `retry_after` seconds (or `X-RateLimit-Reset` - current time) before retrying. Implement exponential backoff with jitter to avoid thundering herd.

---

## Endpoint-Specific Limits

Some endpoints have stricter limits due to resource intensity:

| Endpoint | Limit | Reason |
|----------|-------|--------|
| `/api/v1/commands/execute` | Same as tier | Standard |
| `/api/v1/plugins/install` | 10/min | Plugin installation is expensive |
| `/api/v1/billing/add-credits` | 5/min | Payment processing rate limit |
| `/api/v1/agents/create` | 20/min | Agent spawn consumes resources |

---

## Bypass Mechanisms

### Whitelisted IPs

Enterprise customers can request static IP whitelisting for no limits. Contact sales.

### Burst Allowance

The "burst" column in tier table allows temporary spikes above sustained rate. Example: Starter tier (60/min, burst 10) can do 70 requests in a short burst, then must wait for token bucket to refill.

### Retry-After Header

Always honor `Retry-After` header. If missing, calculate from `X-RateLimit-Reset`.

---

## Implementation (Token Bucket)

Mekong uses token bucket algorithm:

- Bucket size = burst limit
- Refill rate = requests per minute / 60 seconds
- Each request consumes 1 token
- If bucket empty → 429

---

## Monitoring

### Check Your Usage

```bash
# CLI command
mekong status --show-rate-limits

# Or API call
curl -H "Authorization: Bearer $TOKEN" \
  https://api.mekong.cli/api/v1/rate-limit-status
```

Response:

```json
{
  "tier": "Starter",
  "limit": 60,
  "remaining": 45,
  "reset_at": "2026-06-21T08:32:00Z",
  "usage_percent": 25
}
```

### Alerts

Configure alerts when usage exceeds 80% of limit:

```bash
mekong alerts create --metric rate_limit_usage --threshold 80 --email alerts@yourcompany.com
```

---

## Best Practices (Client)

1. **Batch operations** — Combine multiple requests when possible
2. **Cache responses** — Cache GET results for `Cache-Control` TTL
3. **Implement backoff** — Wait increasing delays on 429
4. **Use async** — Don't block on synchronous calls
5. **Monitor headers** — Log `X-RateLimit-Remaining` to track usage
6. **Upgrade tier** — If consistently hitting limits

---

## Server-Side Implementation

### FastAPI Middleware

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/v1/commands")
@limiter.limit("60/minute")
def list_commands():
    return {"commands": [...]}
```

### Redis-Backed Distributed Rate Limiting

For multi-worker deployments, use Redis:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.storage import RedisStorage

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

---

## Troubleshooting

### "I'm not making many requests but still get 429"

- Check for retries without backoff
- Multiple parallel processes/threads sharing same token
- Webhooks consuming limit
- IP address shared with other users (NAT)

**Solution:** Use separate tokens per process, implement backoff, upgrade tier.

### "Rate limit resets at unexpected times"

Rate limit window is sliding 60-second window, not fixed minute boundaries. Check `X-RateLimit-Reset` for exact reset time.

### "Burst not working as expected"

Burst allows temporary spike, but refill rate is fixed. After burst, you must wait for refill.

---

## Enterprise Custom Limits

Contact sales for:

- Higher per-minute limits
- Dedicated rate limit pool (not shared)
- IP whitelisting (unlimited from known IPs)
- Custom limits per endpoint

---

## See Also

- [API Reference](../reference/API_REFERENCE.md)
- [Authentication](./AUTHENTICATION.md)
- [Error Codes](./ERROR_CODES.md)

---

**Last Updated:** 2026-06-21  
**Token Bucket Algorithm:** Yes  
**Distributed:** Redis-backed for multi-worker
