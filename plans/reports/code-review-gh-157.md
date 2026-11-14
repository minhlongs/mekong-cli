# Code Review Report — GH-157 (`feat/strategy-c-gateway-stategraph-misa`)

- **Branch Audited:** `feat/strategy-c-gateway-stategraph-misa` (`81dc6d8aa`) vs `origin/main` (`fcc565289`)
- **Issue:** `#157` — Strategy C StateGraph, Profile 4 Router, Pilot A HTTP/Card & Legal Fourth-Door Closure
- **Scope:** 36 changed files (+4,603 / -521 LOC) across `src/opc/`, `src/api/`, `src/raas/`, `src/cli/`, `apps/dashboard/`, `.goose/recipes/`, `config/`, `.github/workflows/gates.yml`, and `tests/`
- **Verdict:** **CHANGES REQUIRED (`BLOCKED` — 3 Critical, 6 High, 5 Medium, 2 Low)**

---

## Verified Hard Invariants (Passing)

- **LOC Ceiling (`<= 185 LOC`):** Verified across 100% of `src/opc/**/*.py` (max 185 LOC in `pilot_a.py`, `zalo_http.py`, `bench_layers_vn.py`) and all 11 OPC contract test files (max 179 LOC).
- **Neutral Core AST Boundary:** Zero forbidden country-pack AST imports (`thue_dnvn`, `ke_toan`, `zalo_oa`, `zalo_engine`, `tt78`) in `src/opc/**/*.py` and core kernel modules.
- **Byte-for-Byte Protected Files:** `git diff origin/main...HEAD -- src/core/opencore/phase_559_opencore_25_step_catalog.py .mekong/company.json` is empty (0 bytes changed).
- **CLI Group Count:** `len(build_app().registered_groups) == 189` preserved.
- **Static Gates & Unit Suites:** `ruff check src/ tests/` passes with 0 errors; `bandit -r src/ -lll -q` and `bandit -r src/opc/ ... -ll -q` pass with 0 findings; all 86 G1 boundary/OPC/Strategy-E/Strategy-C tests pass (`22.08s`); zero `:any` types and zero `console.*` statements in `apps/dashboard/app/dashboard/opc/**` and `apps/dashboard/lib/opc-cockpit-data.ts`; zero secrets or `.env` files committed.
- **HTML / XML / CSV Injection Escaping:** `pilot_a_card_view.py` properly HTML-escapes user fields and escapes `</` inside inline JSON; `misa_export.py` escapes XML attributes/entities and prefixes leading whitespace/tab formula payloads (`=`, `+`, `-`, `@`, `|`) with `'`.

---

## Critical Findings (Blockers)

### C-01: Guaranteed `HTTP 500` (`ValueError: Unknown connector: 'zalo_oa'`) When Approving Live Zalo OA Runs via `POST /v1/opc/pilot-a/decide`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:342`, `:421`, `:427` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/pilot_a.py:121-123`
- **Evidence (Empirically Reproduced):**
  1. When `POST /v1/opc/pilot-a/webhook/zalo` is invoked with `"connector": "zalo_oa"` and a valid `X-ZEvent-Mac`, `PilotAWorkflow.handle_webhook` persists `payload.connector = "zalo_oa"` in `opc_runs` and binds it into `action_digest`.
  2. When the owner subsequently calls `POST /v1/opc/pilot-a/decide`, line 342 calls `_build_workflow(tenant_id=req.tenant_id)` with default `connector_name="zalo_oa_sandbox"`.
  3. `PilotAWorkflow.__init__` (`src/opc/pilot_a.py:123`) constructs `OPCEngine` with `connectors={"mock_followup_draft": ..., "zalo_oa_sandbox": ...}` — `"zalo_oa"` is omitted!
  4. `OPCEngine.execute_approved_action` (`src/opc/engine.py:156-161`) **atomically consumes the approval token in SQLite first**, then raises unhandled `ValueError("Unknown connector: 'zalo_oa'")`, crashing the request with `HTTP 500` and leaving `opc_side_effect_journal` empty.
