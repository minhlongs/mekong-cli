# Code Review Report — GH-157 (`feat/strategy-c-gateway-stategraph-misa`)

- **Branch Audited:** `feat/strategy-c-gateway-stategraph-misa` (`65f5f7acdfe057af67629aa5dfab373c8e0f255c` Round-3 / `93224c01a` Round-2 / `81dc6d8aa` Round-1) vs `origin/main` (`fcc565289`)
- **Issue:** `#157` — Strategy C StateGraph, Profile 4 Router, Pilot A HTTP/Card & Legal Fourth-Door Closure
- **Scope:**
  - Overall branch (`origin/main...HEAD`): 41 changed files (`+5,172` / `-589` LOC) across `src/opc/`, `src/api/`, `src/raas/`, `src/cli/`, `src/middleware/`, `apps/dashboard/`, `.goose/recipes/`, `config/`, `dna/`, `.github/workflows/gates.yml`, `plans/`, and `tests/`
  - Round-3 delta (`93224c01a..65f5f7acd`): 13 changed files (`+313` / `-256` LOC)
- **Round-1 Verdict (`81dc6d8aa`):** `BLOCKED` (3 Critical, 6 High, 5 Medium, 2 Low)
- **Round-2 Verdict (`93224c01a`):** `BLOCKED` (1 Critical, 2 High, 3 Medium, 1 Low)
- **Round-3 Verdict (`65f5f7acd`):** **`APPROVED FOR PR / MERGE` (0 Critical, 0 High, 0 Medium, 2 Low/Informational non-blocking notes)** — All 7 Round-2 findings (`R2-C01`, `R2-H01`, `R2-H02`, `R2-M01`, `R2-M02`, `R2-M03`, `R2-L01`) and all 16 original Round-1 findings (`C-01..L-02`) are resolved and empirically verified.

---

## Round-3 Hard Invariants Verification (`65f5f7acd` — ALL PASSING)

- **LOC Ceiling (`<= 185 LOC`):** **PASS** — Verified across all 46 governed files:
  - 24 `src/opc/**/*.py` modules (max `185` LOC in `src/opc/connectors/zalo_http.py` and `src/opc/bench_layers_vn.py`)
  - 13 `src/core/opencore/**/*.py` + `src/core/raas_license_verifier.py` modules (max `169` LOC in `src/core/raas_license_verifier.py`)
  - 9 `tests/test_opc_*.py` + `tests/test_strategy_*.py` files (max `179` LOC in `tests/test_opc_approval_security.py`)
  - Zero violations (`violations=[]`).
- **Neutral Core AST Boundary:** **PASS** — Zero forbidden country-pack AST imports (`thue_dnvn`, `ke_toan`, `zalo_oa`, `zalo_engine`, `tt78`) across all 24 `src/opc/**/*.py` files.
- **Byte-for-Byte Protected Files:** **PASS** — `git diff --exit-code origin/main...HEAD -- src/core/opencore/phase_559_opencore_25_step_catalog.py .mekong/company.json` returned exit code `0` (0 bytes changed).
- **CLI Group Count (`189`):** **PASS** — `len(build_app().registered_groups) == 189` verified directly in runtime.
- **Core DNA & CycloneDX SBOM Gates:** **PASS** — `CoreDnaManifest.load()` validates `mekong.core_dna.v1` (`2026.10.28`), `dna/core-dna.json` registers `feat/strategy-c-gateway-stategraph-misa`, and `scripts/generate-sbom.py` emits valid CycloneDX 1.5 (`1,254` components).
- **MEKONG-BENCH v1.0:** **PASS** — `mekong opc bench --json` passes `15/15` deterministic layers (`exit_code=0`).
- **Static Analysis & Test Suites:** **PASS**
  - `/opt/homebrew/bin/ruff check src/ tests/` -> `0` errors
  - `/opt/homebrew/bin/bandit -r src/ -lll -q` -> `0` findings
  - `/opt/homebrew/bin/bandit -r src/opc/ src/core/opencore/ src/core/raas_license_verifier.py src/seed/ integrations/ -ll -q` -> `0` findings
  - G1 Open-Core / RaaS / OPC / Strategy-C / Strategy-E / Promise / Core-DNA gate -> **`258` passed (`0` failed)**
  - G1/G3 Python unit test suite -> **`2,568` passed (`0` failed)**
- **Dashboard TypeScript, Secrets, `:any`, `console.*`:** **PASS** — Zero secrets or `.env` files tracked; `0` TypeScript errors across `apps/dashboard/app/dashboard/opc/**` and `apps/dashboard/lib/opc-cockpit-data.ts`; `0` `:any` / `as any` casts and `0` `console.*` statements.

---

## Round-3 Empirical Verification Matrix (`R2-C01..R2-L01`)

