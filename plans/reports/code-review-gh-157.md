# Code Review Report — GH-157 (`feat/strategy-c-gateway-stategraph-misa`)

- **Branch Audited:** `feat/strategy-c-gateway-stategraph-misa` (`93224c01a` Round-2 / `81dc6d8aa` Round-1) vs `origin/main` (`fcc565289`)
- **Issue:** `#157` — Strategy C StateGraph, Profile 4 Router, Pilot A HTTP/Card & Legal Fourth-Door Closure
- **Scope:** 41 changed files (+5,088 / -562 LOC) across `src/opc/`, `src/api/`, `src/raas/`, `src/cli/`, `src/middleware/`, `apps/dashboard/`, `.goose/recipes/`, `config/`, `dna/`, `.github/workflows/gates.yml`, and `tests/`
- **Round-1 Verdict (`81dc6d8aa`):** `BLOCKED` (3 Critical, 6 High, 5 Medium, 2 Low)
- **Round-2 Verdict (`93224c01a`):** **`BLOCKED` (1 Critical, 2 High, 3 Medium, 1 Low remaining)** — 9 of 16 Round-1 findings fully resolved (`C-01`, `C-03`, `H-05`, `H-06`, `M-01`, `M-02`, `M-03`, `M-05`, `L-01`, `L-02`), 6 partially resolved with residual trust-boundary/state/router/budget defects, plus 1 newly exposed `card_sig` capability-leak vector on public `/webhook/zalo`.

---

## Round-2 Hard Invariants Verification (`93224c01a` — ALL PASSING)

- **LOC Ceiling (`<= 185 LOC`):** **PASS** — Verified across 100% of 24 `src/opc/**/*.py` modules (max `185` LOC in `src/opc/bench_layers_vn.py`), 13 `src/core/opencore/**/*.py` + `src/core/raas_license_verifier.py` modules (max `169` LOC), and 12 OPC/Strategy-C/E contract test files (max `179` LOC in `tests/test_opc_approval_security.py`). Zero violations.
- **Neutral Core AST Boundary:** **PASS** — Zero forbidden country-pack AST imports (`thue_dnvn`, `ke_toan`, `zalo_oa`, `zalo_engine`, `tt78`) across all 24 `src/opc/**/*.py` files.
- **Byte-for-Byte Protected Files:** **PASS** — `git diff --exit-code origin/main...HEAD -- src/core/opencore/phase_559_opencore_25_step_catalog.py .mekong/company.json` returned exit code `0` (0 bytes changed).
- **CLI Group Count (`189`):** **PASS** — `len(build_app().registered_groups) == 189` verified directly in runtime.
- **Core DNA Gate (`.github/workflows/core-dna-gate.yml`):** **PASS** — `dna/core-dna.json` updated (`core_dna_changed=true` alongside `feature_surface_changed=true`), `CoreDnaManifest.load()` validates `mekong.core_dna.v1` (`2026.10.28`), and `tests/test_core_dna.py` + `tests/test_core_dna_workflow.py` pass (`13/13`).
- **Static Analysis & Test Suites:** **PASS** — `ruff check src/ tests/` passes with 0 errors; `bandit -r src/ -lll -q` and `bandit -r src/opc/ src/core/opencore/ src/core/raas_license_verifier.py src/seed/ integrations/ -ll -q` pass with 0 findings; all **258** G1 Open-Core/RaaS/OPC/Strategy-E/Strategy-C/Promise/Core-DNA tests pass (`40.46s`).
- **Secrets, `.env`, `:any`, `console.*`:** **PASS** — Zero secrets or `.env` files tracked; zero `:any` / `as any` casts and zero `console.*` statements across `apps/dashboard/app/dashboard/opc/**` and `apps/dashboard/lib/opc-cockpit-data.ts`.

---

## Round-2 Verification Matrix (`C-01..L-02`)

