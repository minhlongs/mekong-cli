# Phase 01 — Fail-Closed Rail Gate for Vietnamese Orgs

- **Status:** pending
- **Violation:** L1 — a Vietnamese legal-entity tenant can select the USDT (`nowpayments`) rail
- **Files touched:** `src/raas/checkout_router.py`, `src/raas/tenant.py`, `tests/test_dual_rail_checkout.py`
- **Risk:** medium — adds a column to a user database

## Context

At HEAD `e2797d447`, `src/raas/checkout_router.py:89` selects the payment rail purely
from the request body:

```python
if req.rail.lower() == "nowpayments":
    from src.raas.nowpayments_checkout import create_invoice
```

No org jurisdiction is consulted. Any caller can put a Vietnamese legal entity on a
USDT rail, which the advisory closed as an exit-now requirement for the VN entity
under Nghị định 52/2024/NĐ-CP.

`/v1/pricing` (`src/raas/revenue_router.py:137`) and the Polar 410 payload
(`:113`) advertise `["vietqr", "nowpayments"]`, and
`tests/test_dual_rail_checkout.py` asserts those lists. Disclosure stays; the gate
lands on checkout only.

## Requirements

1. A checkout request whose org is a Vietnamese legal entity and whose rail is not
   `vietqr` is rejected.
2. An unresolvable jurisdiction is treated as Vietnamese (fail-closed on the crypto rail).
3. Non-VN orgs keep today's behaviour exactly.
4. The rejection carries a named error code plus the rails actually permitted to that org.

## Steps

1. In `src/raas/tenant.py`, add a `jurisdiction` column to the `tenants` DDL guarded
   by a `PRAGMA table_info` check, defaulting existing and new rows to `VN`. Add a
   resolver method that returns the jurisdiction for an org id or name, and a setter
   so a tenant can later be marked non-VN.
2. In `src/raas/checkout_router.py`, add `jurisdiction: Optional[str]` to
   `CheckoutRequest` (optional — never required, so existing clients are unaffected).
3. Add a module-level `resolve_org_jurisdiction(req, tenant_store)` that resolves in
   order: explicit request field, tenant row, `org_id` prefix case-insensitively equal
   to `VN`, else `VN` (fail-closed).
4. Add `rails_allowed_for_jurisdiction(juris)` returning `["vietqr"]` for `VN` and
   `["vietqr", "nowpayments"]` otherwise.
5. Before the rail branch, raise `HTTPException(403, detail={"error": "rail_not_permitted_for_jurisdiction", ...})`
   when the requested rail is not in the allowed set.
6. Keep the existing branch body and the VietQR default untouched.

## Validation

```bash
python3 -m pytest tests/test_dual_rail_checkout.py -q
```

Plus new tests, appended to that file following its existing fixture style:

- VN org + `rail="nowpayments"` → 403, error name asserted, `detail` lists allowed rails.
- org_id `"VN-acme"` with no jurisdiction field → 403 (fail-closed by prefix).
- No org at all, default `org_id="default"` → 403 (fail-closed default).
- Explicit `jurisdiction="SG"` + `rail="nowpayments"` → success, rail echoed.
- Existing `test_get_pricing_tiers` and `test_polar_webhook_is_decommissioned_http_410`
  still pass unmodified (both rails still advertised).

## Risk & Mitigation

- **Adding a column to `~/.mekong/raas/tenants.db`**: guard with `PRAGMA table_info`
  and `ALTER TABLE ... ADD COLUMN`, so an existing install upgrades in place and a
  fresh install creates the column in DDL. Back up the database before running any
  local smoke that writes.
- **existing tenants default to VN**, which blocks their crypto rail. That is the
  intended legal closure; record it in the PR description so it is a visible decision
  rather than a silent behaviour change.

## Rollback

Revert the PR. The added column is additive and harmless if left behind.