- **Fix:** Resolve `connector_name = str(action_dict.get("connector", "zalo_oa_sandbox"))` from the persisted `action_payload` before building `PilotAWorkflow` in `/decide` (or always register `ZaloOAConnector` alongside `ZaloSandboxConnector` when eligible), and check connector existence in `OPCEngine.execute_approved_action` *before* `consume_approval_atomic`.

### C-02: Unauthenticated Public Exposure of Pilot A Endpoints, Webhook MAC/Consent/Price Tampering, and Orphaned `tenant_provisioner`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:54-77`, `:95-140`, `:158-214`, `:257-363`, `:509-556` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/tenant_provisioner.py:40-129`
- **Evidence:**
  1. **Zero Authn/Authz on Owner & Data Endpoints:** `pilot_a_router` is mounted directly on public `src/gateway.py:93` with zero `Depends(...)` authentication on `GET /runs/{run_id}`, `GET /card/{run_id}`, `POST /decide`, and `GET /draft-export/{run_id}`. Because `action_digest` is an unkeyed SHA-256 returned directly by `GET /runs/{run_id}` and `GET /card/{run_id}`, anyone who learns or guesses a `run_id` + `tenant_id` can read customer PII/quotes, export accounting drafts, or trigger `approve`/`reject`/`handoff` without an owner secret or API key.
  2. **`verify_tenant_api_key` & `<slug>.tenant.json` Are Completely Orphaned in Production:** `verify_tenant_api_key` (`src/opc/tenant_provisioner.py:119`) has **zero** callers in `src/`. Moreover, `_build_workflow` and `_build_profile` (`src/api/pilot_a_routes.py:95-140`) never read the provisioned `<slug>.tenant.json` (ignoring the tenant's `business_name`, `owner_name`, `sme_tier`, `monthly_workflow_quota`, `bank_id`, and `account_no` — reproduced: a tenant provisioned with VCB `9999111122` still emits VietQR for global default MB `0988889999`), and CLI `opc_strategy_c_cmd.py:25` writes to `.mekong/tenants` whereas `pilot_a_routes.py:90` reads `.mekong/pilot_a_tenants`.
  3. **Request-Body Trust Boundary Violations on Public `/webhook/zalo`:**
     - **MAC Bypass:** Even when `ZALO_OA_SECRET_KEY` is set in production, omitting the `X-ZEvent-Mac` header while keeping default `connector="zalo_oa_sandbox"` causes `(self.require_webhook_mac or oa_secret_key is not None or webhook_mac is not None)` (`src/opc/pilot_a.py:129`) to evaluate to `False`, completely skipping MAC verification.
     - **Consent Forgery, Price Override & Quota Escalation:** Public `PilotAZaloWebhookRequest` lets an unauthenticated external caller set `grant_consent=True` (forging Decree 13/2023 subject consent at line 180), `service_rates_vnd={"tu_van_ai": 0}` (overriding shop unit prices to 0 VND at line 98), and `sme_tier="agency"` (escalating monthly quota from 300/500 to 3,500 at line 172).
     - **Unbounded Disk/SQLite DoS:** Every unauthenticated call with a random valid slug `tenant_id` creates 3 new SQLite databases (+6 WAL/SHM files) on disk via `resolve_tenant_db_path`.
- **Fix:**
  - Load provisioned `<tenant_id>.tenant.json` when present (and unify default tenant dir between CLI and Gateway), sourcing `sme_tier`, `bank_id`, `account_no`, `business_name`, and `owner_name` from server/tenant config rather than untrusted webhook body fields.
  - Require `verify_tenant_api_key` (via `Authorization: Bearer mk_opc_...` / `X-API-Key`) or a signed HMAC card token (`ApprovalToken.signature`) on `/runs`, `/card`, `/decide`, and `/draft-export` when a tenant is provisioned or `MEKONG_ENV=production`.
  - Enforce `verify_zalo_webhook_mac` whenever `ZALO_OA_SECRET_KEY` is set in non-test environments unless authenticated by a valid tenant/admin API key; never allow unauthenticated callers to pass `grant_consent=True` or arbitrary `service_rates_vnd`.

### C-03: `.github/workflows/core-dna-gate.yml` Will Hard-Fail on PR Creation Against `main`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/.github/workflows/core-dna-gate.yml:36-53`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/cli/commands/opc_command.py`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/cli/commands/opc_strategy_c_cmd.py`
- **Evidence:**
  - `core-dna-gate.yml` runs on every `pull_request` targeting `main`. Step `Detect feature surface changes` matches `^(src/cli/|src/commands/|...)` — which matches both `src/cli/commands/opc_command.py` and `src/cli/commands/opc_strategy_c_cmd.py` in this diff — and exits `1` unless `^dna/(core-dna|binh-phap-operating-system|command-surface)\.json$` is also updated in the PR diff.
  - Currently zero `dna/*.json` files are modified on `feat/strategy-c-gateway-stategraph-misa` (verified via `git diff --name-only origin/main...HEAD`). Historical PRs `#143`, `#155`, and `#156` all required `dna/core-dna.json` updates for this exact gate (PR `#155` failed run `43586964968` before updating `dna/core-dna.json`).
- **Fix:** Register the new `opc provision-tenant` / `opc validate-recipe` capabilities in `dna/core-dna.json` (and/or `dna/command-surface.json`) and re-run `pytest tests/test_core_dna.py tests/test_core_dna_workflow.py`.

---

## High Priority Findings

### H-01: Dashboard Live Gateway Sync Always Fails `/decide` with `HTTP 409 tamper_detected_digest_mismatch` + Divergent Catalog/VAT Math
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/lib/opc-cockpit-data.ts:60-110`, `:240-274`, `:460-477`, `:543-655` and `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/app/dashboard/opc/page.tsx:238-308`
- **Evidence (Empirically Reproduced):**
  1. When the user clicks "Đồng bộ Gateway" (`handleGatewayWebhookSync`), `syncPilotAZaloWebhook` posts to `/v1/opc/pilot-a/webhook/zalo` and captures only `serverRunId` (`body.run_id`), **discarding `body.action_digest`, `body.total_amount_vnd`, and `body.vietqr_emvco`** (`opc-cockpit-data.ts:587-596`).
  2. When the user then clicks "✅ Duyệt & Gửi Báo Giá + VietQR", `handleApproveAndSend` sends the **locally computed** Web Crypto `actionDigest` (`opc-cockpit-data.ts:460-477`) to `POST /v1/opc/pilot-a/decide` against `serverRunId`.
  3. The frontend's `OpcActionPayload` schema (`capability: "vn.zalo_oa_followup"`, `parameters: {amount, project_title}`, VAT-inclusive `grandTotal`, `expiresAt` client clock, and catalog rates `450k/350k/300k`) is completely different from the backend's `ActionPayload` (`capability: "followup.create_draft"`, `parameters: {amount_vnd, tenant_id, vietqr_emvco, vietqr_quicklink, interaction_age_seconds, last_user_interaction_ts, ...}`, VAT-exclusive `5,400,000 VND` on `600k/400k/350k` rates).
  4. Consequently, `POST /v1/opc/pilot-a/decide` **100% deterministically rejects the Dashboard request with `HTTP 409 tamper_detected_digest_mismatch`**, and `syncPilotADecision` (`opc-cockpit-data.ts:631-637`) catches `!response.ok` and silently masks the `HTTP 409` rejection as `status: 'success'` ("Verified via local Web Crypto (Offline-safe)") in `page.tsx:291-321`!
- **Fix:** Capture `action_digest`, `total_amount_vnd`, `vietqr_emvco`, `vietqr_memo`, and `tenant_id` from `syncPilotAZaloWebhook`'s response; bind `serverActionDigest` when synced to a live gateway; surface `HTTP 409` / `4xx` errors from `/decide` as `tamper_detected` / error rather than silently reporting `Offline-safe` dispatch success on server rejection; and align `SERVICE_CATALOG` default Pilot A VND rates (`600k / 400k / 350k`) and memo prefix (`OPC {runId}` vs `MEKONG {runId}`).

### H-02: State Machine Corruption & Concurrent Double-Dispatch Race in `GovernedStateGraph` and `/decide`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/state_graph.py:104-118`, `:148-152` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:364-458`
- **Evidence (Empirically Reproduced):**
  1. **Concurrent Double Side-Effect in `SqliteGraphCheckpointer.execute_side_effect_once` (`state_graph.py:106-117`):** `SELECT result_json FROM opc_side_effect_journal` runs *outside* any lock, then `commit_fn(state)` runs unlocked, and `BEGIN IMMEDIATE` is acquired only *after* `commit_fn` returns. Under a 4-thread concurrent `GovernedStateGraph.resume` probe, `commit_fn` executed **4 times instead of 1**! (In `pilot_a_routes.py`, `StateStore.record_action_attempt` happens to catch the second thread only if `idempotency_key` matches, whereas standalone `GovernedStateGraph.resume` callers suffer multi-dispatch, and `pilot_a_routes.py:412` still mints and saves multiple `ApprovalToken` rows per race).
  2. **Failed / Uncertain Dispatches Turn Into `COMPLETED` on Replay (`pilot_a_routes.py:423-441` & `state_graph.py:151`):** `GovernedStateGraph.resume` unconditionally checkpoints `GraphStage.COMPLETED` even when `commit_out["status"]` is `"failed"` or `"reconciliation_required"`. Worse, on a second `/decide` call, `dedup` is `True`, so line 425 sets `out_status = "deduplicated"` and line 434 overwrites a `FAILED` or `RECONCILIATION_REQUIRED` run in `opc_runs` to `WorkflowStatus.COMPLETED`!
  3. **Post-Completion Status Clobber (`pilot_a_routes.py:364-406`):** Neither the `handoff` branch (line 364) nor the `reject`/`revise` branch (line 390) checks `run_data["status"]`. Reproduced: sending `decision="reject"` or `decision="handoff"` *after* a run is already `COMPLETED` returns `HTTP 200` and overwrites `opc_runs.status` from `completed` to `rejected` / `revise_requested`! Also in `RUNTIME_ENGINE=legacy` (`checkpointer=None`), `handoff` sets `REVISE_REQUESTED`, which does not block a subsequent `approve` (line 408 only blocks `REJECTED`).
- **Fix:**
  - Claim an `in_flight` reservation row inside `opc_side_effect_journal` under `BEGIN IMMEDIATE` *before* invoking `commit_fn(state)`, and only persist/transition to `GraphStage.COMPLETED` when `commit_out.get("status") in ("completed", "deduplicated")` (or preserve the original `commit_out["status"]` on replay).
  - Enforce strict state precondition at the top of `decide_pilot_a_run`: reject transitions unless `run_data["status"] in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.REVISE_REQUESTED)`, and introduce/enforce a non-approvable status (or check `HANDOFF_ZALO_OA_MANAGER` across both engines) after `handoff`.

### H-03: NOWPayments IPN Fourth-Door Guard Fails Open on Unregistered `order_id`s (`mk-<hex>`) and Hyphenated VN Tenant Slugs
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/raas/nowpayments_webhook_handler.py:83-140`, `:185-188`
- **Evidence (Empirically Reproduced):**
  1. `TenantStore.jurisdiction_for(org_id)` (`src/raas/tenant.py:211-246`) and `checkout_router.py:82-92` follow a **fail-closed** policy: any unidentifiable org defaults to `"VN"` (denying crypto).
  2. By contrast, `_is_vn_jurisdiction_ipn` (`nowpayments_webhook_handler.py:125-140`) queries `SELECT jurisdiction FROM tenants WHERE id = ? OR name = ?` and **returns `False` (allowing crypto!) whenever `row is None`!**
  3. **Concrete Bypass 1 (`mk-<hex>` Checkout Orders):** `checkout_router.py:147` generates `order_id = f"mk-{uuid.uuid4().hex[:12]}"`, and NOWPayments IPN callbacks frequently omit `customer_email`. `_is_vn_jurisdiction_ipn` extracts `candidates = ["mk", "mk-a1b2c3d4e5f6"]`, finds no row in `tenants`, and **returns `False`**, allowing a crypto IPN without any non-VN tenant attribution!
  4. **Concrete Bypass 2 (Hyphenated Registered VN Tenant Names):** If a VN tenant is registered in `TenantStore` with `name = "shop-hanoi"` (`jurisdiction = 'VN'`), and an IPN arrives with `order_id = "shop-hanoi-pro-monthly"`, line 187 computes `workspace_id = order_id.split("-")[0]` -> `"shop"`. `candidates` contains `["shop", "shop-hanoi-pro-monthly"]` — neither matches `name = "shop-hanoi"` in SQLite, so `_is_vn_jurisdiction_ipn` **returns `False`**!
  5. **Legacy Test Drift Note:** Running `pytest tests/test_billing.py tests/test_nowpayments_ipn_golden.py` shows 6 failures on pre-existing `TIERS` credit numbers (`4000 != 1200`, `1500 != 300`); note those legacy tests call `handle_ipn` with `ws_test-pro-monthly` without a `TenantStore` entry, which explains why `_is_vn_jurisdiction_ipn` returned `False` on `row is None`, but leaving `mk-*` and hyphenated VN tenant names open weakens the fourth-door guarantee.
