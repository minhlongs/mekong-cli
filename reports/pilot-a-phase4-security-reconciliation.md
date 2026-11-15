# Pilot A / Strategy C — Phase 4 Security Findings Reconciliation (`PS-01` – `PS-06`)

- **Repository:** `minhlongs/mekong-cli`
- **Baseline Audited:** `ced4c75536bb301f8aec720626663f1c0f77bb08` (PR `#159` merge commit)
- **Remediation Branch:** `fix/sc08-pilot-a-security-hardening` (Issue `#160`)
- **Date:** `2026-11-15` (Asia/Saigon)

All **six** findings from the post-push security sweep (`security-guidance v2.0.20`, `2026-11-14T19:51:06Z`, `vulns_found=6`) have been reconciled with source-level evidence, minimal corrective patches, and executable regression tests. Zero findings were dismissed as dev-only.

---

## Summary Table

| ID | Severity | Finding | Classification | Corrective Patch | Regression Test | Post-Fix Status |
|---|---|---|---|---|---|---|
| **PS-01** | **HIGH** | Unauthenticated Dev Sandbox Webhook Intake & Subject Consent Grant | **CONFIRMED VULNERABILITY** | `src/api/pilot_a_routes.py:116-127, 391-445` | `tests/test_sc08_auth_tenant_isolation.py::test_dev_sandbox_webhook_opt_in_gate_and_privileged_fields_forbidden` | **REMEDIATED (`0` bypasses)** |
| **PS-02** | **HIGH** | Client-Side Secret Exposure (`NEXT_PUBLIC_MEKONG_TENANT_API_KEY`) & Missing BFF | **CONFIRMED VULNERABILITY** | `apps/dashboard/lib/opc-bff-auth.ts`, `apps/dashboard/app/api/opc/pilot-a/**`, `apps/dashboard/lib/opc-cockpit-data.ts` | `tests/test_sc08_dashboard_bff.py` (`9` tests) | **REMEDIATED (`0` client secrets)** |
| **PS-03** | **HIGH** | Volatile In-Memory Checkout State, 6-Char Tail Collision, Amount Inference & `PREMIUM` Default | **CONFIRMED VULNERABILITY** | `src/core/vietqr_engine.py:197-776`, `src/raas/checkout_router.py:239-435` | `tests/test_sc08_payment_integrity.py` (`tests 1, 3..9`) | **REMEDIATED (`0` unauthorized licenses)** |
| **PS-04** | **HIGH** | Unauthenticated License Disclosure & Synthetic `org-<tail>` Binding on `/v1/checkout/status` | **CONFIRMED VULNERABILITY** | `src/raas/checkout_router.py:132-206, 378-466` | `tests/test_sc08_payment_integrity.py::test_2_caller_authorization_matrix_on_checkout_status` | **REMEDIATED (`HTTP 401` fail-closed)** |
| **PS-05** | **MEDIUM** | Non-Cryptographic `0xdeadbeef` Pseudo-Hash Fallback, Silent Offline Approval & Signed Card URL Leakage | **CONFIRMED VULNERABILITY** | `apps/dashboard/lib/opc-cockpit-data.ts`, `apps/dashboard/app/dashboard/opc/page.tsx`, `src/api/pilot_a_routes.py:110-145, 505-565`, `src/api/pilot_a_card_view.py:155-208` | `tests/test_sc08_dashboard_bff.py::test_compute_sha256_fails_closed_without_subtle_crypto`, `tests/test_sc08_auth_tenant_isolation.py::test_signed_card_url_leakage_headers_csp_history_scrub_and_x_card_sig` | **REMEDIATED (`fail-closed` + `no-store`/`no-referrer`)** |
| **PS-06** | **MEDIUM** | Overseas Hosted-Invoice `mk-*` Credit Misattribution (`"mk"`) & Webhook `payment_id` Replay | **CONFIRMED VULNERABILITY** | `src/raas/nowpayments_webhook_handler.py:83-195, 290-375`, `src/raas/credit_account_repository.py:232-315` | `tests/test_sc08_payment_integrity.py::test_10_nowpayments_overseas_mk_customer_email_attribution_and_replay_lock` | **REMEDIATED (`1x` exact tenant grant)** |

