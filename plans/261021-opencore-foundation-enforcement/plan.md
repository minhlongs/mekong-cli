# Open-Core Foundation Enforcement — plan

- **Repo:** Mekong CLI v6.0 (Python). **Branch:** `feat/trade-transport-remedies-suite-phases-163-166`. **Date:** 2026-10-21.
- Step 1 verdict: [step-01-opencore-verdict.md](step-01-opencore-verdict.md)
- Canonical blueprint: [../company-blueprint/plan.md](../company-blueprint/plan.md)

**No `company.json` change required.** `.mekong/company.json` already carries `open_core_25_steps_aligned: true` with an empty `binh_phap_state.revenue_events` — leave it as is, do not edit. `Verified: audit_blueprint('.') → company_json_clean=True, synchronized=True, 25/25`.

## Verified state (commands run 2026-10-21)

| Check | Result |
| --- | --- |
| `audit_blueprint('.')` | matched_steps_count=25/25, three_lenses_present=True, company_json_clean=True, synchronized=True |
| `audit_repository('.')` | completion_pct=100.0, verdict=BLOCKED_SECRET_OR_BOUNDARY_LEAK, safe_for_public_github_push=False, saas_paywall_active=False |
| `verify_filesystem_hygiene('.')` | missing_items == `('git-index:tracked-private-files=3',)` |
| Secrets / keys | leaked_secrets_detected=0; no `.env`/`.pem`/`.key` tracked; all other hygiene checks pass |
| `pytest tests/test_idea_deep_opencore_brainstorm.py` | 5 failed, 1 passed |

The three tracked private files are the SOLE blocker for the public-push gate.

## Decision already made

Edition placement is founder-chosen and not reopened here: the license **GATE ships in `community`** (a working funnel is what earns GitHub trust); **ENFORCEMENT of paid tiers is `cloud`**. Step 1 verdict: Community GO; Cloud and Enterprise NO-GO today; overall GO conditional on the three blockers below.

## The 4 LOC violations (Verified, measured — exactly four)

| # | File | LOC | Limit |
| --- | --- | --- | --- |
| 1 | `src/core/health_reporter.py` | 188 | > 180 |
| 2 | `src/core/autonomous.py` | 195 | > 180 |
| 3 | `src/core/dag_scheduler.py` | 186 | > 180 |
| 4 | `src/core/api_adapter.py` | 183 | > 180 |

`Verified`: a scan of every other guarded folder (`src/core/opencore`, `src/raas`, `src/api`, `src/middleware`, `src/seed`, ~60 dirs total as listed in the test) found ZERO further >180 violations; `src/components`, `src/lib`, `apps/dashboard/src` have zero >175 violations. The guard folder list and the explicit ~200-file `core_checked`/`cmd_checked` lists live in `tests/test_idea_deep_opencore_brainstorm.py::test_loc_invariants_for_deep_brainstorm_modules`.

## CRITICAL SCOPING INSIGHT — a green gate is not a shippable paid edition

The readiness engine's two monetization flags are **defaults that nothing verifies**:

```python
OpenCoreSaasReadinessEngine.audit_repository(
    cls, repo_root, completed_steps=25,
    jwt_license_gate_enforced=True,
    mcu_http402_billing_wired=True,
)
```

Both default `True` and the verdict is computed from them without checking them. **The gate will go GREEN once hygiene is clean, even if the tier namespaces and Polar are still broken.** A green verdict is therefore NOT evidence that monetization is enforceable — treat Phases C and D as still outstanding after the gate flips.

Divergence to note: the CLI path `src/cli/commands/opencore_saas_restructuring_command.py:65-75` DOES pass computed `jwt_gate` / `mcu_billing` values, so the CLI can report `MONETIZATION_GATE_INCOMPLETE` while the engine reports `READY`. Phase E closes this.

---

## PHASE A — Green the gate (community). Safe to execute immediately.