- **Fix:** Also match hyphen-prefix candidates (progressive `"-"` prefixes of `order_id`, e.g., `"shop-hanoi"` from `"shop-hanoi-pro-monthly"`), explicitly reject `mk-*` checkout `order_id`s unless resolved to a non-VN `TenantStore` record or explicit non-VN `jurisdiction`, and require `NOWPAYMENTS_IPN_SECRET` when `MEKONG_ENV == "production"` even if `x-nowpayments-sig` is omitted (`nowpayments_webhook_handler.py:178`).

### H-04: `SelectiveRouter` Is Never Wired Into `PilotAWorkflow` or `pilot_a_routes.py` + Broken OpenAI ChatCompletion Parsing
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/selective_router.py:158-170`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/pilot_a.py:139`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:38`, `:316`
- **Evidence (Empirically Reproduced):**
  1. **Orphaned Class in Production:** `SelectiveRouter` (`src/opc/selective_router.py:116`) has **zero** production callers anywhere in `src/`! `PilotAWorkflow` and `pilot_a_routes.py` import only the helper `extract_deterministic_citations` and rely on caller-supplied `event.extraction_confidence` rather than routing through `SelectiveRouter.route(...)`. Likewise, `load_declarative_recipe` and `verify_mcp_manifest_sha256` (`src/opc/recipe_loader.py`) are only invoked by the CLI validator command, never enforced by `PilotAWorkflow` or `OPCEngine` at pack load time.
  2. **OpenAI-Compatible Response Parsing Bug (`selective_router.py:160-170`):** `SelectiveRouter.route` sends an OpenAI Chat Completions payload (`{"model": ..., "messages": [{"role": "user", "content": safe_msg}]}`), which returns `{"choices": [{"message": {"content": "..."}}], "usage": {...}}` — **not** top-level `confidence`, `extracted`, or `citations` keys! Because line 167 defaults `l_conf = float(parsed.get("confidence", 0.88))` and `0.88 >= 0.85`, **any real MLX / Ollama / LiteLLM `/v1/chat/completions` HTTP 200 response silently fabricates `confidence = 0.88` with empty `extracted` fields** instead of parsing `choices[0].message.content` or halting on missing confidence!
  3. **Zombie Thread Leak on Timeout (`selective_router.py:161-173`):** Creating a fresh `ThreadPoolExecutor(max_workers=1)` per request and calling `pool.shutdown(wait=False, cancel_futures=True)` does not interrupt an already-running `urlopen`, leaking blocked worker threads if the local endpoint hangs until socket timeout.
- **Fix:** Wire `SelectiveRouter` into `PilotAWorkflow` (when `extraction_confidence` is not pre-supplied or via an explicit router hook), parse `choices[0]["message"]["content"]` when top-level `extracted`/`confidence` are absent, and **default missing LLM `confidence` to `0.0` (fail-closed)** instead of `0.88`.

### H-05: 48-Hour Zalo OA Interaction Window Bypassed at `/decide` Dispatch Time & Frozen on Mobile Card
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:313-314`, `:411-430` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/engine.py:168`
- **Evidence:**
  1. `PilotAWorkflow.approve_and_send` (`src/opc/pilot_a.py:171-174`) explicitly checks `window_age > ZALO_INTERACTION_WINDOW_SECONDS` against current `time.time()` before dispatching.
  2. However, `POST /v1/opc/pilot-a/decide` bypasses `wf.approve_and_send` and calls `wf.engine.execute_approved_action(...)` directly. Inside `OPCEngine.execute_approved_action` (`src/opc/engine.py:168`), `connector.dispatch(idempotency_key, payload)` is called **without passing `now=now`**.
  3. In both `ZaloOAConnector.dispatch` (`zalo_http.py:114-117`) and `ZaloSandboxConnector.dispatch` (`pilot_a.py:90`), `last_user_interaction_ts` is only checked `if now is not None`; when `now is None`, it falls back to the static `interaction_age_seconds` captured at intake! If a message arrived at `age = 30h` and the owner clicks Approve `20h` later (`50h > 48h`, while the 24h approval token is still valid), `/decide` dispatches a message violating Zalo's 48h CS window!
  4. Similarly, `GET /v1/opc/pilot-a/card/{run_id}` (`pilot_a_routes.py:313-314`) computes `rem_hours` from static `interaction_age_seconds` instead of `int(time.time()) - int(params.get("last_user_interaction_ts", ...))`, so the card badge never counts down.
- **Fix:** Compute live `age_s = int(time.time()) - int(params["last_user_interaction_ts"])` in both `get_pilot_a_mobile_card` and `decide_pilot_a_run` (returning `HTTP 403 ZaloInteractionWindowError` when `age_s > ZALO_INTERACTION_WINDOW_SECONDS`), and pass `now=now` (or fall back to `int(time.time())`) inside `ZaloOAConnector.dispatch` / `ZaloSandboxConnector.dispatch`.

### H-06: `<15KB` Mobile HTML Card SLA Violated on Large `requested_services` + Redacted Customer Notes & Citations Lost After Persistence
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:62`, `:311-331`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_card_view.py:125-136`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/pilot_a.py:155`
- **Evidence (Empirically Reproduced):**
  1. **`>15KB` Card Overflow:** `PilotAZaloWebhookRequest.requested_services` (`pilot_a_routes.py:62`) has **no `max_length` cap**, and `render_mobile_approval_card_html` (`pilot_a_card_view.py:126`) iterates over all `line_items` without truncation. Reproduced: a valid request with 250 `requested_services` produces a **24,769-byte** HTML card, violating the `<15KB` mobile card contract.
  2. **Customer Notes & Source Citations Silenced on `GET /card/{run_id}`:** `PilotAWorkflow.handle_webhook` (`src/opc/pilot_a.py:155`) overwrites `opc_runs.proposal_input` with `{"request_id": ..., "client_name": ..., "sender_id": ...}` — **dropping `notes` (`redacted.redacted_text`)**! When `GET /v1/opc/pilot-a/card/{run_id}` runs (`pilot_a_routes.py:315-316`), `intake.get("notes")` is always `None`, so it falls back to `payload.content` (`"[BẢN NHÁP BÁO GIÁ] ..."`), which displays the synthetic quote banner instead of the customer's redacted Zalo message and causes `extract_deterministic_citations` to miss the customer's message spans!