---

## Detailed Finding Reconciliation

### `PS-01` — Unauthenticated Dev Sandbox Webhook Intake & Subject Consent Grant
- **Severity:** `HIGH`
- **Reproducible Test (Before):** Sending an unauthenticated `POST /v1/opc/pilot-a/webhook/zalo` with `{"tenant_id": "unprov_x", "connector": "zalo_oa_sandbox", "grant_consent": true, ...}` when `MEKONG_ENV=development` and `ZALO_OA_SECRET_KEY` was unset created `unprov_x.db`, recorded Decree 13 subject consent in `consent_log`, and reserved workflow quota without any signature or API key.
- **Root Cause:** `src/api/pilot_a_routes.py:296-320` (at `ced4c7553`) left an implicit fallback open when `tenant_cfg is None`, `not _is_production()`, and `not has_zalo_secret`, and evaluated `allow_grant_consent` as `True` on that path.
- **Confirmed Impact:** Arbitrary unauthenticated callers on non-production deployments could forge customer consent records, exhaust disk/SQLite files with ghost tenants, or override `sme_tier`.
- **Minimal Corrective Patch:**
  - Added `_is_public_or_production()` (`production`, `staging`, `public`, or `MEKONG_PUBLIC_GATEWAY=1`) and `_allow_dev_sandbox_webhook()` requiring explicit `MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK=1` (`src/api/pilot_a_routes.py:116-127`).
  - Unconditionally blocked `grant_consent=True`, `service_rates_vnd != None`, and `sme_tier != "pilot_a"` (`HTTP 403 privileged_webhook_fields_forbidden`) for all unauthenticated callers across **all** environments (`src/api/pilot_a_routes.py:402-415`).
  - Enforced pre-workflow tenant existence checks on `/runs`, `/card`, `/decide`, `/webhook/vietqr`, and `/draft-export` so unauthorized probes create `0` SQLite files on disk (`src/api/pilot_a_routes.py:203-229`).
- **Regression Test:** `tests/test_sc08_auth_tenant_isolation.py::test_dev_sandbox_webhook_opt_in_gate_and_privileged_fields_forbidden` and `test_ghost_unprovisioned_tenant_probes_never_create_sqlite_files` (`PASSED`).
- **Residual Risk:** Low — operators running local unauthenticated sandbox demos must explicitly export `MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK=1`, which is automatically ignored if `MEKONG_ENV` is `production`/`staging`/`public` or `MEKONG_PUBLIC_GATEWAY=1`.

---

### `PS-02` — Client-Side Secret Exposure (`NEXT_PUBLIC_MEKONG_TENANT_API_KEY`) & Missing Multi-Tenant BFF
- **Severity:** `HIGH`
- **Reproducible Test (Before):** Setting `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` during `next build` inlined the raw `mk_opc_*` tenant secret into `.next/static/chunks/*.js` (`apps/dashboard/lib/opc-cockpit-data.ts:549`).
- **Root Cause:** Direct browser-to-Gateway calls injected `X-API-Key` from a `NEXT_PUBLIC_*` build-time environment variable without server-side session or workspace-to-tenant membership checks.
- **Confirmed Impact:** Full tenant impersonation (`approve`, `reject`, `draft-export`) if `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` was populated in any shared or hosted Dashboard build.
- **Minimal Corrective Patch:**
  - Removed all `NEXT_PUBLIC_MEKONG_*` references from `apps/dashboard/lib/opc-cockpit-data.ts` and `apps/dashboard/.env.local.example`.
  - Implemented `apps/dashboard/lib/opc-bff-auth.ts` + 5 Next.js App Router BFF endpoints (`apps/dashboard/app/api/opc/pilot-a/{session,webhook/zalo,decide,runs/[runId],draft-export/[runId]}/route.ts`) enforcing `HttpOnly; SameSite=Strict` HMAC-SHA256 `mk_opc_session` cookies, workspace-to-tenant authorization (`403 cross_tenant_forbidden`), hierarchical RBAC (`owner` > `operator` > `viewer`), CSRF `Origin` validation, server-only `MEKONG_TENANT_KEYS_JSON` lookup, and response scrubbing of `card_sig`/`sig=`/`mk_opc_*`.
