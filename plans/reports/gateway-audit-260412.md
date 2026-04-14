# Gateway & RaaS Billing Audit — 2026-04-12

## Checkout Flow Scope
`POST /v1/checkout` → Polar pays → `POST /webhook/polar` → tenant + 200 credits → API key → missions

---

## BUGS FOUND

### BUG-01: Wrong Polar Webhook Signature Header — CRITICAL
**File:** `src/raas/revenue_router.py:121`
**Severity:** CRITICAL — all production webhooks rejected (401), zero tenants provisioned

```python
# Current (WRONG):
signature = request.headers.get("webhook-signature", "")

# Polar.sh actually sends: "webhook-signature" (Svix-based) OR "X-Polar-Signature"
# The sister file src/api/polar_webhook.py:275 uses X-Polar-Signature and expects "sha256=" prefix
```

The `revenue_router.py` webhook reads `webhook-signature` as a raw hex string and directly compares against `hmac.new(...).hexdigest()`.

The more complete implementation in `src/api/polar_webhook.py` reads `X-Polar-Signature`, strips `sha256=` prefix, and validates timestamp. The two implementations are inconsistent.

**Polar's actual header** per their Svix-based webhook system is `webhook-signature` with format `v1,<base64>` (not hex). The raw HMAC hex compare will ALWAYS fail in production.

**Fix:** Use the `polar_webhook` approach with `X-Polar-Signature` + `sha256=` prefix stripping, OR verify Polar's exact header format from dashboard and align both files.

---

### BUG-02: Credit Resolution in Webhook Uses Name-in-Product-ID String Match — HIGH
**File:** `src/raas/revenue_router.py:143-145`
**Severity:** HIGH — wrong tier gets 0 credits; customer pays but gets nothing

```python
for key, amount in CREDIT_MAP.items():
    if key in product_id.lower():  # key = "starter"/"growth"/"pro"
        credits = amount
        break
```

Polar `product_id` is a UUID (e.g. `"a09a5fa0-63db-42a4-a547-3b1523ffc263"`). The string `"starter"` will NEVER appear in a UUID. `credits` stays 0, block at `if credits and customer_email:` is skipped — tenant gets 0 credits.

**Fix:** Map by price/product UUID. Match `product_id` against `_POLAR_PRICE_DEFAULTS` values, or pass tier in Polar metadata and use `data.get("metadata", {}).get("tier")`.

```python
# Quick fix:
PRODUCT_ID_TO_TIER = {v: k for k, v in _POLAR_PRICE_DEFAULTS.items()}
tier = PRODUCT_ID_TO_TIER.get(product_id)
credits = CREDIT_MAP.get(tier, 0) if tier else 0
```

---

### BUG-03: polar_webhook_handler.py — FK Reference to Non-Existent Table in Same DB — HIGH
**File:** `src/raas/polar_webhook_handler.py:87`
**Severity:** HIGH — `PolarSubscriptionRepository._init_db()` crashes on first call; startup ImportError chain fails

```sql
-- workspaces.db is opened, but workspaces table is defined in workspace_repository.py
-- and never created in this DB file:
workspace_id TEXT PRIMARY KEY REFERENCES workspaces(id) ON DELETE CASCADE,
```

`polar_webhook_handler.py` opens `~/.mekong/raas/workspaces.db` and creates `polar_subscriptions` with a FK to `workspaces(id)`. The `workspaces` table is only created by `workspace_repository.py` in the same DB. If `PolarSubscriptionRepository` is initialized before `WorkspaceRepository`, SQLite FK enforcement will fail on insert even if FK pragma is off (the schema CREATE itself will succeed, but INSERTs will violate integrity when pragma is ON).

**Fix:** Either ensure `WorkspaceRepository._init_db()` is called first in app startup, or drop the FK constraint and enforce at application layer.

---

### BUG-04: polar_webhook_handler.py — Calls Private `_now_iso` on CreditAccountRepository — MEDIUM
**File:** `src/raas/polar_webhook_handler.py:375, 395`
**Severity:** MEDIUM — AttributeError at runtime when subscription is updated/cancelled

```python
existing.updated_at = self._credit_repo._now_iso()  # _now_iso is @staticmethod but accessed via private convention
```

`_now_iso` is defined as `@staticmethod` on `CreditAccountRepository`. Calling it via `self._credit_repo._now_iso()` works in Python (static methods can be called on instances), but it's accessing a private method on a different class — fragile and will break if `CreditAccountRepository` renames it. `PolarSubscriptionRepository` already defines its own `_now_iso` at line 105.

**Fix:** Use `self._subscription_repo._now_iso()` or `datetime.now(timezone.utc).isoformat()` directly.

---

### BUG-05: CORS — `mekongmind.pages.dev` Not in Default Allowed Origins — HIGH
**File:** `src/gateway.py:81-88`
**Severity:** HIGH — landing page → checkout POST blocked by browser CORS

```python
_ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in _os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8080",  # ← missing mekongmind.pages.dev
    ).split(",")
    ...
]
```

Default fallback only allows localhost. If `CORS_ALLOWED_ORIGINS` env var is not set in production, browser preflight to `POST /v1/checkout` will fail.

**Fix:** Add production domains to default, or ensure env var is always set:
```python
"http://localhost:3000,http://localhost:8080,https://mekongmind.pages.dev,https://mekongmind.com"
```

---

### BUG-06: MCUBilling is In-Memory — Resets on Every Restart — HIGH
**File:** `src/gateway.py:177`, `src/core/mcu_billing.py:112-126`
**Severity:** HIGH — credits provisioned via webhook (SQLite `CreditStore`) are NOT used by `MCUBilling`

