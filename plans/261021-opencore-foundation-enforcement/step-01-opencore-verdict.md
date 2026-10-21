# /idea Step 1 — Open-Core Verdict (repo = Mekong CLI v6.0, Python)

**Scope correction (important):** The `/idea` command text targets Sophia AI Factory (Next.js 16 + Cloudflare Workers/D1/R2/KV + TS, `src/seed/*.ts`, `@Sophia_Bbot`, sophia.agencyos.network). This checkout is **Mekong CLI v6.0**, a Python codebase. `apps/sophia-ai-factory/` exists but is gitignored (`.gitignore:119` = `apps/*`) and contains only `node_modules` — no `src/seed/`, no open-core manifest. The TS modules the command names (`src/seed/config/open-core-manifest.ts`, `src/seed/security/raas-license-verifier.ts`, `src/tree/open-core/workspace-portability-store.ts`, `/api/open-core/portability`) **do not exist here and are not reachable.** The open-core machinery that does exist here is Python: `src/cli/idea_commands.py`, `src/core/opencore/*`, `src/api/opencore_status_routes.py`. This verdict runs the pipeline that actually exists in this repo. Note there is no `make`/venv requirement for any step below.

**Idea analyzed (founder-selected):** "Open-core foundation fix" — make the Community→Cloud→Enterprise funnel technically enforceable. Edition placement was chosen by the founder: the license gate ships in `community` (proves the funnel is real, builds GitHub trust); enforcement of paid tiers is `cloud`.

## Truthfulness labels used
`Verified` = backed by a command run in this repo today. `Hypothesis` = needs customer validation. `Target` = directional goal. No fabricated numbers anywhere.

## Verified evidence (commands run 2026-10-21)