- **Regression Test:** `tests/test_sc08_dashboard_bff.py` (`9/9 PASSED`) + canary `next build` chunk inspection (`0` hits in `.next/static/`).
- **Residual Risk:** Low — session revocation prior to the 8-hour cookie TTL relies on `DELETE /api/opc/pilot-a/session` or rotating `MEKONG_DASHBOARD_SESSION_SECRET` (appropriate for single-VPS Pilot A cohort; server-side session revocation list can be added if multi-admin team churn increases).

---

### `PS-03` — Volatile In-Memory Checkout State, 6-Char Tail Collision, Amount Inference & `PREMIUM` Default
- **Severity:** `HIGH`
- **Reproducible Test (Before):** Creating an order on worker 1 (or restarting the process so `_EXPECTED_CHECKOUT_AMOUNTS` was empty) and recording a `1 VND` bank transfer whose memo contained `order_id[-6:]` caused `GET /v1/checkout/status` to fall through to `tier_name = CanonicalLicenseTier.PREMIUM` (`src/raas/checkout_router.py:243`) and issue a valid `PREMIUM` license key; furthermore, a single transfer satisfied multiple orders sharing a 6-character suffix.
- **Root Cause:** Expectations were stored in a module-level Python `dict` (`_EXPECTED_CHECKOUT_AMOUNTS`), transactions were scanned via `list_transactions(limit=20)` with substring matching `order_id[-6:] in memo`, and unknown orders fell back to amount-based tier inference or `CanonicalLicenseTier.PREMIUM`.
- **Confirmed Impact:** Critical financial integrity failure — underpayment, partial-memo collision, cross-order double-spending of one bank transfer, and `PREMIUM` tier escalation across worker restarts.
- **Minimal Corrective Patch:**
  - Added durable SQLite WAL `checkout_orders` table (`settled_bank_tx_id TEXT UNIQUE`) and `BEGIN IMMEDIATE` atomic 1:1 settlement in `src/core/vietqr_engine.py:197-776`.
  - Removed `_EXPECTED_CHECKOUT_AMOUNTS`, `_VND_TO_SME_TIER`, `_VND_TO_COMMERCIAL_TIER`, `mk-paid-*` magic prefixes, 6-char memo truncation, and `PREMIUM` default from `src/raas/checkout_router.py`.
  - Enforced `HTTP 403 simulation_forbidden_in_production` when `MEKONG_ENV=production` even if `PYTEST_CURRENT_TEST` is set.
- **Regression Test:** `tests/test_sc08_payment_integrity.py` (`10/10 PASSED`, covering unknown orders, 6-char collisions, multi-order memos, `expected - 1` underpayments, `bank_tx_id` replay, `>25` newer transactions across worker restarts, 8-thread concurrency races, and production simulation rejection).
- **Residual Risk:** Minimal — domestic bank settlement requires exact `order_id` token in the transfer memo (pre-populated in the dynamic EMVCo Tag 62 Subtag 08 QR payload); manual customer typos omitting the order ID remain `pending` fail-closed for human reconciliation rather than guessing.

---

### `PS-04` — Unauthenticated License Key Disclosure & Synthetic Tenant Binding on `GET /v1/checkout/status`
- **Severity:** `HIGH`
- **Reproducible Test (Before):** Any unauthenticated `GET /v1/checkout/status?order_id=<id>` returned the signed `RAAS_LICENSE_KEY` in plaintext, bound to synthetic `org-{order_id[-6:]}` instead of the buyer's organization.
- **Root Cause:** `get_checkout_status` had zero caller authentication and synthesized `tenant_id=f"org-{order_id[-6:]}"`.
- **Confirmed Impact:** Credential theft by anyone observing or guessing an `order_id`, plus entitlement drift away from the paying `org_id`.
- **Minimal Corrective Patch:**
  - `POST /v1/checkout` now generates cryptographic `checkout_secret = chk_<random>` (persisting only `checkout_secret_sha256` in `checkout_orders`) and normalizes `org_id`.
  - `GET /v1/checkout/status` enforces `HTTP 401 unauthorized_checkout_status` unless the caller presents a constant-time verified `X-Checkout-Secret` or the owning tenant's `X-API-Key` / `Bearer` token (`src/raas/checkout_router.py:175-206, 378-435`).
  - `sign_license_key` and `POST /v1/license/activate` bind deterministically and idempotently to the persisted `order["org_id"]`.
  - Updated `apps/dashboard/lib/agentops-api.ts` and `apps/dashboard/app/checkout/demo/page.tsx` to pass `X-Checkout-Secret` and keep keys out of `window.localStorage`.