| ID | Round-1 Finding | Round-2 Status | Empirical Verification Evidence (`93224c01a`) |
|---|---|---|---|
| **C-01** | `HTTP 500` (`Unknown connector: 'zalo_oa'`) in `/decide` | **RESOLVED** | `pilot_a_routes.py:556` passes `connector_name=payload.connector` to `_build_workflow`, and `engine.py:152-154` validates connector existence *before* `consume_approval_atomic`. Verified via `test_pilot_a_gateway_live_zalo_connector_handoff_mac_and_quarantine` and live probe with `ZALO_OA_TIER=basic` + `oa_tier=enterprise` (`HTTP 200 completed`). |
| **C-02** | Unauthenticated Pilot A exposure, webhook MAC bypass, orphaned `tenant_provisioner` | **PARTIAL -> R2-C01 (Critical)** | Provisioned `<slug>.tenant.json` + `verify_tenant_api_key` + `card_sig` HMAC are now wired on `/runs`, `/card`, `/decide`, `/draft-export`, and CLI/Gateway share `.mekong/pilot_a_tenants`. **HOWEVER**, `/webhook/zalo` returns `card_sig` & `card_url` directly in its HTTP JSON response to **unauthenticated / external callers**, and skips MAC when `ZALO_OA_SECRET_KEY` is unset in prod or when `MEKONG_ENV != "production"` on a provisioned tenant — allowing an unauthenticated caller to mint a run, harvest `card_sig` from the webhook response, and immediately execute `POST /decide` (`approve`)! |
| **C-03** | `core-dna-gate.yml` hard failure on PR | **RESOLVED** | `dna/core-dna.json` registers `feat/strategy-c-gateway-stategraph-misa` surface changes; workflow grep check and `pytest tests/test_core_dna.py tests/test_core_dna_workflow.py` pass. |
| **H-01** | Dashboard live sync `/decide` `409` masked as success + catalog drift | **PARTIAL -> R2-M01 (Medium)** | `syncPilotAZaloWebhook` now captures `serverActionDigest` & `serverCardSig`, `SERVICE_CATALOG` aligns to `600k/400k/350k` + `OPC {runId}`, and `syncPilotADecision` surfaces `4xx` rejections on Approve. **Residual bugs:** (1) `handleGatewayWebhookSync` updates `runId` (`page.tsx:258`), which triggers `actionPayload` recomputation -> `useEffect` (`page.tsx:160-173`) **asynchronously wipes `serverActionDigest` and `serverCardSig` back to `''`**, re-breaking `POST /decide` with `HTTP 409` on the very first sync! (2) `handleHandoffZalo` (`page.tsx:348-366`) ignores `syncRes.serverRejected` and marks state `revoked` even on `401/409`. |
| **H-02** | Concurrent double-dispatch race & replay status clobber | **PARTIAL -> R2-H01 (High)** | `BEGIN IMMEDIATE` in-flight lock prevents duplicate `commit_fn` execution (`calls=1` under 3 threads), and post-completion `reject`/`handoff` clobber is blocked (`HTTP 409`). **Two reproduced regressions remain:** (1) Concurrent Thread 2 hitting `in_flight` receives `{"status": "deduplicated"}` (`state_graph.py:111`), causing `GovernedStateGraph.resume` (`line 156`) to write `GraphStage.COMPLETED` while `commit_fn` is still running or failing (`reconciliation_required`)! (2) In `RUNTIME_ENGINE=legacy`, replaying `/decide` after a `failed` or `reconciliation_required` dispatch gets `out_status="deduplicated"` from `engine.py:163` and **overwrites `opc_runs.status` to `completed`** (`pilot_a_routes.py:655-681`)! |
| **H-03** | NOWPayments IPN fourth-door bypass on `mk-*` & hyphenated VN slugs | **PARTIAL -> R2-H02 (High)** | Progressive hyphen prefixes (`shop-hanoi` from `shop-hanoi-pro-monthly`) and unattributed `mk-*` order IDs are now blocked (`403`). **Residual bypass:** `nowpayments_webhook_handler.py:126-129, 149` trusts unverified body fields `country` / `jurisdiction` (`explicit_non_vn`) to exempt `mk-<hex>` checkout orders when no `TenantStore` record exists (`{"order_id": "mk-a1b2c3d4e5f6", "country": "US"}` reproduced `False` -> grants crypto credits without non-VN tenant attribution!). |
| **H-04** | `SelectiveRouter` unwired in `PilotAWorkflow` + OpenAI ChatCompletion `0.88` bug | **PARTIAL -> R2-M02 (Medium)** | `_unwrap_llm_json` now parses `choices[0].message.content`, defaults missing confidence to `0.0` (fail-closed), drops per-call `ThreadPoolExecutor` leaks, and `verify_mcp_manifest_sha256` runs in `PilotAWorkflow.__init__`. **Residual defect:** `PilotAWorkflow.__init__` (`pilot_a.py:98`) hardcodes `local_endpoint=""` (`"" is not None`), permanently disabling `MLX_BASE_URL` / `LITELLM_BASE_URL` env lookup in `SelectiveRouter.__init__`, and `pilot_a.py:122` discards `route_res.confidence` / `route_res.extracted`, never routing through Tier 2/3 in production. |
| **H-05** | 48h Zalo interaction window bypassed at `/decide` & static on `/card` | **RESOLVED** | Live `now_s - int(last_ts)` enforced in both `get_pilot_a_mobile_card` (`0.0g` + `disabled` button) and `decide_pilot_a_run` (`HTTP 403 ZaloInteractionWindowError` reproduced at 50h). |
| **H-06** | `<15KB` mobile HTML card overflow + lost customer notes/citations | **RESOLVED** | `requested_services` capped at `max_length=20` (`max_length=64` per slug), card renders top 12 items + `400`-char clipped redacted notes (`8,089 bytes < 15,000 bytes` under worst-case `&<>` expansion), and `notes` persisted in `pilot_a.py:137`. |
| **M-01** | `CSRFMiddleware` (`CSRF_ENABLED=1`) breaks Pilot A webhooks & mobile card `/decide` | **RESOLVED** | `/v1/opc/pilot-a/webhook/`, `/v1/opc/pilot-a/decide`, and `/webhooks/` added to `_CSRF_SKIP_PREFIXES` while `/decide` enforces `card_sig` / API key. Empirically verified over `https://mekongmind.com` with active `mekong_csrf` cookie (`200` on card `/decide`, `403` on unauthenticated `/v1/checkout`). |
| **M-02** | DSAR `<72h` erasure misses `vietqr` `transactions` table | **RESOLVED** | `privacy_guard.py:141-145` deletes matching rows from both `qr_codes` and `transactions` in `{stem}_vietqr.db`. Empirically verified (`0` transactions remaining, `404` on run lookup). |
| **M-03** | `/draft-export/{run_id}` drops `bank_tx_id` after 50 VietQR transactions | **RESOLVED** | `_lookup_vietqr_bank_tx_id` queries `WHERE matched_order_id = ?` directly in SQLite. Empirically verified with 61 transactions (`TX-OLD-001` preserved in CSV export). |
| **M-04** | `SelectiveRouter` reserves cloud budget when `cloud_fallback_fn is None` | **PARTIAL -> R2-M03 (Medium)** | Fixed when `hard_budget_limit is None`, **but** `selective_router.py:167-169` still calls `self.usage_ledger.reserve_budget(...)` inside `if self.cloud_fallback_fn is None:` whenever `hard_budget_limit` is set — permanently burning `50.00 VND` per low-confidence call despite making zero cloud requests! |
| **M-05** | CI coverage steps omit `tests/test_strategy_c_*.py` | **RESOLVED** | All 3 `tests/test_strategy_c_*.py` files added to both `g1-validation` and `g3-quality` `--cov=src` steps in `.github/workflows/gates.yml`. |
| **L-01** | `extraction_confidence` accepts `NaN`/`Infinity` | **RESOLVED** | `Field(0.95, ge=0.0, le=1.0, allow_inf_nan=False)` enforced on `PilotAZaloWebhookRequest`. |
| **L-02** | Dashboard `VatRatePct` omits `5%` statutory tier | **RESOLVED** | `VatRatePct = 0 | 5 | 8 | 10` and `VAT_RATES = [8, 10, 5, 0]` updated in `opc-cockpit-data.ts` and `client-intake-card.tsx`. |

