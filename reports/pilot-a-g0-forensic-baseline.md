# Pilot A / Strategy C — Independent Forensic Re-Baseline (`G0`–`G13`)

- **Repository:** `minhlongs/mekong-cli`
- **Verified Merge Baseline (`origin/main`):** `ced4c75536bb301f8aec720626663f1c0f77bb08`
- **Merged PR:** [`#159`](https://github.com/minhlongs/mekong-cli/pull/159) (`feat/strategy-c-gateway-stategraph-misa` → `main`, closes `#157`)
- **Open Post-Merge Hardening Issue:** [`#160`](https://github.com/minhlongs/mekong-cli/issues/160) (`ai-handle`)
- **Isolated Audit & Remediation Worktree:** `/Users/macbook/mekong-cli-sc08-pilot-a` (`fix/sc08-pilot-a-security-hardening`)
- **Audit Date:** `2026-11-15` (Asia/Saigon)

---

## 1. Repository, Branch & Worktree Verification

| Check | Observed State | Evidence Command |
|---|---|---|
| **PR `#159` Merge Commit OID** | `ced4c75536bb301f8aec720626663f1c0f77bb08` (`MERGED`) | `gh pr view 159 --repo minhlongs/mekong-cli --json mergeCommit,state` |
| **`origin/main` HEAD** | `ced4c75536bb301f8aec720626663f1c0f77bb08` | `git -C /Users/macbook/mekong-cli rev-parse origin/main` |
| **User Primary Working Tree (`/Users/macbook/mekong-cli`)** | `0e0a8439ba274c8952442c98ebc1694d55dd1630` (detached HEAD + untracked user artifacts preserved untouched) | `git -C /Users/macbook/mekong-cli status --short --branch` |
| **Isolated Remediation Worktree** | `/Users/macbook/mekong-cli-sc08-pilot-a` branched cleanly at `ced4c75536bb301f8aec720626663f1c0f77bb08` | `git -C /Users/macbook/mekong-cli worktree list` |
| **GitHub Actions on `ced4c7553`** | `28` check-runs `success`, `1` (`deploy-api-staging`) `skipped` | `gh api repos/minhlongs/mekong-cli/commits/ced4c75536bb301f8aec720626663f1c0f77bb08/check-runs` |

> **Critical Forensic Observation:** Passing CI on `ced4c7553` did **not** guarantee multi-worker commercial payment safety or browser secret isolation. The baseline tests ran inside a single process (`TestClient`) with `PYTEST_CURRENT_TEST` set and without multi-worker restarts or unauthenticated polling adversaries against `GET /v1/checkout/status`.

---

## 2. Review Trail & Complete 6-Finding Post-Push Security Scan Reconstruction

### 2.1 Pre-Merge & Post-Push Evidence Sources
1. **Round-1 to Round-3 Isolated Code Review (`plans/reports/code-review-gh-157.md`):** Audited commits `81dc6d8aa` → `93224c01a` → `65f5f7acd`, resolving 16 Round-1 findings (`C-01..L-02`) and 7 Round-2 findings (`R2-C01..R2-L01`), while logging 2 Low/Informational post-merge items (NOWPayments `mk-*` `customer_email` attribution and `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` client bundle scope).
2. **Post-Push Automated Security Sweep (`2026-11-14T19:51:06.655Z` / `2026-11-15 02:51:06 ICT`):**
   - Triggered by `security-guidance v2.0.20` push-sweep hook (`review=push`, `baseline=ced4c75536bb`, `vulns_found=6`).
   - Summary emitted:
     `Push security review found 6 issues: Authentication / Authorization Bypass (Unauthenticated Webhook Forgery) in src/api/pilot_a_routes.py; Client-Side Secret Exposure (NEXT_PUBLIC_* Credential Leak) in apps/dashboard/lib/opc-cockpit-data.ts; +4 more`.
   - Because `PUSH_SWEEP_REPORT_CAP = 3` in `security_reminder_hook.py:2692`, the notification rendered the top 3 `HIGH` findings verbatim and suppressed the remaining 3 `MEDIUM`/`LOW` findings in the diff across `src/raas/checkout_router.py`, `apps/dashboard/lib/opc-cockpit-data.ts`, `src/api/pilot_a_routes.py` / `src/api/pilot_a_card_view.py`, and `src/raas/nowpayments_webhook_handler.py`.
3. **GitHub Issue `#160`:** Filed immediately after the push scan to track the post-merge remediation items.

### 2.2 Complete Six-Finding Forensic Matrix (`PS-01` – `PS-06`)

| ID | Severity | Title & Category | Affected Source (`ced4c7553`) | Reproduction Path at Baseline | Proposed Remediation |
|---|---|---|---|---|---|
| **PS-01** | **HIGH** | Unauthenticated Dev Sandbox Webhook Intake & Subject Consent Grant | `src/api/pilot_a_routes.py:296-321` | When `MEKONG_ENV != "production"`, `ZALO_OA_SECRET_KEY` is unset, `X-ZEvent-Mac` is omitted, `connector="zalo_oa_sandbox"`, and `tenant_id` has no `<slug>.tenant.json`, an unauthenticated `POST /v1/opc/pilot-a/webhook/zalo` with `grant_consent=true` creates SQLite files for `tenant_id`, records Decree 13 subject consent in `consent_log`, and consumes workflow quota. | Require `is_owner_authed` OR verified `X-ZEvent-Mac` across **all** environments by default; allow unprovisioned sandbox webhook intake **only** when `MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK=1` is explicitly set in a non-production, non-public environment, and **never** allow unauthenticated webhook requests to set `grant_consent=True`, override `service_rates_vnd`, or override `sme_tier`. |
| **PS-02** | **HIGH** | Client-Side Secret Exposure (`NEXT_PUBLIC_MEKONG_TENANT_API_KEY`) & Missing Multi-Tenant BFF | `apps/dashboard/lib/opc-cockpit-data.ts:547-559` | Setting `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` inlines the shop owner's `mk_opc_*` secret into static `.next/static/chunks/*.js`, exposing full tenant approve/reject/export authority to any browser visitor or XSS/extension reader; no server-side session or workspace-to-tenant authorization check exists. | Delete all `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` references; create Next.js Route Handlers under `apps/dashboard/app/api/opc/pilot-a/**` verifying an `HttpOnly` HMAC-SHA256 session cookie + workspace membership for the requested `tenant_id`, injecting server-only `MEKONG_TENANT_KEYS_JSON` / `MEKONG_TENANT_API_KEY`. |
| **PS-03** | **HIGH** | Volatile In-Memory Checkout State, 6-Char Tail Collision, Amount Inference & `PREMIUM` Escalation | `src/raas/checkout_router.py:115-129, 173, 221, 233-263`; `src/core/vietqr_engine.py:182-196` | (a) `_EXPECTED_CHECKOUT_AMOUNTS` is an in-process Python `dict` wiped on worker restart or missed on a second Uvicorn worker. (b) `list_transactions(limit=20)` misses older transfers and matches `order_id[-6:] in memo` (collision/spoofing). (c) On unknown `order_id` with non-catalog `amount_vnd` (e.g., `1 VND` transfer containing 6 hex chars), `tier_name` stays `CanonicalLicenseTier.PREMIUM` (`line 243`) and mints a valid `PREMIUM` license key! (d) A single bank transaction can satisfy multiple polling orders sharing a 6-char suffix. | Persist every checkout order in SQLite WAL table `checkout_orders` (`VietQrEngine`) before payment; bind settlement 1:1 atomically (`BEGIN IMMEDIATE`) by exact `order_id`, `org_id`, and `amount_vnd >= expected_amount_vnd`; remove `_EXPECTED_CHECKOUT_AMOUNTS`, `_VND_TO_SME_TIER` inference, `_VND_TO_COMMERCIAL_TIER` inference, 6-char memo matching, and `PREMIUM` default; mint and persist the license key idempotently for the exact `org_id`. |
| **PS-04** | **HIGH** | Unauthenticated License Key Disclosure & Synthetic Tenant Binding on `GET /v1/checkout/status` | `src/raas/checkout_router.py:233-263` | Any unauthenticated caller polling `GET /v1/checkout/status?order_id=<id>` retrieves the plaintext signed `RAAS_LICENSE_KEY`; furthermore, the license is signed for synthetic `org-{order_id[-6:]}` instead of the buyer's persisted `org_id`, decoupling entitlement from the paying tenant. | Issue a per-order cryptographic `checkout_secret` at `POST /v1/checkout` (storing only `checkout_secret_sha256` in `checkout_orders`); enforce `HTTP 401` on `GET /v1/checkout/status` unless caller presents valid `X-Checkout-Secret` or valid `X-API-Key` belonging to the order's `org_id`; bind `sign_license_key(tenant_id=order.org_id, ...)`. |
| **PS-05** | **MEDIUM** | Non-Cryptographic `0xdeadbeef` Pseudo-Hash Fallback, Silent Offline Approval & Signed Card URL Leakage | `apps/dashboard/lib/opc-cockpit-data.ts:479-502, 598-633, 680-689`; `apps/dashboard/app/dashboard/opc/page.tsx:321-344`; `src/api/pilot_a_routes.py:469-526`; `src/api/pilot_a_card_view.py:189-198` | (a) When `window.crypto.subtle` is absent, `computeSha256Hex` returns a deterministic 32-bit `0xdeadbeef` hash repeated 4x instead of failing closed, and `handleApproveAndSend` marks the quote `consumed`/`success` even when the Gateway is unreachable (`offline_webcrypto`). (b) `GET /v1/opc/pilot-a/card/{run_id}?sig=...` lacks `Cache-Control: no-store` and `Referrer-Policy: no-referrer`, leaving `?sig=` in browser history and potential `Referer` headers. | Fail closed in `computeSha256Hex` (use Web Crypto `crypto.subtle` or Node `crypto`, else throw `CryptoUnavailableError`) and reject approval in `page.tsx` whenever BFF/Gateway sync is not `200 OK`. Add `Cache-Control: no-store, no-cache, must-revalidate`, `Pragma: no-cache`, `Referrer-Policy: no-referrer` on `/card/{run_id}` and `/draft-export/{run_id}`, plus `history.replaceState` in card JS to scrub `sig` from the URL bar immediately after load. |
| **PS-06** | **MEDIUM** | Overseas Hosted-Invoice `mk-*` Credit Misattribution (`"mk"`) & Missing Webhook `payment_id` Replay Lock | `src/raas/nowpayments_webhook_handler.py:126-148, 194-201, 227-238` | (a) When a registered non-VN (`SG`/`US`) tenant pays a hosted `mk-<hex>` invoice where NOWPayments echoes `order_id` + `customer_email` without `tenant_id`, `_is_vn_jurisdiction_ipn` verifies the non-VN `TenantStore` row via `customer_email`, but `handle_ipn` (`line 200`) sets `workspace_id = order_id.split("-")[0] == "mk"`, crediting literal `"mk"` instead of the tenant. (b) `handle_ipn` calls `repo.add_credits()` without checking/recording `processed_events` on `payment_id`, allowing duplicate IPN callbacks to double-credit the workspace! | Resolve and return the matched non-VN `TenantStore` row `id` during jurisdiction verification and bind `workspace_id` to that exact tenant ID; enforce atomic `payment_id` replay idempotency via `CreditAccountRepository` (`processed_events` inside `BEGIN IMMEDIATE`) so duplicate IPNs grant `0` additional credits. |

---

## 3. Strategic Research Gates `G0`–`G13` — Honest Re-Classification at `ced4c7553`

Classification taxonomy enforced strictly per Supreme Command #08:
- **`PRODUCTION_VERIFIED`**: Verified with live external provider traffic & production tenant operations.
- **`INTEGRATION_VERIFIED`**: Verified end-to-end across real HTTP routes, SQLite WAL persistence, and cryptographic verifiers using synthetic fixtures (no live external network).
- **`MOCK_VERIFIED`**: Verified via unit/component harnesses with simulated transports or in-memory/partial stubs.
- **`IMPLEMENTED`**: Present in code/configuration without full runtime adversarial verification.
- **`NOT_VERIFIED`**: Not verified (or currently failing an invariant required by the gate).

| Gate | Gate Description (Strategic Research 08/11/2026) | Baseline Status (`ced4c7553`) | Forensic Justification & Exact File References |
|---|---|---|---|
| **G0** | Strategic Problem & Pilot A Wedge Lock (Zalo OA → Quote → Approval → VietQR → MISA Draft) | `INTEGRATION_VERIFIED` | Wedge implemented in `src/opc/pilot_a.py:1-184` and `src/api/pilot_a_routes.py:1-828`; tested in `tests/test_pilot_a_e2e.py` and `tests/test_strategy_c_http_gateway.py`. |
| **G1** | Neutral Core & AST Boundary (`0` country-pack / vendor SDK leaks in `src/core/` & `src/opc/`) | `INTEGRATION_VERIFIED` | Enforced via AST static checks in `tests/test_core_boundary.py:1-120` and `tests/test_opc_platform_contract.py:1-170`. |
| **G2** | Promise Spine, Durable SQLite WAL State & Checkpoint Recovery | `INTEGRATION_VERIFIED` | `src/opc/state.py`, `src/opc/state_graph.py:66-160` (`SqliteGraphCheckpointer`), verified across restarts in `src/opc/bench_layers_vn.py:67-80` (`L7`). |
| **G3** | Capability Bus, Declarative Recipe & MCP SHA-256 Allowlist Governance | `INTEGRATION_VERIFIED` | `src/opc/recipe_loader.py`, `.goose/recipes/pilot-a-zalo-lead-to-quote.yaml`, `config/mcp_manifest_allowlist.json`; verified in `tests/test_strategy_c_runtime.py`. |
| **G4** | Payload-Bound HMAC Approval, Anti-TOCTOU & Single-Use Atomic Lock | `MOCK_VERIFIED` *(Partial gap in UI)* | Backend `src/opc/approval.py` + `src/api/pilot_a_routes.py:528-717` are `INTEGRATION_VERIFIED`, **but** `apps/dashboard/lib/opc-cockpit-data.ts:492-502` still contains the `0xdeadbeef` pseudo-hash fallback and offline approval UI (`PS-05`). Target after Phase 3: `INTEGRATION_VERIFIED`. |
| **G5** | Honest Usage Accounting, Profile 4 Routing & Pre-Execution Budget Lock | `INTEGRATION_VERIFIED` | `src/opc/usage.py` + `src/opc/selective_router.py:138-174` enforce SQLite `reserve_budget` and `UNKNOWN_COST_EVENT` (`UsageStage.UNKNOWN`) without zero-coercion. |
| **G6** | Untrusted Input Quarantine Floor (VI/EN Prompt Injection & Tag Escape) | `INTEGRATION_VERIFIED` | `src/opc/quarantine.py` + `src/opc/bench_layers_vn.py:100-117` (`50/50` adversarial VI/EN corpus blocked before tool dispatch). |
| **G7** | VN Pack Hygiene, Decree 13 PII/DSAR (`<72h`) & Decree 123 `DRAFT_PENDING_TVAN` | `INTEGRATION_VERIFIED` | `src/opc/privacy_guard.py:45-155`, `src/opc/accounting_draft.py:19-160`, `src/opc/misa_export.py:38-166` enforce `<72h` erasure and block `ISSUED` status. |
| **G8** | Payment-to-License Integrity & Decree 52 Domestic Rail Enforcement | `NOT_VERIFIED` *(Fails P0 invariants at `ced4c7553`)* | Decree 52 crypto block works (`src/raas/checkout_router.py:153-168`), **but** `_EXPECTED_CHECKOUT_AMOUNTS` is volatile RAM (`line 123`), `/v1/checkout/status` leaks `license_key` unauthenticated, matches 6-char memo tails, and defaults unknown orders to `PREMIUM` (`PS-03`, `PS-04`, `PS-06`). Target after Phase 2: `INTEGRATION_VERIFIED`. |
| **G9** | `MEKONG-BENCH` 15-Layer Deterministic Evaluation Suite | `INTEGRATION_VERIFIED` | All 15 programmatic oracle layers (`L1–L5` in `src/opc/mekong_bench.py:65-131`, `L6–L15` in `src/opc/bench_layers_vn.py:25-186`) are implemented and pass offline (`15/15`). |
| **G10** | Open-Core 25-Step Catalog, `<=185 LOC` Ceiling, `189` CLI Groups & Multi-Tenant BFF Boundary | `NOT_VERIFIED` *(BFF gap at `ced4c7553`)* | LOC/CLI/catalog invariants pass, **but** `apps/dashboard/lib/opc-cockpit-data.ts:549` exposes `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` and lacks a server-side multi-tenant BFF (`PS-02`), and `pilot_a_routes.py:296-320` lacks an explicit dev sandbox opt-in flag (`PS-01`). Target after Phase 3: `INTEGRATION_VERIFIED`. |
| **G11** | Live Zalo OA Production Webhook & Official Account Onboarding | `MOCK_VERIFIED` *(Code) / `NOT_VERIFIED` (Live Prod)* | `ZaloOAConnector` (`src/opc/connectors/zalo_http.py`) verifies real Zalo `sha256(app_id + data + timestamp + secret)` MACs and 48h windows against synthetic HTTP transports (`MOCK_VERIFIED`). Live merchant Zalo OA webhook onboarding is `NOT_VERIFIED` (prohibited in this offline command; gated for invite-only pilot). |
| **G12** | Live Napas 247 / Sepay Bank Webhook Production Settlement | `MOCK_VERIFIED` *(Code) / `NOT_VERIFIED` (Live Prod)* | EMVCo CRC16-CCITT generation and HMAC-SHA256 bank webhook verification (`src/core/vietqr_engine.py`, `src/opc/accounting_draft.py`) are verified with signed synthetic payloads (`MOCK_VERIFIED`). Live bank settlement is `NOT_VERIFIED` (prohibited in this command). |
| **G13** | Paid Design-Partner Cohort Conversion (1 → 5–10 VN SMEs) | `NOT_VERIFIED` | Commercial post-launch milestone requiring founder sign-off and real customer onboarding (Phase 7 readiness report + checklist). |

---

## 4. Upstream LangGraph / LiteLLM vs. Local Compatibility Layers (Truth Matrix)

Per Phase 1 Requirement 7, exact source inspection establishes the true boundary between upstream third-party frameworks and local stdlib implementations:

1. **LangGraph (`src/opc/state_graph.py`):**
   - **Installed in local Python environment?** `importlib.util.find_spec("langgraph")` returns `True` on this machine, **but** `langgraph` is **never imported or executed** anywhere in `src/`.
   - **Actual runtime implementation (`src/opc/state_graph.py:24-160`):** `GovernedStateGraph` and `SqliteGraphCheckpointer` are **100% locally implemented pure-Python + SQLite WAL state machines** (`opc_graph_checkpoints` and `opc_side_effect_journal`). `has_langgraph_extra()` (`line 41`) only checks `find_spec("langgraph")`, and `RUNTIME_ENGINE="langgraph"` (`line 46`) selects the local `GovernedStateGraph` checkpointer path over the legacy stateless path (`src/opc/pilot_a.py:99`).
   - **Architectural assessment:** Positive for deterministic security and `<=185 LOC` Neutral Core compliance (zero third-party graph serialization vulnerabilities, atomic `BEGIN IMMEDIATE` side-effect locking), provided documentation honestly describes `GovernedStateGraph` as a **local LangGraph-style SQLite state graph** rather than claiming execution of `langgraph.graph.StateGraph`.

2. **LiteLLM (`src/opc/selective_router.py` & `config/litellm_proxy.yaml`):**
   - **Installed in local Python environment?** `importlib.util.find_spec("litellm")` returns `False`; `litellm` SDK is **not imported** in `src/opc/`.
   - **Actual runtime implementation (`src/opc/selective_router.py:113-175`):**
     - **Tier 1 (Primary):** Pure-Python deterministic regex/offset extractor (`extract_deterministic_citations`, `0 VND`, `<1 ms`).
     - **Tier 2 (`MLX_BASE_URL` / `LITELLM_BASE_URL`):** Standard-library `urllib.request` HTTP `POST` client speaking the OpenAI Chat Completions JSON wire format (`{"model": ..., "messages": ...}`) with a hard `1.5s` deadline (`timeout_ms * 0.92`) to an external MLX server or an externally deployed LiteLLM Proxy configured via `config/litellm_proxy.yaml:1-47`.
     - **Tier 3 (`cloud_fallback_fn`):** Injectable Python callable gated by SQLite `UsageLedger.reserve_budget()` (`fail_closed_budget_enforcement=True`) and `UNKNOWN_COST_EVENT` tracking.
   - **Cost Tracker (`src/core/cost_tracker.py:10-165`):** Local Python cost calculator modeled after LiteLLM's pricing schema, not importing `litellm`.
   - **Architectural assessment:** Clean out-of-process proxy seam — `SelectiveRouter` integrates with an external LiteLLM Proxy over HTTP when `LITELLM_BASE_URL` is pointed at a running proxy container, while keeping zero `litellm` Python package bloat inside the CLI/Gateway process.