- **Regression Test:** `tests/test_sc08_payment_integrity.py::test_2_caller_authorization_matrix_on_checkout_status` and `tests/test_dual_rail_checkout.py` (`PASSED`).
- **Residual Risk:** Low — callers must retain `checkout_secret` across page reloads if polling without a tenant `X-API-Key`.

---

### `PS-05` — Non-Cryptographic `0xdeadbeef` Pseudo-Hash Fallback, Silent Offline Approval & Signed Card URL Leakage
- **Severity:** `MEDIUM`
- **Reproducible Test (Before):**
  1. When `window.crypto.subtle` was absent, `computeSha256Hex` in `apps/dashboard/lib/opc-cockpit-data.ts:492-502` returned a 32-bit `0xdeadbeef` hash repeated 4x, and `page.tsx:321-343` marked the approval `consumed`/`success` even when Gateway fetch threw a network error.
  2. `GET /v1/opc/pilot-a/card/{run_id}?sig=...` lacked `Cache-Control: no-store` and `Referrer-Policy: no-referrer` and embedded `?sig=` inside `<a href>` download links.
- **Root Cause:** Demo-era offline fallback left in cryptographic authorization UI, and missing HTTP anti-leakage headers / URL scrubbing on mobile card HTML.
- **Confirmed Impact:** Misleading UI state on degraded/non-HTTPS contexts and potential `sig` capability token retention in browser history, proxy caches, or `Referer` headers.
- **Minimal Corrective Patch:**
  - `computeSha256Hex` now requires `crypto.subtle.digest('SHA-256', ...)` and throws `CRYPTO_UNAVAILABLE` otherwise; `page.tsx` fails closed (`approvalState = 'idle'`, `tamper_detected`) on any crypto error or non-2xx/network BFF error.
  - Added `Cache-Control: no-store, no-cache, must-revalidate, private`, `Pragma: no-cache`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and strict `Content-Security-Policy` on `/card/{run_id}`, plus `<meta name='referrer' content='no-referrer'>`, immediate `window.history.replaceState` scrubbing of `sig`, and `X-Card-Sig` header transport (`src/api/pilot_a_routes.py:110-145`, `src/api/pilot_a_card_view.py:155-208`).
- **Regression Test:** `tests/test_sc08_dashboard_bff.py::test_compute_sha256_fails_closed_without_subtle_crypto_and_client_helpers_fail_closed` and `tests/test_sc08_auth_tenant_isolation.py::test_signed_card_url_leakage_headers_csp_history_scrub_and_x_card_sig` (`PASSED`).
- **Residual Risk:** Low —shop owners opening `/card/{run_id}` must have JavaScript enabled (already required for the 1-tap `fetch('/v1/opc/pilot-a/decide')` button).

---

### `PS-06` — Overseas Hosted-Invoice `mk-*` Credit Misattribution (`"mk"`) & Webhook `payment_id` Replay
- **Severity:** `MEDIUM`
- **Reproducible Test (Before):**
  1. Registered `SG` tenant created via email `ops@sg.example` paid a `mk-<hex>` NOWPayments invoice echoing `order_id` + `customer_email` (without `tenant_id`): `_is_vn_jurisdiction_ipn` passed, but `workspace_id` resolved to `"mk"` (`src/raas/nowpayments_webhook_handler.py:200`).
  2. Delivering the same `finished` IPN twice granted `2x` credits because `processed_events` was never checked in `handle_ipn`.