- **Fix:** Add `max_length=25` (and per-item `max_length=64`) to `PilotAZaloWebhookRequest.requested_services`, cap rendered `line_items` (e.g., top 15 with `"+N hạng mục khác"` summary) and truncate `customer_notes` in `render_mobile_approval_card_html` to guarantee `<15,000` UTF-8 bytes, and persist `"notes": redacted.redacted_text` in `pilot_a.py:155`.

---

## Medium Priority Findings

### M-01: `CSRFMiddleware` (`CSRF_ENABLED=1`) Breaks Pilot A Webhooks and Mobile Card `fetch('/decide')`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/middleware/csrf_middleware.py:29-33` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_card_view.py:188`
- **Evidence:** `_CSRF_SKIP_PREFIXES` only exempts `("/v1/webhook/", "/v1/polar/", "/v1/payments/")` — missing `/v1/opc/pilot-a/webhook/` and `/webhooks/nowpayments`! Additionally, `mekong_csrf` is set `httponly=True` (`csrf_middleware.py:122`), so inline JS in `/v1/opc/pilot-a/card/{run_id}` cannot read it to populate `X-CSRF-Token` on `POST /v1/opc/pilot-a/decide`. Enabling `CSRF_ENABLED=1` in production will reject Zalo webhooks, VietQR webhooks, NOWPayments IPNs, and mobile card approvals with `HTTP 403 csrf_validation_failed`.
- **Fix:** Add `"/v1/opc/pilot-a/webhook/"` and `"/webhooks/"` to `_CSRF_SKIP_PREFIXES`, and inject a signed action/CSRF token into the mobile card when `CSRF_ENABLED=1`.

