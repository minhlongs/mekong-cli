# Mekong CLI — Billing/Payment/Metering System Map

**Generated:** 2026-08-16  
**Scope:** Complete inventory of billing, payment, and metering code across the repository

---

## Executive Summary

The Mekong CLI contains **3 distinct billing implementations** and **5 Tier enum definitions** operating in parallel. Only **System 1 (MCU Billing)** is wired to the live gateway; Systems 2 & 3 are partially integrated but dormant for production traffic.

| System | Status | Entry Point | Tier Enum |
|--------|--------|-------------|-----------|
| **MCU Billing** (src/core/mcu_billing.py) | **LIVE** — Wired to `src/gateway.py` global instance | FastAPI `/health` + mission endpoints via `license_gate` | `TierKey` (src/seed/config/tiers.py) |
| **Engine Billing** (engine/billing/) | **DORMANT** — Tests only; middleware not added to gateway | `engine/billing/tier_rate_limit_middleware.py` (never mounted) | `Tier` (engine/billing/tier_config.py) |
| **Engine Payments** (engine/payments/) | **PARTIAL** — Used by `RaasLicenseGate` via `usage_meter.py` | CLI commands + `src/lib/raas_gate/` | `Tier` (engine/license/license_metadata.py) |

---

## 1. Three Billing Implementations Comparison

### 1.1 System 1: MCU Billing (LIVE — Canonical)

**Files:**
- `src/core/mcu_billing.py` (9747 bytes, 267 lines) — Core MCU accounting
- `src/core/mcu_gate.py` (9637 bytes, 235 lines) — Atomic lock/confirm/refund
- `src/middleware/license_gate.py` (2607 bytes, ~84 lines) — FastAPI dependency

**Architecture:**
- **Credit Unit:** 1 MCU = 1 credit
- **Storage:** SQLite WAL at `~/.mekong/credits.db`
- **Operations:** `add_credits()`, `deduct()`, `lock()`, `confirm()`, `refund_full()`, `refund_partial()`
- **Cost Table:** `MCU_COSTS` — maps operation types (standard, premium, etc.) to credit costs
- **Tier Credits:** `TIER_CREDITS` — monthly credit allocation per tier (starter=100, growth=500, premium=2000)

**Wiring:**
```python
# src/gateway.py:248-250
from src.core.mcu_billing import MCUBilling
mcu_billing = MCUBilling()  # Global singleton
```

```python
# src/middleware/license_gate.py:74-79
credits = CreditStore()
if credits.get_balance(tenant_id) <= 0:
    raise HTTPException(402, detail={"error": "no_credits"})
request.state.tier = claims.get("tier", "starter")
```

**Tier Source:** `src/seed/config/tiers.py` → `TierKey` enum (BASIC, PREMIUM, ENTERPRISE, MASTER + VN aliases)

---

### 1.2 System 2: Engine Billing — Tier Rate Limiting (DORMANT)

**Files:**
- `engine/billing/tier_config.py` (4451 bytes, ~143 lines) — Tier enum + rate limit configs
- `engine/billing/tier_rate_limit_middleware.py` (16156 bytes, ~400 lines) — FastAPI middleware
- `engine/billing/tier_rate_limit_dispatch.py` (4009 bytes) — Dispatch logic
- `engine/billing/tier_rate_limit_policy.py` (3728 bytes) — Policy definitions
- `engine/billing/tier_rate_limit_events.py` (2268 bytes) — Event hooks

**Architecture:**
- **Tier Enum:** `Tier.FREE`, `Tier.TRIAL`, `Tier.PRO`, `Tier.ENTERPRISE` (different from MCU!)
- **Rate Limits:** Per-tier `requests_per_minute`, `requests_per_hour`, `burst_allowance`
- **Presets:** `api_default`, `api_strict`, `auth_default`, `auth_strict`
- **Storage:** In-memory token bucket + optional Redis (not configured)
- **License Validation:** Uses `engine.license.jwt_license_generator.validate_jwt_license()`

**Critical Finding:** Middleware class exists but **never mounted** on FastAPI app in `src/gateway.py`. Only tests import it.

**Wiring Attempt (dead):**
```python
# engine/billing/tier_rate_limit_middleware.py:428-432
class ConfiguredMiddleware(TierRateLimitMiddleware):
    def __init__(self, app):
        super().__init__(app)
```
No `app.add_middleware(ConfiguredMiddleware)` anywhere in codebase.

---