---

## Remaining Round-2 Findings (Must Fix Before Merge)

### Critical Findings (1)

#### R2-C01 (Residual C-02 + New Capability Leak): `/v1/opc/pilot-a/webhook/zalo` Leaks Owner `card_sig` to External Webhook Callers and Permits Unauthenticated Forgery When `ZALO_OA_SECRET_KEY` Is Unset or Non-Prod
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:320-324`, `:367-402`
- **Empirically Reproduced Proofs:**
  1. **Owner Approval Capability (`card_sig`) Leaked to Untrusted Webhook Caller (`lines 367-368, 394, 396`):** `POST /v1/opc/pilot-a/webhook/zalo` is the inbound webhook called by **Zalo's external webhook servers** (not the shop owner, unless `is_owner_authed` is `True`), yet its HTTP response unconditionally returns `"card_sig": card_sig` and `"card_url": "...?sig={card_sig}"`. Any caller able to invoke `/webhook/zalo` receives the exact HMAC capability token needed to call `GET /card/{run_id}`, `GET /draft-export/{run_id}`, and **`POST /v1/opc/pilot-a/decide` (`decision="approve"`)**, completely bypassing owner approval!
  2. **Unauthenticated Prod Bypass When `ZALO_OA_SECRET_KEY` Is Empty (`lines 320-324`):**
     ```python
     must_check_mac = (
         x_zevent_mac is not None
         or req.connector.strip().lower() == "zalo_oa"
         or (_is_production() and bool(os.getenv("ZALO_OA_SECRET_KEY", "").strip()) and not is_owner_authed)
     )
     ```
     In our runtime probe (`MEKONG_ENV=production`, provisioned tenant `sadec_prod`, `ZALO_OA_SECRET_KEY` unset), an unauthenticated attacker posted to `/webhook/zalo` (`connector="zalo_oa_sandbox"`, no headers) -> received `HTTP 200` with `card_sig` -> immediately posted `decision="approve"` to `/decide` -> **`HTTP 200 completed`**!
  3. **Provisioned Tenant MAC Bypass Outside `MEKONG_ENV=production` (`line 323`):** Even when `ZALO_OA_SECRET_KEY` *is* configured and the tenant is provisioned (`tenant_cfg is not None`), `must_check_mac` only checks `_is_production()`, so omitting `X-ZEvent-Mac` on staging/self-hosted deployments skips MAC verification completely (`HTTP 200` reproduced in Probe 1b).
- **Required Fix:**
  1. **Never return `card_sig` or `sig=`-bearing `card_url` / `notification_cards` in the `/webhook/zalo` HTTP response unless `is_owner_authed` is `True`** (or in non-provisioned local dev when `tenant_cfg is None and not _is_production()`). External Zalo webhook callers only need `{"status": "INTERRUPT_AUTHORIZE", "run_id": ..., "event_id": ...}`; the signed `card_url` belongs exclusively in out-of-band owner notifications or authenticated owner sync calls.
  2. Fail closed on `/webhook/zalo` when `tenant_cfg is not None or _is_production()`: require **either** `is_owner_authed` (valid `X-API-Key` / `Bearer`) **or** valid `verify_zalo_webhook_mac` (raising `HTTP 401/503` if `ZALO_OA_SECRET_KEY` is missing rather than silently skipping MAC verification!).

---

### High Priority Findings (2)

#### R2-H01 (Residual H-02): Legacy Replay Clobbers `FAILED` / `RECONCILIATION_REQUIRED` Runs to `COMPLETED`, and Concurrent `in_flight` Thread Marks Checkpoint `COMPLETED` Prematurely
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/api/pilot_a_routes.py:654-681`, `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/state.py:131-149`, and `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/state_graph.py:108-112`, `:153-158`
- **Empirically Reproduced Proofs:**
  1. **Legacy Engine Replay Overwrites Uncertain/Failed Runs to `COMPLETED` (`Probe 2a`):** When `runtime_engine="legacy"` and the first `/decide` call returns `status="reconciliation_required"` (persisting `opc_runs.status = "reconciliation_required"`), a second `/decide` call enters `wf.engine.execute_approved_action(...)`, which hits `record_action_attempt == False` and returns `{"status": "deduplicated"}`. Lines 656-671 map `out_status == "deduplicated"` to **`WorkflowStatus.COMPLETED`** and overwrite `opc_runs.status` from `reconciliation_required` to `completed`!
  2. **Concurrent `in_flight` Race Writes `GraphStage.COMPLETED` Over Uncertain/Failed Outcome (`Probe 2b`):** In `SqliteGraphCheckpointer.execute_side_effect_once` (`state_graph.py:111`), a concurrent second request arriving while Thread 1's `commit_fn` is still `in_flight` receives `({"status": "deduplicated"}, True)`. `GovernedStateGraph.resume` (`line 156`) checks `commit_out.get("status") in ("completed", "deduplicated")` -> **`True`** -> writes `GraphStage.COMPLETED` to `opc_graph_checkpoints` (and `WorkflowStatus.COMPLETED` in `opc_runs`) even when Thread 1's `commit_fn` fails or returns `"reconciliation_required"`!