- **Root Cause:** Jurisdiction verification discarded the matched `TenantStore` row instead of returning its canonical ID, and `handle_ipn` called non-idempotent `repo.add_credits()`.
- **Confirmed Impact:** Lost customer credits on legitimate overseas hosted invoices (credited to `"mk"`) and 2x+ credit inflation on webhook retries/replays.
- **Minimal Corrective Patch:**
  - Implemented `_resolve_ipn_tenant_and_vn_flag` in `src/raas/nowpayments_webhook_handler.py` binding overseas `mk-*` invoices via persisted `checkout_orders` or `TenantStore` (`customer_email` / `explicit_ws`) directly to the verified non-VN tenant (`"mk"` receives `0`), plus underpayment rejection (`price_amount < expected_amount_usd`) and missing-`payment_id` rejection.
  - Added `CreditAccountRepository.grant_event_credits_once` (`src/raas/credit_account_repository.py`) using `BEGIN IMMEDIATE` over `processed_events`, `credit_accounts`, and `credit_transactions`.
- **Regression Test:** `tests/test_sc08_payment_integrity.py::test_10_nowpayments_overseas_mk_customer_email_attribution_and_replay_lock`, `tests/test_sc08_payment_integrity.py::test_nowpayments_ipn_secret_required_master_tier_credits_and_deferred_license_retry`, and `tests/test_strategy_c_legal_pricing.py` (`PASSED`).
- **Residual Risk:** Minimal — Decree 52 domestic VN exclusion remains fail-closed (`HTTP 403`) across all VN signals and unattributed `mk-*` payloads.

---

## Post-Implementation Adversarial Self-Audit Hardening (5 Additional Edge Defects Closed)

During the post-implementation adversarial sweep, five additional subtle edge cases were uncovered via live probe execution and immediately remediated with regression tests (`153/153` passing across all SC08, billing, Open-Core, and UI contract suites):

1. **Unsigned NOWPayments IPN Fail-Closed Across All Environments (`src/raas/nowpayments_webhook_handler.py:59-68, 253-263`, `src/raas/nowpayments_router.py:58-62`):** Previously, missing `NOWPAYMENTS_IPN_SECRET` only failed closed when `MEKONG_ENV=production` (allowing unsigned IPNs in `staging`/`development`), and omitting `price_amount` skipped underpayment verification. Now `NOWPAYMENTS_IPN_SECRET` is required in **all** environments (`HTTP 503` `ipn_secret_unconfigured`) unless `MEKONG_ALLOW_UNSIGNED_IPN=1` is explicitly opted in, and persisted orders require explicit `price_amount` + `price_currency == "usd"`.
2. **Canonical Tier Priority & `MASTER`/`PREMIUM`/`BASIC` Credit Mapping (`src/raas/nowpayments_webhook_handler.py:88-96, 349-353`):** Persisted `checkout_orders.canonical_tier` now always takes precedence over untrusted webhook `order_description` strings, and `_extract_tier` includes `basic`, `premium`, and `master` (preventing `$4,999 MASTER` invoices from falling back to `starter` `1,500` credits).
3. **Retry-Safe NOWPayments License Settlement Recovery (`src/raas/nowpayments_webhook_handler.py:369-385`, `src/raas/nowpayments_router.py:58-62`):** Previously, if `grant_event_credits_once` succeeded and `settle_external_order_atomic` threw a transient error, the exception was logged and swallowed (`HTTP 200`), permanently stranding `checkout_orders` in `pending` on subsequent replays. Now settlement exceptions propagate `retryable: True` (`HTTP 503`), and replays with `granted == False` still execute idempotent `settle_external_order_atomic` without double-granting credits.
4. **Zalo Webhook Timestamp Freshness (`300s`) & Canonical `card_sig` Derivation (`src/api/pilot_a_routes.py:372-383, 560-585`):** Enforced a `±300s` replay window on `X-ZEvent-Mac` timestamps before touching tenant stores, and ensured `/runs/{run_id}` and `/card/{run_id}` derive `card_sig` strictly from server-side `_sign_card_url` rather than echoing query-string `?sig=` when authenticated via `X-API-Key`.
5. **Empty `MEKONG_WORKSPACE_TENANTS_JSON={}` Handling (`apps/dashboard/lib/opc-bff-auth.ts:116-120`):** Treated `{}` (the `.env.local.example` placeholder) identically to unset (`null`) so operators copying `.env.local.example` verbatim are not locked out of BFF login.