### 1.3 System 3: Engine Payments — Usage Metering (PARTIAL)

**Files:**
- `engine/payments/usage_meter.py` (5149 bytes, ~125 lines) — PostgreSQL-backed meter
- `engine/payments/usage_metering_service.py` (23953 bytes, ~650 lines) — Full service with circuit breaker, HMAC auth, batching

**Architecture:**
- **Storage:** PostgreSQL (asyncpg) — `license_usage` table
- **Tier Limits:** From `engine/license/license_metadata.py`:
  ```python
  TIER_LIMITS = {
      "free": {"commands_per_day": 10, "max_days": None},
      "trial": {"commands_per_day": 50, "max_days": 7},
      "pro": {"commands_per_day": 1000, "max_days": None},
      "enterprise": {"commands_per_day": -1, "max_days": None},
  }
  ```
- **Operations:** `record_usage(key_id, tier, commands_count)`, `get_usage_summary(key_id)`

**Wiring:**
- Used by `src/lib/raas_gate/license_gate_check_mixin.py` → `record_usage()`
- Used by `src/core/entitlement_enforcer.py` → `get_usage_summary()`
- Used by `src/commands/license_commands.py` → CLI reporting
- **NOT used by gateway request flow**

---

## 2. Tier Enum Duplication Table

| # | Location | Enum Name | Values | Purpose | Used By |
|---|----------|-----------|--------|---------|---------|
| 1 | `src/seed/config/tiers.py:32` | `TierKey` | `BASIC`, `PREMIUM`, `ENTERPRISE`, `MASTER`, `STARTER`, `GROWTH`, `TRIAL`, `STARTER_VN`, `GROWTH_VN`, `PRO_VN` | **Canonical** — MCU billing, Polar webhook, tier credits | `src/core/mcu_billing.py`, `src/api/billing_routes.py`, `src/api/billing_endpoints.py` |
| 2 | `engine/billing/tier_config.py:14` | `Tier` | `FREE`, `TRIAL`, `PRO`, `ENTERPRISE` | Rate limiting middleware (dormant) | `engine/billing/*.py`, `src/lib/rate_limiter_factory.py`, `src/api/tier_config_routes.py`, `src/commands/tier_admin.py` |
| 3 | `engine/license/license_metadata.py:7` | `TIER_LIMITS` (dict) | `free`, `trial`, `pro`, `enterprise` | Usage metering + license parsing | `engine/payments/usage_meter.py`, `src/lib/raas_gate/`, `src/core/entitlement_enforcer.py` |
| 4 | `src/polymarket/sdk.py` | `Tier` | `STARTER`, `PRO`, `ELITE` | Polymarket trading (unrelated) | `src/polymarket/` only |
| 5 | `src/cli/usage_types.py` | `TierInfo` (TypedDict) | — | CLI usage reporting types | `src/cli/usage_commands.py` |

**Conflict Map:**
- `TierKey.STARTER` (100 credits) ≠ `Tier.PRO` (1000 cmds/day) ≠ `TIER_LIMITS["pro"]` (1000 cmds/day)
- `TierKey.TRIAL` (50 credits) ≠ `Tier.TRIAL` (50 cmds/day, 7 days) ≠ `TIER_LIMITS["trial"]` (50 cmds/day, 7 days)
- MCU system uses UPPERCASE; Engine systems use lowercase

---

## 3. License System Map

### 3.1 Core License Gate (LIVE — Gateway Middleware)
**File:** `src/middleware/license_gate.py` (84 lines)

```python
async def license_gate(request: Request) -> str:
    # 1. Extract JWT from Authorization header
    # 2. Verify signature (JWT_SECRET)
    # 3. Check claims: tenant_id, tier, exp
    # 4. Check MCU balance > 0 via CreditStore
    # 5. Set request.state.tenant_id, license_key, tier
    # Returns: tenant_id or raises 401/402
```

**Wired in:** `src/gateway.py` — applied as FastAPI dependency on mission endpoints

### 3.2 Engine License Gate (DORMANT — Middleware Class)
**File:** `engine/license/license_gate_middleware.py` (1644 bytes)

```python
class EngineLicenseGateMiddleware:
    # Mounted in src/gateway.py:257
    app.add_middleware(EngineLicenseGateMiddleware)
```
**But:** Uses `engine.license.license_enforcer.LicenseEnforcer` → `engine.billing.tier_config.Tier`
- Checks `MEKONG_MINIMUM_TIER` env (defaults to FREE)
- Calls `enforcer.require_tier(minimum_tier, user_id)`
- **Never triggers** because `minimum_tier=FREE` by default