- **Files:** `git rm --cached` exactly 3 — `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/main.py`, `apps/nhipdieuxanh-orchestrator/mock-services/ai-service/requirements.txt`, `apps/nhipdieuxanh-orchestrator/tests/e2e/lead-flow.spec.ts`. Add an explicit `.gitignore` entry for `apps/nhipdieuxanh-orchestrator/` (no ignore rule currently matches these files, so they would otherwise re-track).
- **Do NOT touch `apps/dashboard/`** — its 93 tracked files are intentionally public (`.gitignore:120` = `!apps/dashboard/`).
- **Quirk, do not "fix":** the trailing `app/` rule re-matches `apps/dashboard/app/**` for *untracked* files, which is why `git check-ignore` lists them as UNCOVERED while they are correctly tracked.
- **LOC:** per-file < 180 maintained (no file grows past the limit).
- **Edition:** community.
- **Done:** `verify_filesystem_hygiene('.').missing_items == ()` and `audit_repository('.')` verdict == `PUBLIC_GITHUB_SAAS_READY`.
- **Risk:** Low. Untracking is reversible; `.gitignore` entry is additive.

## PHASE B — Repair the 4 LOC violations (community). Safe to execute immediately.

- **Files:** the four above. Each split must **preserve public API / import surface**.
- **Preferred pattern:** extract internals into focused modules and re-export from a stable facade, rather than rewriting callers.
- **`health_reporter.py` is class-boundary rich** — `HealthMetrics`, `HealthReport`, `HealthReporter`, `get_health_reporter`, `record_command`, `report_health` (lines ~27/47/54/176/183/187) — a natural split, but the module-level names must remain importable.
- **Edition:** community.
- **Done:** `test_loc_invariants_for_deep_brainstorm_modules` passes; no import breakage in the whole suite.
- **RISK:** these four are imported widely; a split that drops a re-export breaks call sites across the repo. Mitigation: facade re-export + full-suite run before commit.

## PHASE C — Polar removal, FULL scope. BLOCKED-ON-FOUNDER-APPROVAL for (b)-(f).

The handoff understated scope (2 files). Verified inventory of the real surface:

| Item | Location |
| --- | --- |
| (a) in-flight uncommitted rewrite → provider-agnostic NOWPayments / VietQR | `src/raas/checkout_router.py` |
| (b) `/v1/polar/` in `_CSRF_SKIP_PREFIXES` | `src/middleware/csrf_middleware.py:31` |
| (c) `polar-billing` vendor entry | `src/core/vendor_engine.py:52` |
| (d) ADDITIONAL tracked files not in original scope | `src/core/task_classifier.py:74`, `src/core/binh_phap/standards.py`, `src/core/binh_phap/reactions.py`, `src/core/opencore/phase_559_opencore_25_step_catalog.py`, `src/cli/_app_setup/groups_19.py`, `src/cli/commands/revenue_command.py`, `src/polymarket/billing.py`, `src/harness/agents/classifier.py`, `src/api/vn_pricing_routes.py`, `src/services/polar_client.py` |
| (e) untracked (not in git at all) | `packages/mekong-engine/src/raas/polar-webhook.ts`, `packages/mekong-engine/src/routes/raas-webhooks.ts`, `packages/mekong-engine/src/routes/system-routes.ts` + its test |
| (f) TRACKED-PUBLIC webhook route | `apps/dashboard/app/api/polar/webhook/route.ts` |

**False-positive trap (do NOT delete):** `src/core/maritime/phase_339_polar_code_polaris_rio.py`, `src/core/maritime_polar_wash_ev_salvage_engine.py`, `maritime_polar_wash_ev_salvage_command.py` are the IMO **Polar Code** (ice navigation) — unrelated to Polar.sh.

**Founder sign-off required for (b)-(f):** these touch a live revenue path and a public app. (f) sits inside the intentionally-public dashboard, so removing it is a product decision, not cleanup. Phase A+B remain safe to run while (b)-(f) await approval.

**Sequencing constraint:** a webhook endpoint that live traffic still posts to must not be deleted without migration. Order is disable-then-remove, and NOWPayments IPN must remain the active verified rail throughout (must not break).