| ID | Round-2 Finding | Round-3 Status | Empirical Verification Evidence (`65f5f7acd`) |
|---|---|---|---|
| **R2-C01** | `/webhook/zalo` leaked `card_sig` to external callers and bypassed MAC when `ZALO_OA_SECRET_KEY` unset or non-prod | **RESOLVED** | `src/api/pilot_a_routes.py:401-415` emits `card_sig`, `sig=` URLs, and `notification_cards` exclusively when `is_owner_authed` is `True`. `lines 296-317` fail closed (`HTTP 401 missing_zalo_webhook_secret` when `ZALO_OA_SECRET_KEY` is missing; `HTTP 401 invalid_zalo_webhook_mac` when `X-ZEvent-Mac` is missing/invalid across prod, provisioned tenants, and `zalo_oa`). `_verify_owner_access` (`lines 143-167`) enforces valid tenant API key or `card_sig` unconditionally across both `development` and `production` (`HTTP 401` verified on `/runs`, `/card`, `/decide`, `/draft-export`). |
| **R2-H01** | Concurrent `in_flight` race marked checkpoint `COMPLETED` prematurely; legacy replay clobbered `FAILED` / `RECONCILIATION_REQUIRED` to `COMPLETED` | **RESOLVED** | `src/opc/state_graph.py:108-110, 153-154` preserves `{"status": "in_flight"}` without advancing checkpoint stage; `src/api/pilot_a_routes.py:689-690` returns `HTTP 409 action_in_flight` without mutating `opc_runs`. Multi-threaded `threading.Event` probe confirmed Thread 2 receives `HTTP 409 action_in_flight` while `status` stays `pending_approval` and `checkpoint_stage` stays `INTERRUPT_AUTHORIZE`. `pilot_a_routes.py:634-642` + `src/opc/engine.py:154-157` return `HTTP 409 run_requires_reconciliation_or_failed` on replay of `FAILED` / `RECONCILIATION_REQUIRED` runs in both `legacy` and `langgraph` modes. |
| **R2-H02** | Unattributed `mk-*` NOWPayments IPN bypassed VN guard via spoofed `country`/`jurisdiction` and credited `"mk"` | **RESOLVED** | `src/raas/nowpayments_webhook_handler.py:126-146` removes `explicit_non_vn`, requiring a verified non-VN `TenantStore` record (`resolved_non_vn == True`) for `mk-*` order IDs (`{"order_id": "mk-112233445566", "country": "US", "jurisdiction": "SG"}` returns `HTTP 403 rail_not_permitted_for_jurisdiction`). `lines 196-198` route `mk-*` orders with `tenant_id`/`org_id`/`workspace_id` to the tenant workspace (`overseas_sg` credited `1,500`, `"mk"` balance `0`). |
| **R2-M01** | Dashboard `useEffect([actionPayload])` wiped `serverActionDigest`/`serverCardSig` after `runId` sync; `handleHandoffZalo` ignored `serverRejected` | **RESOLVED** | `apps/dashboard/app/dashboard/opc/page.tsx:160-171` only updates `actionDigest`, while `ClientIntakeCard.onChange` (`lines 514-518`) clears `serverActionDigest`/`serverCardSig` on user edits. `handleHandoffZalo` (`lines 357-365`) checks `if (syncRes.serverRejected)` before transitioning to `revoked`. `apps/dashboard/lib/opc-cockpit-data.ts:547-559` wires `X-API-Key` (`NEXT_PUBLIC_MEKONG_TENANT_API_KEY`) and `tenant_id` (`NEXT_PUBLIC_MEKONG_TENANT_ID`). |
| **R2-M02** | `PilotAWorkflow` hardcoded `local_endpoint=""` and leaked unredacted text into router citations on handoff | **RESOLVED** | `src/opc/pilot_a.py:98` passes default `local_endpoint=None` so `SelectiveRouter` honors `MLX_BASE_URL` and `LITELLM_BASE_URL` (verified via live probe), incorporates `rt_res.extracted` / `rt_res.confidence` (`lines 124-126`), and redacts PII on `handle_webhook_or_handoff` (`lines 150-151`, verified zero phone/email leakage in handoff payload). |
| **R2-M03** | `SelectiveRouter` burned `50.00 VND` budget when `cloud_fallback_fn is None` and `hard_budget_limit` was set | **RESOLVED** | `src/opc/selective_router.py:167-168` returns `low_confidence_halt` immediately when `self.cloud_fallback_fn is None` without calling `reserve_budget` (`0` ledger rows recorded under `hard_budget_limit="500.00"`). |
| **R2-L01** | `connector.dispatch.__code__` crashed on `functools.partial`/callables/mocks; `OPCEngine.generate_draft` persisted unredacted `intake.notes` | **RESOLVED** | `src/opc/engine.py:26-31, 164` uses `_accepts_now_kwarg` via `inspect.signature` (verified on `functools.partial`, callable object instances, and `MagicMock`), and `lines 117, 121` redact `intake.notes` via `redact_vietnamese_pii` before `StateStore.save_run` (verified zero MST/phone in persisted `proposal_input_json`). |

