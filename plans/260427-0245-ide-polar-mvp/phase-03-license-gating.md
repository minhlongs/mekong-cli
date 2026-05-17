# Phase 03: License Gating Middleware

**Priority:** P0 — Required for paid access
**Status:** ✅ COMPLETE (2026-04-27)
**Effort:** 2-3 ngày
**Last Verified:** 2026-04-27 — license-middleware.test.ts + polar-webhook.test.ts pass
**Depends on:** Phase 01 (deployed gateway), Phase 02 (real product IDs)

## Context Links

- `src/api/polar_webhook.py:95` — `process_subscription_created` already creates license
- `src/lib/license_generator.py` — `LicenseKeyGenerator` exists
- `src/middleware/auth_middleware.py:145` — referrals to `mekongmind.com/pricing`
- `src/auth/session_manager.py` — JWT issuer (existing)
- `src/raas/credits.py` — `CreditStore` (existing, tested)
- `src/core/mcu_gate.py:143` — recharge URL formatter (existing)

## Overview

Code có sẵn từng mảnh:
- ✅ License key generator
- ✅ JWT session manager
- ✅ Credit store (CreditStore)
- ✅ MCU gate (deducts credits)
- ✅ Polar webhook → license creation

**Gap:** Không có middleware verify license trước khi serve `/v1/missions`. Hiện tại endpoint open — bất kỳ ai có URL đều submit được.

## Architecture

```
User → POST /v1/missions
       Header: Authorization: Bearer <jwt>
              │
              ▼
       ┌────────────────────────┐
       │ LicenseGateMiddleware  │
       │ 1. Verify JWT signature│
       │ 2. Extract tenant_id   │
       │ 3. Check license active│
       │ 4. Check MCU > 0       │ → If fail: HTTP 402 + recharge URL
       │ 5. Inject tenant_id    │
       └──────────┬─────────────┘
                  ▼
       create_mission_endpoint()
                  ▼
       After mission complete:
       MCUGate.deduct(tenant_id, 1)
```

## Requirements

### Functional
- Middleware reject HTTP 401 nếu không có JWT
- Middleware reject HTTP 401 nếu JWT invalid signature
- Middleware reject HTTP 402 nếu license inactive (cancelled/expired)
- Middleware reject HTTP 402 nếu MCU balance = 0
- Middleware inject `request.state.tenant_id` cho downstream handlers
- POST `/auth/login` accept `{license_key}` → trả JWT short-lived (1h)
- POST `/auth/refresh` accept refresh token → new JWT

### Non-Functional
- Latency overhead < 5ms per request (cache JWT decode + license lookup)
- Security: JWT signed HS256 với `JWT_SECRET` từ env (đã có)

## Related Code Files

### Modify
- `src/api/polar_webhook.py:95` — sau khi tạo license, gọi `email_license_to_user()`
- `src/polymarket/billing.py:40-42` — thêm Growth product mapping
- `src/api/gateway_mission_routes.py:38` — wrap endpoint với `Depends(license_gate)`

### Create
- `src/middleware/license_gate.py` — FastAPI dependency function `license_gate(request)`
- `src/api/auth_routes.py` — `/auth/login`, `/auth/refresh` endpoints
- `src/lib/license_email.py` — gửi email license key (Resend API)
- `tests/middleware/test_license_gate.py` — middleware tests
- `tests/api/test_auth_routes.py` — auth endpoint tests
- `docs/polar-setup.md` — runbook for Phase 02 humans

### Delete
- None

## Implementation Steps

1. **`src/middleware/license_gate.py`** — FastAPI dependency:
   ```python
   async def license_gate(request: Request) -> str:
       token = extract_bearer_token(request)
       if not token:
           raise HTTPException(401, "missing_token")
       try:
           claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
       except jwt.PyJWTError:
           raise HTTPException(401, "invalid_token")
       tenant_id = claims["tenant_id"]
       if not LicenseStore.is_active(tenant_id):
           raise HTTPException(402, {"error": "license_inactive", "recharge_url": ...})
       if CreditStore.balance(tenant_id) <= 0:
           raise HTTPException(402, {"error": "no_credits", "recharge_url": ...})
       request.state.tenant_id = tenant_id
       return tenant_id
   ```

2. **`src/api/auth_routes.py`** — POST `/auth/login`:
   - Accept `{"license_key": "lic_xxx"}`
   - Verify license → get `tenant_id`
   - Issue JWT (1h TTL) + refresh token (30d TTL)
   - Return `{"access_token", "refresh_token", "expires_in"}`

3. **`src/api/gateway_mission_routes.py`** — add dep:
   ```python
   @router.post("/missions")
   async def create_mission_endpoint(
       request: CreateMissionRequest,
       tenant_id: str = Depends(license_gate),
   ):
       ...
   ```

4. **`src/lib/license_email.py`** — Resend API:
   ```python
   def send_license_email(email: str, license_key: str, tier: str) -> None:
       requests.post("https://api.resend.com/emails", ...)
   ```

5. **Wire webhook** — in `polar_webhook.py:95`:
   ```python
   license_key = LicenseKeyGenerator.generate(tier)
   send_license_email(customer_email, license_key, tier)
   ```

6. **MCU deduct after mission** — `gateway_mission_routes.py` `_run_hybrid_router`:
   ```python
   if status == "completed":
       MCUGate.deduct(tenant_id, cost_mcu)
   ```

7. **Tests** — every new file gets test coverage ≥80%.

## Todo List

- [ ] `LicenseStore` — wrapper around existing `licenses` SQLite table (verify exists or create)
- [ ] `src/middleware/license_gate.py` (~80 lines)
- [ ] `src/api/auth_routes.py` (~120 lines)
- [ ] `src/lib/license_email.py` (~60 lines, with Resend)
- [ ] Wire `Depends(license_gate)` to `/v1/missions` POST + GET stream
- [ ] Wire `MCUGate.deduct` after mission completion
- [ ] `tests/middleware/test_license_gate.py` — 8+ test cases (no token, bad token, expired license, no credits, success path)
- [ ] `tests/api/test_auth_routes.py` — 6+ test cases
- [ ] Update `docs/polar-setup.md` with full setup runbook
- [ ] Smoke test: cURL flow login → mission → MCU deduct
- [ ] Update `.env.example` with `RESEND_API_KEY`, `LICENSE_EMAIL_FROM`

## Success Criteria

- Unauthenticated POST `/v1/missions` → HTTP 401
- Valid JWT, expired license → HTTP 402 with recharge URL
- Valid JWT, license OK, balance 0 → HTTP 402 with recharge URL
- Valid JWT, license OK, balance > 0 → HTTP 200, mission created, balance decremented
- Email arrives within 30s of Polar webhook
- All new tests pass; no regression in existing 7095 tests

## Risk Assessment

| Risk | Mitigation |
|---|---|
| JWT secret rotation breaks live sessions | Use refresh token flow; document rotation procedure |
| Email delivery fail (Resend down) | Retry queue (dead letter) + manual resend admin endpoint |
| License key visible in URL params | Always use POST body or Authorization header |
| Race: Polar webhook arrives before email service ready | Idempotent — webhook already idempotent via event_id |

## Security Considerations

- Bcrypt-hash license keys at rest (existing `LicenseKeyGenerator` does this)
- JWT TTL ≤ 1h (force re-auth)
- Refresh token rotation on each use
- Rate limit `/auth/login` (5 req/min/IP)
- Audit log every license issuance + every MCU deduct

## Next Steps

Phase 04 — IDE UI consumes these auth endpoints.