- **Edition:** cloud (enforcement-side removal); (a) is the committed foundation for it.
- **Done:** zero Polar.sh references in tracked Python/TS except items held for founder decision; NOWPayments IPN still green.

## PHASE D — Tier namespace collapse to canonical `BASIC|PREMIUM|ENTERPRISE|MASTER` ($199/$399/$799/$4,999 one-time). BLOCKED-ON-FOUNDER-APPROVAL.

`Verified`: there are **SIX** incompatible namespaces, not five.

| # | Namespace | Contents |
| --- | --- | --- |
| 1 | `src/seed/config/tiers_models.py` `TierKey` | free/trial/starter/growth/pro/enterprise, $0/$0/$49/$149/$499/$0; `aliases()` (~30-57) maps `BASIC→starter`, `PREMIUM→growth`, `MASTER→pro`, `ENTERPRISE→pro` |
| 2 | `src/raas/billing_tiers.py` `CREDIT_MAP` | free(50)/starter(300)/growth(1200)/scale(3500)/pro(7000) |
| 3 | `src/lib/raas-gate.ts` | free/pro/enterprise; NON-cryptographic 4-hex `generateChecksum`, prefix-sniffing `parseTier` — no HMAC, forgeable |
| 4 | `packages/license-sdk/src/core/tiers.ts` | free/starter/pro/enterprise ($0/$29/$99/$299). UNCOMMITTED (untracked, NOT gitignored) |
| 5 | `src/core/tier_fallback_chain.py` | BASIC/PREMIUM/ENTERPRISE/MASTER — the INTENDED canonical set |
| 6 | `engine/license/jwt_license_generator.py::_get_tier_quotas` | free/trial/pro/enterprise + `quotas.get(tier, quotas["free"])` silent default |

**The bug that matters:** `MASTER→pro` and `ENTERPRISE→pro` means a MASTER ($4,999) buyer is silently served PRO ($799) entitlements; `quotas.get(tier, quotas["free"])` silently degrades an unknown tier to free. **Both must fail closed.** Related silent defaults: `src/middleware/license_gate.py` sets `request.state.tier = claims.get("tier", "starter")` and only checks `is_active()` + non-zero credits — never tier entitlement.

**Bonus `Verified` find:** `packages/license-sdk/src/core/verifier.ts` is genuinely real crypto (HMAC-SHA256 + `timingSafeEqual` + expiry), secret from `process.env['OPENCLAW_LICENSE_SECRET']` with a DEV fallback `'openclaw-dev-secret-do-not-use-in-production'` — that fallback must fail closed for a paid edition. **Also commit `packages/license-sdk/`** (untracked but NOT gitignored — `Verified`) since the real HMAC lives there.

- **Edition:** cloud (enforcement); gate/constants themselves are community.
- **Done:** one canonical tier constant module; every other namespace imports it or is deleted; `aliases()` no longer collapses MASTER/ENTERPRISE; zero silent tier defaults; a test proving a MASTER key does not receive PRO features and an unknown tier does not receive free features.
- **RISK:** high — touches entitlement math and live keys. No pricing change to tiers already sold.

## PHASE E — Make the gate honest (community, small). Safe to execute immediately.

- **File:** `OpenCoreSaasReadinessEngine.audit_repository` — replace the hardcoded `jwt_license_gate_enforced=True` / `mcu_http402_billing_wired=True` defaults with real computed checks (e.g. actually round-trip a signed key through the gate; actually assert a 402 on zero balance).
- **Edition:** community.
- **Done:** a green readiness verdict means what it says; the CLI vs engine divergence above no longer exists.
- **RISK:** Low, but this is what makes the gate trustworthy — do it before treating verdict `PUBLIC_GITHUB_SAAS_READY` as a milestone.

## Execution order

**A → B → E → (gate flips green) → C → D, with C(b)-(f) and D gated on founder approval.** A, B and E are safe now; the green gate must not be read as monetization being enforceable until C and D land.