- **Required Fix:**
  - At `decide_pilot_a_run` (`pilot_a_routes.py:615`), if `cur_status in (WorkflowStatus.FAILED, WorkflowStatus.RECONCILIATION_REQUIRED)`, return `HTTP 409` (`run_requires_reconciliation_or_failed`) instead of re-executing and clobbering `cur_status` to `COMPLETED`.
  - In `SqliteGraphCheckpointer.execute_side_effect_once` (`state_graph.py:110-111`), when `cached.get("status") == "in_flight"`, return `{"status": "in_flight"}` (not `"deduplicated"`), and in `GovernedStateGraph.resume` (`line 156`) + `pilot_a_routes.py:653, 663`, do **not** transition to `GraphStage.COMPLETED` / `WorkflowStatus.COMPLETED` when `status == "in_flight"` (either return `HTTP 409 action_in_flight` or preserve `COMMIT_RECONCILE` / `PENDING_APPROVAL`).

#### R2-H02 (Residual H-03): NOWPayments Fourth-Door Guard Allows Unattributed `mk-<hex>` Crypto IPNs via Untrusted Payload `country` / `jurisdiction` Spoofing
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/raas/nowpayments_webhook_handler.py:126-130`, `:149-150`
- **Empirically Reproduced Proof (`NP Probe B`):**
  - Lines 126-129 set `explicit_non_vn = True` whenever the webhook JSON body contains `"country": "US"` or `"jurisdiction": "SG"`.
  - Line 149 checks `if order_low.startswith("mk-") and not (explicit_non_vn or resolved_non_vn): return True`.
  - Reproduced: `_is_vn_jurisdiction_ipn({"order_id": "mk-a1b2c3d4e5f6", "country": "US", "price_currency": "usd"}, "mk-a1b2c3d4e5f6", "mk")` returns **`False`** even when zero `TenantStore` row exists! Moreover, `workspace_id` resolves to `"mk"`, granting credits to a shared `"mk"` bucket rather than a verified non-VN tenant.
- **Required Fix:** Remove `explicit_non_vn` from the `mk-*` exemption check (`if order_low.startswith("mk-") and not resolved_non_vn: return True`) so `mk-*` checkout orders require an actual non-VN `TenantStore` record (`resolved_non_vn == True`).

---

### Medium Priority Findings (3)

#### R2-M01 (Residual H-01): React `useEffect` Race Wipes `serverActionDigest` & `serverCardSig` Immediately After `handleGatewayWebhookSync`, Re-Triggering `HTTP 409`
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/apps/dashboard/app/dashboard/opc/page.tsx:122-173`, `:257-266`, `:348-366`
- **Evidence (Traced Deterministic State Sequence):**
  1. Initial state has `runId = 'run_pilot_a_8f3a91c2b4e0'`.
  2. User clicks "Đồng bộ Gateway" -> `handleGatewayWebhookSync` (`lines 257-265`) calls `setRunId(syncRes.serverRunId)` (e.g. `'run_9a1b2c3d4e5f'`), `setServerActionDigest(syncRes.serverActionDigest)`, and `setServerCardSig(syncRes.serverCardSig)`.
  3. Changing `runId` recomputes `financials.vietQrMemo` (`OPC run_9a1b2c3d4e5f`) -> recomputes `actionPayload` (`line 138`) -> fires `useEffect([actionPayload])` (`lines 160-173`).
  4. When `computeSha256Hex(canonical).then(...)` resolves asynchronously a microtask later (`lines 166-167`), it executes **`setServerActionDigest('')` and `setServerCardSig('')`**, wiping out the server digest and card signature that `handleGatewayWebhookSync` just saved!
  5. When the user then clicks "✅ Duyệt & Gửi Báo Giá + VietQR", `serverActionDigest` is `''`, so it falls back to local `lockedDigest` and **still fails `/decide` with `HTTP 409 tamper_detected_digest_mismatch`** on the first sync!
  6. Additionally, `handleHandoffZalo` (`lines 348-366`) does not check `if (syncRes.serverRejected)` before setting `setApprovalState('revoked')`.