### 3.3 RaasLicenseGate (CLI — PARTIAL)
**Files:** `src/lib/raas_gate/license_gate_core.py`, `license_gate_check_mixin.py`, `license_gate_sync.py`

- Used by CLI commands for offline license validation
- JWT-based (RSA-signed) with embedded quotas
- Integrates with `engine.payments.usage_meter` for usage tracking
- **Not used by gateway HTTP requests**

### 3.4 License Generator (Engine)
**File:** `engine/license/jwt_license_generator.py` (14334 bytes)

- RSA key pair generation (private key ~/.mekong/keys/private.pem)
- JWT token creation with tier, quotas, expiration
- Used by: `engine/license/license_enforcer.py`, `engine/billing/tier_rate_limit_middleware.py`

---

## 4. Polar.sh Integration Trace

### 4.1 Client
**File:** `src/services/polar_client.py` (5611 bytes, ~200 lines)

```python
class PolarClient:
    - create_checkout_session(org_id, tier, email) → checkout_url
    - verify_webhook_signature(raw_body, signature, secret) → event_dict
    - parse_webhook_event(event_dict) → normalized_event
```
- Zero external deps: stdlib `urllib.request` + `hmac`
- Webhook replay protection (5-min window)

### 4.2 Webhook Handler (LIVE)
**File:** `src/api/billing_routes.py` (11117 bytes, ~300 lines)

```python
POST /v1/billing/checkout/org?org_id=<slug>   # org_admin/founder gate
POST /v1/billing/webhook/org                   # Public, signature-gated
```

**Flow:**
1. Webhook received → verify HMAC signature (POLAR_WEBHOOK_SECRET)
2. Parse event → `subscription.active` / `subscription.canceled`
3. Look up org by `metadata.org_id`
4. Call `tier_credits(tier)` from `src/seed/config/tiers` to get MCU amount
5. `mcu_billing.add_credits(tenant_id, credits)` → provisions credits
6. Log to `~/.mekong/polar_webhook.log` (mode 0600)

**Tier Mapping (billing_routes.py:174-180):**
```python
tier_key = payload.get("tier", "starter").lower()
credits = tier_credits(tier_key)  # Uses canonical TierKey
```

### 4.3 Billing Endpoints (Stripe + Polar)
**File:** `src/api/billing_endpoints.py` (864 lines, NOT 27.6K)

- **Stripe Checkout:** `/checkout/stripe` — Creates Stripe session for tier upgrade
- **Stripe Webhook:** `/webhook/stripe` — Provisions credits on `checkout.session.completed`
- **Polar Webhook:** `/webhook/polar` — Alternative Polar endpoint
- **Manual Provision:** `/provision/stripe` — Admin endpoint to grant credits by Stripe customer_id
- **Reconciliation:** `/reconcile` — Cross-check Stripe/Polar vs local MCU balances

---

## 5. Payment Integrations

### PayOS / VietQR
**Status:** **TESTS ONLY** — No production wiring

**Evidence:**
- `tests/vn/test_vn_pilot_payment.py` — imports `src.services.vietqr_recurring`
- `tests/vn/test_vietqr_webhook.py` — webhook endpoint tests
- `tests/zenos/test_vietnam_feature_regression.py` — integration tests
- **No** `src/services/vietqr_recurring.py` or similar in production code
- **No** VietQR routes in `src/api/`

### Stripe
**Status:** **LIVE** — Wired in `src/api/billing_endpoints.py`

- `src/auth/stripe_integration.py` — StripeService class
- Checkout sessions for tier upgrades
- Webhook handling with credit provisioning
- Customer portal integration

---

## 6. Which System Is "Live" vs Dormant