| # | Claim | Label | Evidence |
|---|---|---|---|
| 1 | Blueprint 25/25 synchronized | Verified | `OpenCoreSaasReadinessEngine.audit_blueprint('.')` → matched_steps_count=25/25, three_lenses_present=True, company_json_clean=True, synchronized=True. Files: `plans/company-blueprint/{plan.md,tasks.md,brainstorm-25-step-opencore-saas.md}`, `.mekong/company.json` |
| 2 | Open-core steps 100% complete | Verified | `audit_repository('.')` → `completion_pct = 100.0` |
| 3 | Readiness verdict = BLOCKED | Verified | `audit_repository('.')` → `verdict = BLOCKED_SECRET_OR_BOUNDARY_LEAK` |
| 4 | Exactly ONE blocking cause | Verified | `verify_filesystem_hygiene('.').missing_items` → `('git-index:tracked-private-files=3',)` — nothing else. gitignore_valid/env_example_valid/license_mit_valid/contributing_cla_valid all pass; `leaked_secrets_detected = 0` |
| 5 | The 3 tracked private files | Verified | `git ls-files apps/` → 96 tracked files; 93 under `apps/dashboard/`, 3 NOT under dashboard: `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py`, `.../requirements.txt`, `apps/nhipdieuxanh-orchestrator/tests/e2e/lead-flow.spec.ts`. `git ls-files billing/` → 0. No `.env`/`.pem`/`.key` tracked (all 0) |
| 6 | SIX incompatible tier namespaces | Verified | (a) `src/seed/config/tiers_models.py` TierKey enum = `free/trial/starter/growth/pro/enterprise`, prices $0/$0/$49/$149/$499/$0, and `aliases()` (lines 30-57) maps `BASIC→starter`, `PREMIUM→growth`, `MASTER→pro`, `ENTERPRISE→pro` — i.e. canonical 4-tier names collapse onto a *different, conflicting* price ladder. (b) `src/raas/billing_tiers.py` CREDIT_MAP = `free/starter/growth/scale/pro`. (c) `src/lib/raas-gate.ts` = `free/pro/enterprise`, non-cryptographic 4-hex checksum (`generateChecksum`), prefix-sniffing `parseTier`, no HMAC. (d) `packages/license-sdk/src/core/tiers.ts` = `free/starter/pro/enterprise` ($0/$29/$99/$299). (e) `src/core/tier_fallback_chain.py` = `BASIC/PREMIUM/ENTERPRISE/MASTER` (the intended canonical set). (f) **the real JWT license path** `engine/license/jwt_license_generator.py::_get_tier_quotas` = `free/trial/pro/enterprise`, with a silent `quotas.get(tier, quotas["free"])` fallback |
| 6b | The MASTER bug | Verified | `aliases()` folds `MASTER→pro` and `ENTERPRISE→pro`, so a MASTER ($4,999) buyer would be silently served PRO entitlements. `src/middleware/license_gate.py` also sets `request.state.tier = claims.get("tier", "starter")` and only ever checks `is_active()` + non-zero credits — it never checks tier entitlement at all. Both must fail closed |
| 7 | license-sdk is UNCOMMITTED | Verified | `git check-ignore packages/license-sdk/src/core/verifier.ts` → NOT ignored, but `git ls-files packages/` shows nothing → untracked entirely. It has real HMAC-SHA256 + `timingSafeEqual` + expiry in `packages/license-sdk/src/core/verifier.ts`, secret from `process.env['OPENCLAW_LICENSE_SECRET']` with a DEV fallback `'openclaw-dev-secret-do-not-use-in-production'` |
| 8 | Polar removal is in-flight only | Verified | working tree `git diff src/raas/checkout_router.py` rewrites the docstring/body to provider-agnostic NOWPayments and imports `from src.raas.billing_tiers import CREDIT_MAP, tier_from_reference`, but change is UNCOMMITTED. `src/middleware/csrf_middleware.py:31` still lists `"/v1/polar/"` in `_CSRF_SKIP_PREFIXES`. `src/core/vendor_engine.py:52` still registers `polar-billing` |
| 9 | `/idea` test suite currently RED | Verified | `python3 -m pytest tests/test_idea_deep_opencore_brainstorm.py` → **5 failed, 6 passed**. Assertion failures: `'BLOCKED_...' == 'PUBLIC_GITHUB_SAAS_READY'` (causes 1-4) and `src/core/health_reporter.py: 188 LOC` vs ≤180 invariant (cause 5) |
| 10 | health_reporter LOC violation | Verified | 188 > 180, breaks `test_loc_invariants_for_deep_brainstorm_modules` |
| 11 | Nested Sophia app unusable | Verified | `ls apps/sophia-ai-factory/` → only `node_modules`; `src/seed/security/` and `src/seed/config/` absent |

Not verified / unknown (state explicitly, do not assume): any paying customers, MRR, retention, CAC/LTV, conversion, third-party certifications. None have been measured.

## Step 1 Output — GO / NO-GO by edition