---

## Round-1 Baseline Matrix (`C-01..L-02` — 16/16 RESOLVED)

- `C-01` (`zalo_oa` connector registration & pre-consume validation): **RESOLVED**
- `C-02` (Pilot A owner auth, webhook MAC fail-closed, `card_sig` isolation): **RESOLVED**
- `C-03` (`dna/core-dna.json` Core DNA PR gate): **RESOLVED**
- `H-01` (Dashboard Gateway sync digest preservation, auth headers, & handoff rejection): **RESOLVED**
- `H-02` (Concurrent `in_flight` lock & non-clobbering replay state machine): **RESOLVED**
- `H-03` (Decree 52/2024 NOWPayments IPN fourth-door guard on hyphenated & `mk-*` orders): **RESOLVED**
- `H-04` (`SelectiveRouter` env wiring, ChatCompletions unwrap, & MCP SHA-256 allowlist): **RESOLVED**
- `H-05` (Live 48h Zalo interaction window enforcement at `/card` & `/decide`): **RESOLVED**
- `H-06` (`<15KB` mobile HTML card ceiling & redacted customer notes/citations): **RESOLVED**
- `M-01` (`CSRFMiddleware` skip prefixes with `card_sig`/API-key enforcement): **RESOLVED**
- `M-02` (Decree 13 `<72h` DSAR erasure across `opc`, `privacy`, and `vietqr` `transactions` DBs): **RESOLVED**
- `M-03` (Direct SQLite `matched_order_id` lookup for `/draft-export/{run_id}`): **RESOLVED**
- `M-04` (`SelectiveRouter` zero budget reservation when `cloud_fallback_fn is None`): **RESOLVED**
- `M-05` (`tests/test_strategy_c_*.py` wired into `g1-validation` & `g3-quality` coverage gates): **RESOLVED**
- `L-01` (`allow_inf_nan=False` on `extraction_confidence`): **RESOLVED**
- `L-02` (`VatRatePct` includes `5%` statutory tier): **RESOLVED**

---

## Non-Blocking Informational / Low Observations (Post-Merge Backlog)

1. **[Low — Overseas Hosted-Invoice `mk-*` Credit Attribution Without `tenant_id`]**
   - **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/raas/nowpayments_webhook_handler.py:131-140`, `:196-200` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/raas/checkout_router.py:147`, `:210`
   - **Detail:** Domestic VN and unattributed `mk-*` IPN payloads are strictly blocked (`HTTP 403`), and HMAC-SHA512 signature verification is enforced in production (`line 187`). However, when a registered non-VN (`SG`/`US`) tenant checks out via `POST /v1/checkout` (`rail="nowpayments"`), `create_invoice` sends `order_id="mk-<hex>"` and `customer_email` (without `tenant_id`). If NOWPayments echoes only `order_id` and `customer_email`, `_is_vn_jurisdiction_ipn` resolves the non-VN `TenantStore` row via `customer_email`, while `workspace_id` (`lines 197-200`) still falls back to `"mk"` when `explicit_ws` is absent.
   - **Suggested Follow-up:** Return the matched non-VN `TenantStore` identifier (`row["name"]` or `row["id"]`) from the `TenantStore` lookup when `explicit_ws` is empty (and bind `explicit_ws` itself against `TenantStore` when provided) so hosted-invoice overseas checkouts credit the exact tenant account automatically.

2. **[Low — Static Client Env Key Exposure Scope (`NEXT_PUBLIC_MEKONG_TENANT_API_KEY`)]**
   - **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/lib/opc-cockpit-data.ts:549`
   - **Detail:** `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` is inlined into the browser bundle when set at build time, which is suitable for local/self-hosted single-owner cockpits but should not be populated in shared multi-tenant static bundles.
   - **Suggested Follow-up:** For hosted multi-tenant SaaS deployments, proxy `/v1/opc/pilot-a/*` through a server-side session route or prompt the shop owner to paste their tenant key into session storage rather than baking `NEXT_PUBLIC_MEKONG_TENANT_API_KEY` at build time.

---

## Plan Task Status (`plans/261115-GH-157-strategy-c-gateway-stategraph-misa/plan.md`)

- **Phase 1 (Legal Fourth-Door Closure & VN SME Pricing Alignment):** Complete and verified.
- **Phase 2 (Strategy C Core Runtime `<= 185 LOC`):** Complete and verified.
- **Phase 3 (Dashboard OPC Bilingual VN-First Cockpit):** Complete and verified.
- **Phase 4 (FastAPI Pilot A HTTP Routes, Mobile Card & Gateway Wiring):** Complete and verified.
- **Phase 5 (Full Verification, Isolated Adversarial Review, PR & Merge):** Adversarial review complete (`APPROVED FOR PR / MERGE`); ready for commit of updated report, PR creation/update, and merge to `main`.
