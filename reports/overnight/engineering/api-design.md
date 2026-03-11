# API Design Review — Mekong CLI

**Date:** 2026-03-11
**Scope:** RaaS Gateway (CF Worker), internal Python API adapter, endpoint structure

---

## 1. RaaS Gateway Overview

**File:** `apps/raas-gateway/index.js` — Cloudflare Worker v2.0.0
**Language:** JavaScript ES Modules
**Runtime:** Cloudflare Workers (V8 isolates, edge compute)

Gateway sits between external clients (dashboard, CLI, Telegram) and FastAPI backend:

```
Client → CF Worker (Edge) → FastAPI Backend (Fly.io or local)
              │
              ├── Auth (JWT + mk_ API keys)
              ├── Rate limiting (KV-based per tenant)
              ├── Usage metering (KV buckets)
              ├── Quota enforcement
              └── Suspension checks
```

---

## 2. Gateway Routes

| Method | Path | Handler | Auth Required |
|--------|------|---------|--------------|
| GET | `/health` | Inline | No |
| GET | `/v1/status` | Inline | No |
| POST | `/telegram` | Telegram webhook | Bot token |
| ANY | `/v1/*` | Proxy to backend | JWT or mk_ key |
| GET | `/v1/license/activate` | `handleLicenseActivation` | mk_ key |
| GET | `/v1/cli/version` | `getCliVersionInfo` | No |

---

## 3. Authentication Layers

**Import chain:**
```javascript
import { authenticate } from './src/edge-auth-handler.js';
```

Two auth schemes supported:
1. **JWT (Supabase)** — Bearer token from dashboard login
2. **mk_ API keys** — `mk_live_*` / `mk_test_*` prefixed keys for CLI

Auth result enriches request context with `userId`, `role`, `tier` before rate limit checks.

**CORS origins** (hardcoded whitelist):
```javascript
const CORS_ORIGINS = [
  'https://agencyos.network',
  'https://sophia.agencyos.network',
  'https://raas.agencyos.network',
  'http://localhost:3000',
  'http://localhost:5173'
];
```

---

## 4. Middleware Pipeline (per request)

Order of execution per inbound request:

```
1. CORS preflight check (OPTIONS → return headers)
2. authenticate()          — JWT or mk_ key validation
3. checkSuspensionStatus() — KV suspension flag
4. checkRateLimit()        — per-API-key sliding window
5. checkQuota()            — monthly MCU quota
6. validateExtensionFlags()— feature flag gates
7. trackUsage()            — KV usage metering
8. Proxy to backend / route handler
9. checkAndTriggerAlerts() — quota threshold webhooks
10. buildQuotaHeaders()    — X-Quota-* response headers
```

---

## 5. Feature Flags per Role

```javascript
const features = {
  free:       ['basic_cli_commands', 'open_source_agents', 'community_patterns'],
  trial:      [...free, 'trial_agents'],
  pro:        [...free, 'premium_agents', 'advanced_patterns', 'priority_support',
               'custom_workflows', 'ml_models', 'premium_data'],
  enterprise: [...pro, 'agi_auto_pilot', 'team_collaboration', 'audit_logs',
               'sso_integration', 'dedicated_support', 'custom_integrations'],
  service:    ['all']
}
```

---

## 6. Python API Adapter (`src/core/api_adapter.py`)

Internal adapter used by executor's `_execute_api_step`. Wraps `requests` with:
- Configurable base URL, headers, auth
- JSON body serialization
- Timeout (30s default)
- Status-code-based error detection

Used for LLM API calls and internal service calls from recipes.

---

## 7. Gateway Client (`src/core/gateway_client.py`, 626 lines)

Python-side client for calling the RaaS gateway from CLI. Key patterns:
- Reads `MEKONG_GATEWAY_URL` env var (defaults to `https://raas.agencyos.network`)
- Reads `MEKONG_API_KEY` or `mk_*` key from env/config
- Sets `Authorization: Bearer <token>` header
- Handles `HTTP 402` (zero balance) → prints MCU top-up message
- Handles `HTTP 429` (rate limited) → exponential backoff with jitter

---

## 8. Response Schema Standards

**Success:**
```json
{
  "status": "ok",
  "data": { ... },
  "version": "2.0.0"
}
```

**Error:**
```json
{
  "error": "Unauthorized",
  "details": "Invalid mk_ API key format"
}
```

**Rate limit exceeded:**
```
HTTP 429
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1741704000
Retry-After: 3600
```

**Quota exceeded:**
```
HTTP 402
X-Quota-Used: 200
X-Quota-Limit: 200
X-Quota-Reset: 2026-04-01
```

---

## 9. API Design Issues

| Issue | Location | Severity |
|-------|----------|----------|
| CORS origins hardcoded | index.js:62-68 | MEDIUM — env var preferred |
| No versioning on `/health` and `/v1/status` | gateway routes | LOW |
| `validateExtensionFlags` called before `checkQuota` | middleware order | LOW — quota should gate first |
| `gateway_client.py` is 626 lines | Python client | MEDIUM — split needed |
| No API schema (OpenAPI/JSONSchema) | entire gateway | MEDIUM — no contract |
| Telegram webhook path `/telegram` (no version prefix) | index.js | LOW |

---

## 10. Recommendations

1. **Add OpenAPI spec** for `/v1/*` endpoints — generate from FastAPI auto-docs
2. **Move CORS origins to env var** (`CORS_ALLOWED_ORIGINS`) — avoid deploys for origin changes
3. **Reorder middleware** — run `checkQuota` before `validateExtensionFlags` (fail fast on quota)
4. **Split `gateway_client.py`** into `gateway_auth_client.py` + `gateway_request_client.py`
5. **Add request ID header** (`X-Request-Id`) for distributed tracing across Worker → backend
6. **Add schema validation** on webhook payloads — Telegram sends arbitrary JSON
7. **Document mk_ key format** — `mk_live_<32-char-hex>` vs `mk_test_<32-char-hex>` in README