| Component | Status | Evidence |
|-----------|--------|----------|
| **MCU Billing (core)** | ✅ **LIVE** | Global `mcu_billing` in gateway; `license_gate` middleware checks balance on every mission request |
| **Polar.sh Webhook** | ✅ **LIVE** | `billing_router` mounted in gateway; provisions MCU credits on `subscription.active` |
| **Stripe Checkout/Webhook** | ✅ **LIVE** | Endpoints in `billing_endpoints.py` mounted; provisions credits |
| **Engine Billing Rate Limiting** | ❌ **DORMANT** | Middleware class exists but never `app.add_middleware()`; only unit tests import it |
| **Engine Payments Usage Meter** | ⚠️ **PARTIAL** | Used by CLI `RaasLicenseGate` and `entitlement_enforcer`; NOT in gateway request path |
| **Engine License Gate Middleware** | ⚠️ **MOUNTED BUT INEFFECTIVE** | Added to gateway but `MEKONG_MINIMUM_TIER` defaults to FREE → passes all requests |
| **VietQR/PayOS** | ❌ **NOT IMPLEMENTED** | Only test files reference it; no production code |
| **Core Usage Metering (src/usage)** | ✅ **LIVE** | `UsageTracker` used by CLI commands for usage reporting; SQLite at `~/.mekong/raas/tenants.db` |

---

## 7. File:Line References

### MCU Billing (LIVE)
- `src/core/mcu_billing.py:1` — MCUBilling class, MCU_COSTS, TIER_CREDITS
- `src/core/mcu_gate.py:1` — MCULockResult, MCUConfirmResult, MCURefundResult
- `src/middleware/license_gate.py:1` — license_gate dependency
- `src/gateway.py:248` — `mcu_billing = MCUBilling()`
- `src/gateway.py:255` — `app.add_middleware(RequestLoggerMiddleware)` (license_gate via Depends)

### Engine Billing (DORMANT)
- `engine/billing/tier_config.py:14` — `class Tier(Enum): FREE, TRIAL, PRO, ENTERPRISE`
- `engine/billing/tier_rate_limit_middleware.py:23` — `class TierRateLimitMiddleware`
- `engine/billing/tier_rate_limit_middleware.py:428` — `class ConfiguredMiddleware` (never used)

### Engine Payments (PARTIAL)
- `engine/payments/usage_meter.py:1` — UsageMeter class, PostgreSQL
- `engine/payments/usage_metering_service.py:1` — Full service with circuit breaker
- `engine/license/license_metadata.py:7` — TIER_LIMITS dict

### Polar.sh (LIVE)
- `src/services/polar_client.py:1` — PolarClient
- `src/api/billing_routes.py:1` — Webhook + checkout endpoints
- `src/api/billing_endpoints.py:1` — Stripe + Polar + reconciliation endpoints

### License Systems
- `src/middleware/license_gate.py:1` — Core license gate (LIVE)
- `engine/license/license_gate_middleware.py:1` — Engine gate (MOUNTED BUT INEFFECTIVE)
- `engine/license/jwt_license_generator.py:1` — JWT license generator
- `engine/license/license_enforcer.py:1` — Tier enforcement decorator
- `src/lib/raas_gate/license_gate_core.py:1` — CLI RaasLicenseGate

### Tier Configs
- `src/seed/config/tiers.py:32` — **CANONICAL** `TierKey` enum
- `engine/billing/tier_config.py:14` — `Tier` enum (rate limiting)
- `engine/license/license_metadata.py:7` — `TIER_LIMITS` dict (usage metering)

---

## 8. Critical Divergences Requiring Resolution

1. **Three Tier Vocabularies** — Canonical `TierKey` vs Engine `Tier` vs `TIER_LIMITS` dict. MCU billing uses TierKey; rate limiting uses Tier; usage metering uses string keys from TIER_LIMITS.

2. **Two License Gates on Gateway** — `src/middleware/license_gate.py` (MCU balance check) AND `engine.license.license_gate_middleware` (tier minimum check). The latter is ineffective (defaults to FREE).

3. **Two Usage Metering Systems** — `src/usage/usage_tracker.py` (SQLite, CLI) vs `engine/payments/usage_metering_service.py` (PostgreSQL, RaasLicenseGate). Different storage, different APIs.

4. **Dead Code** — `engine/billing/tier_rate_limit_middleware.ConfiguredMiddleware` never mounted; `engine/payments/usage_metering_service` not in gateway path.

---

## 9. Recommendation

**Consolidate to single source of truth:**
1. Use `src/seed/config/tiers.TierKey` as canonical tier enum everywhere
2. Remove `engine/billing/tier_config.Tier` and `engine/license/license_metadata.TIER_LIMITS`
3. Mount `engine.billing.tier_rate_limit_middleware` **or** remove it (currently dead)
4. Unify usage metering: keep `src/usage/usage_tracker` (SQLite, simpler) or migrate fully to PostgreSQL service
5. Decide on single license gate: core (MCU-aware) vs engine (tier-only)

