# Open-Core Foundation Enforcement — tasks

**Repo:** Mekong CLI v6.0 (Python) · **Branch:** `feat/trade-transport-remedies-suite-phases-163-166` · **Date:** 2026-10-21

Step 1 verdict: [step-01-opencore-verdict.md](step-01-opencore-verdict.md) · Phased plan: [plan.md](plan.md) · Canonical blueprint: [../company-blueprint/plan.md](../company-blueprint/plan.md)

**`.mekong/company.json` — NO CHANGE NEEDED.** Already `open_core_25_steps_aligned: true` with empty `binh_phap_state.revenue_events` (Verified: `audit_blueprint('.')` → company_json_clean=True, synchronized=True, 25/25).

**Verdict today:** `completion_pct=100.0` but `verdict=BLOCKED_SECRET_OR_BOUNDARY_LEAK`. Sole gate blocker: `verify_filesystem_hygiene('.').missing_items == ('git-index:tracked-private-files=3',)`. Tests: `tests/test_idea_deep_opencore_brainstorm.py` = 5 failed / 1 passed.

## Phase A — Green the gate (community) · SAFE TO RUN NOW

- [ ] `git rm --cached apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py`
- [ ] `git rm --cached apps/nhipdieuxanh-orchestrator/mock-services/ai-service/requirements.txt`
- [ ] `git rm --cached apps/nhipdieuxanh-orchestrator/tests/e2e/lead-flow.spec.ts`
- [ ] Add `apps/nhipdieuxanh-orchestrator/` to `.gitignore` so the 3 files stay untracked (currently no ignore rule matches them)
- [ ] Leave `apps/dashboard/**` (93 tracked files) ALONE — intentionally public via `!apps/dashboard/` at `.gitignore:120`
- [ ] Confirm `verify_filesystem_hygiene('.').missing_items == ()` and `audit_repository('.')` verdict flips to `PUBLIC_GITHUB_SAAS_READY`

## Phase B — Fix the 4 LOC violations (community) · SAFE TO RUN NOW

Each split must preserve the import surface (re-export from a stable facade; never rewrite callers).

- [ ] `src/core/health_reporter.py` 188 → ≤180 (boundaries: `HealthMetrics`, `HealthReport`, `HealthReporter`, `get_health_reporter`, `record_command`, `report_health`)
- [ ] `src/core/autonomous.py` 195 → ≤180
- [ ] `src/core/dag_scheduler.py` 186 → ≤180
- [ ] `src/core/api_adapter.py` 183 → ≤180
- [ ] Confirm no other guarded folder/file is over the limit (full scan already run: only these 4 fail; `src/components`, `src/lib`, `apps/dashboard/src` all clean)

## Phase E — Make the gate honest (community) · SAFE TO RUN NOW

- [ ] In `OpenCoreSaasReadinessEngine.audit_repository`, replace the hardcoded `jwt_license_gate_enforced=True` / `mcu_http402_billing_wired=True` defaults with real computed checks
- [ ] Actually assert a signed key round-trips through the gate, and that a 402 is returned on zero balance
- [ ] Confirm the engine and the CLI path (`src/cli/commands/opencore_saas_restructuring_command.py:65-75`) no longer disagree on the verdict

## Phase C — Polar removal · BLOCKED ON FOUNDER APPROVAL

Sequence: **disable-then-remove**; NOWPayments IPN must remain the verified active rail throughout and must never break.