```python
# gateway.py mounts this singleton:
mcu_billing = MCUBilling()  # pure in-memory dict

# But webhook/polar provisions credits via:
credit_store = CreditStore()  # SQLite tenants.db
```

Two separate credit stores — customer pays, gets credits in SQLite `CreditStore`, but mission deductions go against `MCUBilling._tenants` (memory). Any restart wipes `MCUBilling`. Tenant always has 0 balance in `MCUBilling` → all missions fail with "Insufficient MCU".

**Fix:** `MCUBilling.deduct()` must delegate to `CreditStore`, not internal dict. The `/raas/missions` router already correctly uses `CreditStore` via `MissionLifecycle`. The `/v1/mcu/deduct` endpoint uses the wrong store.

---

### BUG-07: Checkout URL Structure — Missing Polar Organisation Slug — MEDIUM
**File:** `src/raas/revenue_router.py:66-71`
**Severity:** MEDIUM — checkout URL 404s if default base URL is wrong

```python
def _polar_checkout_base() -> str:
    return os.environ.get(
        "POLAR_CHECKOUT_BASE",
        "https://polar.sh/longtho638-jpg/mekong-cli/subscriptions",  # hardcoded org/repo
    )
```

Default hardcodes `longtho638-jpg/mekong-cli`. If the Polar organisation slug differs from the actual account, all checkout URLs 404. Must be overridden via `POLAR_CHECKOUT_BASE` env var or the default must match production.

---

### BUG-08: /v1/success HMAC Verification Silently Falls Back — LOW/MEDIUM
**File:** `src/raas/checkout_router.py:115-133`
**Severity:** MEDIUM — unauthenticated actors can probe endpoint without provisioning; misleading response

When sig is invalid (tampered redirect), the endpoint returns `api_key="pending_webhook_verification"` instead of a 400/401. This is intentional per comment, but means a user with a tampered redirect gets a misleading "pending" response with no path to resolution. Not a security hole (no real provisioning), but bad UX.

---

### BUG-09: `find_by_email` Uses `name` Column, Not an Email Column — LOW
**File:** `src/raas/tenant.py:179-192`
**Severity:** LOW — functional but fragile; name collision if two tenants have same name

`TenantStore.create_tenant(name=email)` stores email in `name` field. `find_by_email` queries `WHERE name = ?`. No `UNIQUE` constraint on `name` in schema. Two signups with same email could create duplicate tenants.

**Fix:** Add `UNIQUE` constraint on `name`, or add an `email` column with `UNIQUE`.

---

## MISSING ENV VARS (crash-risk on startup)

| Var | Used in | Effect if missing |
|-----|---------|-------------------|
| `POLAR_WEBHOOK_SECRET` | `revenue_router.py:122` | HTTP 500 on every webhook (hard error) |
| `CORS_ALLOWED_ORIGINS` | `gateway.py:84` | Falls back to localhost-only; production CORS breaks |
| `APP_BASE_URL` | `checkout_router.py:74` | Falls back to `mekongmind.com`; OK if that's prod |
| `POLAR_CHECKOUT_BASE` | `revenue_router.py:68` | Falls back to hardcoded slug (BUG-07) |

`POLAR_WEBHOOK_SECRET` missing → hard 500 on ALL webhook calls → zero provisioning.

---

## SUMMARY TABLE

| # | File | Severity | Flow Step Broken | Fix Complexity |
|---|------|----------|-----------------|----------------|
| 01 | revenue_router.py:121 | CRITICAL | Step 4 — webhook sig rejected | Medium |
| 02 | revenue_router.py:143 | HIGH | Step 5 — 0 credits granted | Easy |
| 05 | gateway.py:84 | HIGH | Step 2 — CORS blocks checkout | Easy |
| 06 | gateway.py:177 + mcu_billing.py | HIGH | Step 6 — missions always fail | Hard |
| 03 | polar_webhook_handler.py:87 | HIGH | Step 4 — DB init crash | Easy |
| 07 | revenue_router.py:68 | MEDIUM | Step 2 — 404 checkout URL | Easy |
| 04 | polar_webhook_handler.py:375 | MEDIUM | Step 4 — cancelled sub crash | Easy |
| 08 | checkout_router.py:115 | MEDIUM | Step 5 — misleading UX | Low |
| 09 | tenant.py:179 | LOW | Step 5 — duplicate tenants | Easy |

## Recommended Fix Order
1. BUG-02 (0 credits) — immediate revenue loss
2. BUG-01 (wrong sig header) — must verify Polar's actual header format
3. BUG-05 (CORS) — set env var in production
4. BUG-06 (split credit stores) — architectural; route `/v1/mcu/deduct` to `CreditStore`
5. BUG-03 (FK crash) — fix DB init order or drop FK
6. BUG-07 (hardcoded slug) — verify/update default

## Unresolved Questions
- What exact `webhook-signature` format does the production Polar account send? (Svix `v1,<base64>` or `sha256=<hex>`?) — need to check Polar dashboard webhook logs.
- Is `polar_webhook_handler.py` (workspace-based) actually wired into `POST /webhook/polar`? Currently `revenue_router.py` handles that route directly without using `PolarWebhookHandler`. The handler class exists but may be dead code.
- `MCUBilling` vs `CreditStore` — which is the authoritative store? `/raas/missions` uses `CreditStore`, `/v1/mcu/deduct` uses `MCUBilling`. Need alignment decision.