**Community (Apache/MIT core): GO.** The community core is already public-safe on every hygiene dimension *except* the 3 tracked client files (cause #5), and leaked secrets are 0. Removing those 3 files from the index is the entire delta.

**Cloud ($199/$399/$799): NO-GO today.** Monetization gate incomplete because the license gate cannot enforce it: the HMAC verifier exists (`packages/license-sdk`) but is uncommitted, un-imported by `src/`, and written against a 4th incompatible tier namespace. Do not price, sell, or publish cloud tiers until the gate enforces them.

**Enterprise / Master ($4,999 one-time): NO-GO today.** Same blocker, plus the canonical 4-tier name is not the one that resolves — `aliases()` maps `MASTER→pro`, so a MASTER buyer would be silently served a PRO entitlement.

**Target-state verdict: GO, conditional on the 3 blockers below.** This is not a NO-GO on the idea; the 25-step blueprint is already 100% complete and the hygiene gate is 1 file-level fix from green. The conditional is about *enforcement machinery*, not product-market fit.

**PLG upgrade trigger (Hypothesis — needs customer validation):** self-hosted user hits the ceiling when they need multi-tenant subaccount orchestration or 24/7 queueing that a single-box BYOK setup cannot carry. No measured conversion data exists to confirm this trigger; it is a design assumption.

**Technical feasibility: FEASIBLE.** Everything required is local to this Python repo + the already-written TS verifier: no Cloudflare/Inngest/Next.js dependency is needed to make the gate real. The gate is `community`; enforcement config is `cloud` — which is exactly the boundary the founder selected.

## The three blockers (each is the fix in one sentence)
1. **Public index:** untrack `apps/nhipdieuxanh-orchestrator/**` (3 files) via `git rm --cached`, and add an explicit `.gitignore` entry so they stay untracked. **Do NOT touch `apps/dashboard/`** — its 93 tracked files are *intentionally* public: `.gitignore:119-122` blanket-ignores `apps/*` with an explicit `!apps/dashboard/` negation and `!apps/dashboard/.env.local.example` carve-out. No secret, `.pem`, or `.key` is tracked there.
2. **Tier namespaces:** collapse the **6** namespaces onto the canonical `BASIC | PREMIUM | ENTERPRISE | MASTER` with prices $199/$399/$799/$4,999, preserving `packages/license-sdk`'s real HMAC. `aliases()` must not fold `MASTER→pro`; the JWT quota fallback must not silently serve free on an unknown tier.
3. **Polar:** commit the checkout_router rewrite, drop `/v1/polar/` from `_CSRF_SKIP_PREFIXES`, and remove the `polar-billing` vendor entry. This is broader than first scoped — see Blocker 3 detail below.

Proceed to [plan.md](plan.md) for the phased implementation.

## Blocker 3 detail — Polar is far wider than 2 files (Verified)

Verified Polar surface, well beyond the three items in Step 1's original scope:
- **In-flight:** uncommitted rewrite of `src/raas/checkout_router.py` → provider-agnostic NOWPayments / VietQR.
- **Live code refs (tracked):** `src/middleware/csrf_middleware.py:31` (`/v1/polar/` in `_CSRF_SKIP_PREFIXES`), `src/core/vendor_engine.py:52` (`polar-billing` vendor), plus `src/services/polar_client.py`, `src/cli/commands/revenue_command.py`, `src/api/vn_pricing_routes.py`, `src/cli/_app_setup/groups_19.py`, `src/core/task_classifier.py:74`, `src/core/binh_phap/standards.py`, `src/core/binh_phap/reactions.py`, `src/harness/agents/classifier.py`, `src/core/opencore/phase_559_opencore_25_step_catalog.py`.
- **Untracked (never committed):** `packages/mekong-engine/src/raas/polar-webhook.ts`, `packages/mekong-engine/src/routes/raas-webhooks.ts`, `packages/mekong-engine/src/routes/system-routes.ts` and its test.
- **Tracked and publicly visible:** `apps/dashboard/app/api/polar/webhook/route.ts` — inside the intentionally-public dashboard. Deleting a public webhook route is a product decision requiring founder sign-off, not a cleanup task.
- **False positives to leave alone:** `src/core/maritime/phase_339_polar_code_polaris_rio.py`, `src/core/maritime_polar_wash_ev_salvage_engine.py`, `maritime_polar_wash_ev_salvage_command.py` and their tests are the IMO **Polar Code** (ice navigation) — unrelated to Polar.sh. Do not delete them.

## Blocker 3 requires founder approval

Removing a webhook that live traffic may still post to is a revenue-path decision, so Phase C of the implementation plan is marked blocked-on-founder-approval. Phases A (green the gate) and B (4 LOC splits) are safe to execute immediately. Polar removal should be **disable-then-remove**, with NOWPayments IPN remaining the verified active rail throughout — that protected flow must never break.

## Critical caveat — a green gate is not proof monetization is enforceable

`OpenCoreSaasReadinessEngine.audit_repository` takes `jwt_license_gate_enforced=True` and `mcu_http402_billing_wired=True` as **defaults that nothing verifies**, so the verdict will read `PUBLIC_GITHUB_SAAS_READY` once hygiene is clean *even if the tier namespaces and Polar rails are still broken*. Meanwhile the CLI path (`src/cli/commands/opencore_saas_restructuring_command.py:65-75`) does pass computed values and can report `MONETIZATION_GATE_INCOMPLETE`. So the engine going green is **not** evidence that a paid edition can be enforced, and the two surfaces can disagree. Phase E of the plan replaces those hardcoded defaults with real checks.