### M-02: DSAR `<72h` Erasure Misses `vietqr` `transactions` Table and `opc_workflow_quota_reservations`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/privacy_guard.py:138-143`
- **Evidence (Empirically Reproduced):** `PilotPrivacyGuard.erase_subject_under_72h` deletes from `qr_codes` in `{stem}_vietqr.db`, **but never deletes from `transactions`** in `{stem}_vietqr.db`! In our probe, after `erase_subject_under_72h("84988777666")`, `wf.vietqr.list_transactions()` still returned the erased subject's `TX_DSAR_1` record containing `"Thanh toan OPC run_... tu Nguyen Van Xoa 84988777666"`. Furthermore, if `workflow_id` (`event_id`) contains subject identifiers, `opc_workflow_quota_reservations` is not scrubbed/anonymized.
- **Fix:** Delete matching rows in `transactions` (`WHERE matched_order_id = ? OR memo LIKE ? ESCAPE '\'`) inside `{stem}_vietqr.db` during `erase_subject_under_72h`.

### M-03: `GET /v1/opc/pilot-a/draft-export/{run_id}` Only Scans Last 50 VietQR Transactions (`limit=50`)
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:531-535`
- **Evidence:** `wf.vietqr.list_transactions(limit=50)` silently drops `bank_tx_id` (`MaGiaoDichVietQR`) for any paid order older than the 50 most recent bank transfers in the tenant's VietQR DB, causing MISA/Sapo exports to lose their Napas reconciliation reference even after `/webhook/vietqr` succeeded.
- **Fix:** Query `{stem}_vietqr.db` directly by `WHERE matched_order_id = ?` (or add `VietQrEngine.get_transaction_by_order(run_id)`) instead of scanning `list_transactions(limit=50)`.

### M-04: `SelectiveRouter` Reserves Cloud Budget Even When `cloud_fallback_fn is None`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/selective_router.py:174-178`
- **Evidence:** `self.usage_ledger.reserve_budget(...)` executes *before* checking `if self.cloud_fallback_fn is None:`. When no cloud fallback is configured, every low-confidence message permanently consumes `50.00 VND` of reserved budget in SQLite even though zero cloud calls are made and the router immediately returns `low_confidence_halt`.
- **Fix:** Check `if self.cloud_fallback_fn is None:` *before* calling `self.usage_ledger.reserve_budget(...)`.