- **Required Fix:** Clear `serverActionDigest` and `serverCardSig` inside `ClientIntakeCard`'s `onChange` handler (`page.tsx:507-509`, when user-editable `intake` mutates) instead of inside `useEffect([actionPayload])` (which fires when `runId` updates from Gateway sync), and check `if (syncRes.serverRejected)` inside `handleHandoffZalo`.

#### R2-M02 (Residual H-04): `PilotAWorkflow` Hardcodes `local_endpoint=""` on `SelectiveRouter` and Discards Router Confidence / Extracted Fields
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/pilot_a.py:98`, `:122-130` and `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/selective_router.py:125`
- **Evidence (Empirically Reproduced):**
  - `PilotAWorkflow.__init__` (`pilot_a.py:98`) instantiates `SelectiveRouter(self.usage, self.profile.services, local_endpoint="")`. Because `"" is not None`, `SelectiveRouter.__init__` (`selective_router.py:125`) skips `os.getenv("MLX_BASE_URL") or os.getenv("LITELLM_BASE_URL")` even when configured in production (`wf2.router.local_endpoint == ''` verified in runtime probe)!
  - Furthermore, `pilot_a.py:122` only reads `.citations` from `self.router.route(...)` and ignores `route_res.confidence` when `event.extraction_confidence` is left at default.
- **Required Fix:** Pass `local_endpoint=None` by default in `PilotAWorkflow` (or only disable network lookup when not configured via env) so `MLX_BASE_URL` / `LITELLM_BASE_URL` works in production without breaking offline tests where those env vars are unset.

#### R2-M03 (Residual M-04): `SelectiveRouter` Still Permanently Reserves `50.00 VND` Budget When `cloud_fallback_fn is None` and `hard_budget_limit` Is Set
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/selective_router.py:167-170`
- **Evidence:**
  ```python
  if self.cloud_fallback_fn is None:
      if (eff_lim := hard_budget_limit if hard_budget_limit is not None else self.hard_budget_limit) is not None and self.fail_closed_budget_enforcement and not self.usage_ledger.reserve_budget(...):
          raise PermissionError("Budget reservation failed (fail-closed)")
      return SelectiveRouteResult("low_confidence_halt", ...)
  ```
  `UsageLedger.reserve_budget` writes a permanent `UsageStage.RESERVED` ledger row for `50.00 VND` into `opc_usage`. Executing `reserve_budget` when `self.cloud_fallback_fn is None` charges the tenant's budget ledger for a cloud fallback call that never happens! If the intent was only to check whether existing spend already exceeded `eff_lim`, query `aggregate_run_costs` (or skip reservation entirely when `cloud_fallback_fn is None`, since `low_confidence_halt` performs zero paid external calls).