- [ ] Commit the in-flight rewrite of `src/raas/checkout_router.py` → provider-agnostic NOWPayments / VietQR
- [ ] Remove `"/v1/polar/"` from `_CSRF_SKIP_PREFIXES` in `src/middleware/csrf_middleware.py`
- [ ] Remove the `polar-billing` vendor entry in `src/core/vendor_engine.py`
- [ ] `src/services/polar_client.py` + `src/services/polar_client_models.py` and their callers: `src/cli/commands/revenue_command.py`, `src/api/vn_pricing_routes.py`
- [ ] `src/cli/_app_setup/groups_19.py`, `src/core/task_classifier.py`, `src/core/binh_phap/standards.py`, `src/core/binh_phap/reactions.py`, `src/harness/agents/classifier.py`, `src/core/opencore/phase_559_opencore_25_step_catalog.py`
- [ ] Untracked TS: `packages/mekong-engine/src/raas/polar-webhook.ts`, `packages/mekong-engine/src/routes/raas-webhooks.ts`, `packages/mekong-engine/src/routes/system-routes.ts` + tests
- [ ] **Founder decision:** `apps/dashboard/app/api/polar/webhook/route.ts` is tracked AND publicly visible — deleting a public webhook route is a product call, not cleanup. Do not delete without sign-off.
- [ ] DO NOT touch the IMO **Polar Code** (ice navigation) files: `src/core/maritime/phase_339_polar_code_polaris_rio.py`, `src/core/maritime_polar_wash_ev_salvage_engine.py`, `maritime_polar_wash_ev_salvage_command.py` and their tests — false positives

## Phase D — Collapse 6 tier namespaces to BASIC | PREMIUM | ENTERPRISE | MASTER · BLOCKED ON FOUNDER APPROVAL

Target: `BASIC $199` / `PREMIUM $399` / `ENTERPRISE $799` / `MASTER $4,999` one-time.

- [ ] One canonical tier constant module; every namespace imports it or is deleted. The six today:
  - [ ] `src/seed/config/tiers_models.py` TierKey (free/trial/starter/growth/pro/enterprise)
  - [ ] `src/raas/billing_tiers.py` CREDIT_MAP (free/starter/growth/scale/pro)
  - [ ] `src/lib/raas-gate.ts` (free/pro/enterprise) — non-cryptographic 4-hex checksum, prefix-sniffing, no HMAC
  - [ ] `packages/license-sdk/src/core/tiers.ts` (free/starter/pro/enterprise) — **untracked, commit it**; its `verifier.ts` has the real HMAC-SHA256
  - [ ] `src/core/tier_fallback_chain.py` (BASIC/PREMIUM/ENTERPRISE/MASTER) — the intended canonical set
  - [ ] `engine/license/jwt_license_generator.py::_get_tier_quotas` (free/trial/pro/enterprise)
- [ ] `tiers_models.py::aliases()` must stop folding `MASTER→pro` and `ENTERPRISE→pro` (a $4,999 buyer would silently get PRO entitlements)
- [ ] Remove the silent `quotas.get(tier, quotas["free"])` fallback — unknown tier must fail closed, not degrade to free
- [ ] `src/middleware/license_gate.py`: remove the `claims.get("tier", "starter")` silent default and actually enforce tier entitlement (today it only checks `is_active()` + non-zero credits)
- [ ] `packages/license-sdk/src/core/verifier.ts`: remove the DEV secret fallback `'openclaw-dev-secret-do-not-use-in-production'` — must fail closed when `OPENCLAW_LICENSE_SECRET` is unset
- [ ] Add tests: a MASTER key must NOT receive PRO features; an unknown tier must NOT receive free features

## Verification (must be green before reporting done)

- [ ] `python3 -m pytest tests/test_idea_deep_opencore_brainstorm.py -q` → target 6/6 passed (today 1/6)
- [ ] `python3 -m pytest tests/test_company_blueprint_sync.py -q` → must stay 5/5 passed
- [ ] `python3 -m pytest tests/ -q` → full suite, several minutes (run in background; do not ignore failures)
- [ ] Re-run the readiness engine and record the new verdict + `missing_items`
- [ ] `python3 -m ruff check src/ tests/` clean

## Explicit Non-Goals

- No pricing change to tiers already sold; no revenue/MRR/customer/compliance claims (none are measured)
- No change to the Setup Wizard, Telegram Bot, or NOWPayments IPN protected flows
- No dashboard redesign, no IMO Polar Code changes, no secrets committed
- A green readiness verdict is NOT evidence monetization is enforceable until Phases C, D land