### M-05: CI Coverage Suite (`g1-validation` Step 7 & `g3-quality`) Omits Strategy C Tests, Under-Reporting Coverage on New Modules
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/.github/workflows/gates.yml:64-97`, `:103-116`, `:201-215`
- **Evidence:** `tests/test_strategy_c_*.py` were added to `Open-Core 25-Step & RaaS Boundary Gate` (which runs without `--cov`), but not to `Python unit tests` (line 105) or `Python coverage check` in `g3-quality` (line 203). While the 25% threshold currently passes, new modules `src/api/pilot_a_routes.py` (559 LOC), `src/api/pilot_a_card_view.py` (193 LOC), and `src/opc/{state_graph,selective_router,recipe_loader,misa_export,tenant_provisioner}.py` receive 0% credit in the `coverage.xml` gate.
- **Fix:** Include `tests/test_strategy_c_legal_pricing.py tests/test_strategy_c_runtime.py tests/test_strategy_c_http_gateway.py` in the `--cov=src` pytest invocations in `g1-validation` and `g3-quality`.

---

## Low Priority Findings

### L-01: `PilotAZaloWebhookRequest.extraction_confidence` Accepts `NaN` / `Infinity` Without Pydantic Bounds
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:67`
- **Evidence:** `extraction_confidence: float = Field(0.95)` lacks `ge=0.0, le=1.0, allow_inf_nan=False`. While `verify_confidence_and_math` catches `NaN`, passing `1e309` (`+inf`) over non-strict JSON returns `HTTP 200` and bypasses `<0.85` handoff (`inf >= 0.85` is `True`!).
- **Fix:** Change to `extraction_confidence: float = Field(0.95, ge=0.0, le=1.0, allow_inf_nan=False)`.