- **Required Fix:** Remove `self.usage_ledger.reserve_budget(...)` from the `if self.cloud_fallback_fn is None:` branch so zero budget is debited when no cloud call is executed.

---

### Low Priority Findings (1)

#### R2-L01: `OPCEngine.execute_approved_action` Uses `connector.dispatch.__code__` Which Crashes on `functools.partial`, Callable Objects, or `unittest.mock` Wrappers
- **Location:** `/Users/macbook/mekong-cli-atoz-strategy-e/src/opc/engine.py:168`
- **Evidence:** `"now" in connector.dispatch.__code__.co_varnames` raises `AttributeError: __code__` whenever `connector.dispatch` is a callable class instance, `functools.partial`, or `MagicMock`/`patch(..., wraps=...)` (encountered directly during runtime probing).
- **Required Fix:** Use `inspect.signature(connector.dispatch).parameters` (catching `(TypeError, ValueError)`).

---

## Round-2 Action Checklist to Reach `APPROVED FOR PR / MERGE`

1. **[Critical — R2-C01]** In `src/api/pilot_a_routes.py` (`POST /webhook/zalo`), strip `card_sig` and `sig=` URLs from unauthenticated webhook responses (`return card_sig/card_url only when is_owner_authed or (tenant_cfg is None and not _is_production())`), and enforce `is_owner_authed or valid X-ZEvent-Mac` whenever `tenant_cfg is not None or _is_production()` (failing closed with `401/503` if `ZALO_OA_SECRET_KEY` is unset).
2. **[High — R2-H01]** Block `/decide` replay from clobbering `FAILED` / `RECONCILIATION_REQUIRED` runs to `COMPLETED` in legacy mode (`pilot_a_routes.py`), and return `{"status": "in_flight"}` (not `"deduplicated"`) in `SqliteGraphCheckpointer.execute_side_effect_once` so concurrent callers cannot prematurely mark an uncertain/failing run `COMPLETED`.
3. **[High — R2-H02]** Require `resolved_non_vn` (verified `TenantStore` row) for `mk-*` order IDs in `src/raas/nowpayments_webhook_handler.py:149` instead of trusting payload `country`/`jurisdiction`.
4. **[Medium — R2-M01..R2-M03]** Move `setServerActionDigest('')` / `setServerCardSig('')` out of `useEffect([actionPayload])` into `ClientIntakeCard.onChange` + handle `serverRejected` in `handleHandoffZalo` (`apps/dashboard/app/dashboard/opc/page.tsx`); pass `local_endpoint=None` in `PilotAWorkflow.__init__` (`src/opc/pilot_a.py:98`); and stop calling `reserve_budget` when `cloud_fallback_fn is None` (`src/opc/selective_router.py:167-169`).
5. **[Low — R2-L01]** Replace `connector.dispatch.__code__.co_varnames` with `inspect.signature(connector.dispatch).parameters` in `src/opc/engine.py:168`.