### L-02: Dashboard `VatRatePct` Omits `5%` Statutory Tier Supported by Backend & Recipe
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/lib/opc-cockpit-data.ts:3` and `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/app/dashboard/opc/components/client-intake-card.tsx:45`
- **Evidence:** Backend `accounting_draft.py:128` and `.goose/recipes/pilot-a-zalo-lead-to-quote.yaml:47` allow `(0, 5, 8, 10)`, whereas `VatRatePct` in `opc-cockpit-data.ts` only types `0 | 8 | 10`.
- **Fix:** Widen `VatRatePct` to `0 | 5 | 8 | 10` and include `5` in `VAT_RATES`.

---

## Prioritized Pre-Merge Action Checklist

1. **[Critical — C-01]** Fix `zalo_oa` connector resolution in `POST /v1/opc/pilot-a/decide` (`src/api/pilot_a_routes.py`) and validate connector existence before `consume_approval_atomic` in `OPCEngine.execute_approved_action`.
2. **[Critical — C-02]** Wire `<tenant_id>.tenant.json` + `verify_tenant_api_key` (or HMAC card token) into `src/api/pilot_a_routes.py`, enforce `ZALO_OA_SECRET_KEY` MAC verification fail-closed, and remove unauthenticated webhook overrides (`grant_consent`, `service_rates_vnd`, `sme_tier`, arbitrary unprovisioned `tenant_id` DB creation in production).
3. **[Critical — C-03]** Update `dna/core-dna.json` (and/or `dna/command-surface.json`) so `.github/workflows/core-dna-gate.yml` passes on PR creation.
4. **[High — H-01]** Bind server-returned `action_digest` / quote totals in `apps/dashboard/lib/opc-cockpit-data.ts` & `page.tsx`, align default Pilot A VND catalog rates (`600k/400k/350k`), and surface `/decide` `4xx` errors honestly instead of masking them as offline success.
5. **[High — H-02]** Lock `opc_side_effect_journal` with `BEGIN IMMEDIATE` *before* running `commit_fn`, preserve `"failed"` / `"reconciliation_required"` statuses across replays, and block post-completion state clobbering (`reject`/`revise`/`handoff` on `completed` runs) in `/decide`.
6. **[High — H-03]** Close `_is_vn_jurisdiction_ipn` bypasses on hyphenated VN tenant names (`shop-hanoi-pro-monthly`) and unattributed `mk-<hex>` checkout order IDs in `src/raas/nowpayments_webhook_handler.py`.
7. **[High — H-04, H-05, H-06]** Wire `SelectiveRouter` (with `confidence` defaulting to `0.0` instead of `0.88` on raw OpenAI JSON), enforce live 48h Zalo window at `/decide` + `/card`, persist redacted `notes` in `pilot_a.py`, and cap `requested_services` / rendered card items to guarantee `<15KB`.
8. **[Medium — M-01..M-05]** Exempt `/v1/opc/pilot-a/webhook/` and `/webhooks/` in `CSRFMiddleware`, delete `transactions` rows in `PilotPrivacyGuard.erase_subject_under_72h`, replace `list_transactions(limit=50)` in `/draft-export`, guard `reserve_budget` when `cloud_fallback_fn is None`, and add `test_strategy_c_*.py` to CI coverage steps.
