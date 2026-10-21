# Verified baseline (commands run 2026-10-21 ~21:00, ROOT=/Users/macbook/mekong-cli)

## Gates
| Check | Result | Command |
|---|---|---|
| Blueprint sync | 25/25 matched, three_lenses_present=True, company_json_clean=True, synchronized=True | `OpenCoreSaasReadinessEngine.audit_blueprint('.')` |
| Hygiene | `missing_items == ()` — CLEAN | `verify_filesystem_hygiene('.')` |
| Readiness verdict | `PUBLIC_GITHUB_SAAS_READY`, completion 100.0, public_push=True, paywall=True | `audit_repository('.')` |
| Test suite | **6 passed, 0 failed** (242 warnings) | `pytest tests/test_idea_deep_opencore_brainstorm.py` |
| Ruff (opencore + idea_commands) | All checks passed | `ruff check src/core/opencore/ src/cli/idea_commands.py` |

## Facts that CHANGED since plans/261021-opencore-foundation-enforcement (20:14)
1. The 3 tracked private files are untracked and stay untracked. `.gitignore:123` = `apps/nhipdieuxanh-orchestrator/`. `git ls-files apps/ billing/` → 0 non-dashboard. Hygiene blocker resolved.
2. `packages/license-sdk/` IS TRACKED — 25 files, including `src/core/tiers.ts` and `src/core/verifier.ts`. The 20:14 plan's "UNCOMMITTED, must also commit packages/license-sdk" is stale.
3. The four LOC violations are resolved: `src/core/autonomous.py` 195→174, `src/core/dag_scheduler.py` 186→158, `src/core/api_adapter.py` 183→140. (`health_reporter.py` 188 measured earlier in-session at 171, also green.) `test_loc_invariants_for_deep_brainstorm_modules` PASSES.

## Facts that still HOLD (re-verified)
1. `audit_repository` signature: `(cls, repo_root, completed_steps=25, jwt_license_gate_enforced=True, mcu_http402_billing_wired=True)`. Both monetization flags are caller-supplied defaults, never computed. `evaluate()` returns READY whenever hygiene is clean and those two are truthy. A green verdict is NOT evidence monetization is enforceable.
2. `src/cli/commands/opencore_saas_restructuring_command.py:55-58` — `jwt_gate` and `mcu_billing` are `typer.Option(True, ...)`, i.e. operator-asserted flags, not computed. Only `verified`/`--verify-fs` swaps in a live hygiene call, and even then the two monetization args stay at their True defaults. CLI and engine cannot diverge as claimed in the 20:14 plan; both are equally weak.
3. MASTER bug still live — `src/seed/config/tiers_models.py` `aliases()` maps `MASTER→pro` AND `ENTERPRISE→pro`.
4. `src/lib/raas-gate.ts:97` `generateChecksum` is a non-cryptographic 32-bit FNV-ish hash, 4 hex chars — forgeable. `parseTier` prefix-sniffs `raas_ent_`/`REP-`/`raas_pro_`/`sk-raas-`/`RPP-` with no signature verification.
5. `engine/license/jwt_license_generator.py:336` `quotas.get(tier, quotas["free"])` — silent free degradation on unknown tier.
6. `src/middleware/license_gate.py` — sets `request.state.tier` and checks `is_active()` + non-zero credits only; never tier entitlement.
7. `packages/license-sdk/src/core/verifier.ts` — real crypto present (HMAC-SHA256, `timingSafeEqual`, expiry), but line 21 `process.env['OPENCLAW_LICENSE_SECRET'] ?? DEV_SECRET` where `DEV_SECRET = 'openclaw-dev-secret-do-not-use-in-production'` (line 14). Must fail closed.
8. `src/core/tier_fallback_chain.py` is a MODEL-routing concern (which LLM backs each tier), NOT a billing pricing tier table. Do not treat it as a pricing namespace.
9. No Python module under `src/` imports `license-sdk` (`grep -rn "license-sdk" src/` → empty). The TS SDK and the Python gate are disconnected.
10. Polar.sh surface (live, tracked): `src/middleware/csrf_middleware.py`, `src/core/task_classifier.py`, `src/core/vendor_engine.py`, `src/core/binh_phap/reactions.py`, `src/core/binh_phap/standards.py`, `src/cli/_app_setup/groups_19.py`, `src/cli/commands/revenue_command.py`, `src/polymarket/billing.py`, `src/api/billing_routes_models.py`, `src/api/raas_billing_middleware_helpers.py`, `src/harness/agents/classifier.py`, `src/api/vn_pricing_routes.py`, `src/api/webhooks/router.py`, `src/api/billing_routes_webhooks.py`, `src/api/billing_routes.py`, plus services/polar_client.py. `src/raas/checkout_router.py` rewrite is UNCOMMITTED (working tree).
11. FALSE POSITIVES (IMO Polar Code / polar wash — do not delete): `src/core/maritime/phase_339_polar_code_polaris_rio.py`, `src/core/maritime_polar_wash_ev_salvage_engine.py`, `maritime_polar_wash_ev_salvage_command.py`.
12. Dirty tree: 11 modified + 14 untracked, all in `src/cli/commands/*_commands_records_table.py` + `compliance_table_renderers.py` + 12 command modules + DEPLOYMENT_SUMMARY.md + ORIGINAL_REQUEST.md.
13. `.mekong/company.json`: `open_core_25_steps_aligned: true`, `binh_phap_state.revenue_events: []`. Do not edit.

## Binh Phap chapter table (from src/core/binh_phap/topology.py, dumped at runtime)
| Ch | Commercial (Fable 5) | Dispatch commands |
|---|---|---|
| 1 始計 Lược Kế | yes | swot, annual, founder:validate, okr, venture:five-factors |
| 2 作戰 Tác Chiến | yes | finance, budget, pricing, finance:monthly-close |
| 3 謀攻 Mưu Công | no | plan, brainstorm, scope, product:discovery, ask |
| 4 軍形 Quân Hình | no | cook, code, test, review, fix |
| 5 兵勢 Binh Thế | yes | marketing, sales, growth:experiment, content, launch |
| 6 虛實 Hư Thực | no | research, competitive, venture:void-substance, scout |
| 7 軍爭 Quân Tranh | no | deploy, fix, release:hotfix, release:ship |
| 8 九變 Cửu Biến | no | debug, sre:incident, devops:rollback, ops:health-sweep |
| 9 行軍 Hành Quân | no | sprint, standup, milestone, backlog |
| 10 地形 Địa Hình | no | market, venture:terrain, positioning, tam |
| 11 九地 Cửu Địa | yes | fundraise, founder:negotiate, founder:validate, pivot |
| 12 火攻 Hỏa Công | yes | campaign, outreach, launch, growth:channel-optimize |
| 13 用間 Dụng Gián | no | audit, scout, health, status, security |

NOTE a repo-internal contradiction: `topology.py` binds Ch4 to `cook/code/test/review/fix` and Ch7 to `deploy/release`, while `src/core/binh_phap/standards.py` binds Building=第七篇 軍爭 (Ch7) and Discovery=Ch1 / Planning=Ch3 / Polish=Ch5 / Handoff=Ch12. So the build verb is Ch4 in topology but Ch7 in standards. The mapping in this plan must declare which surface it follows.

## Dispatch authority (Verified — resolves the chapter contradiction above)
`src/core/binh_phap/topology.py:139` `_command_to_chapter(cmd) -> next((ch for ch, cmds in CHAPTER_COMMANDS.items() if cmd in cmds), 0)` is the ONLY functional chapter resolver. Consequences:
- **`CHAPTER_COMMANDS` in topology.py is the authoritative chapter table.** `CTO_FRAMEWORK_PHASES` in `standards.py` is cosmetic — grep for `["chapter"]` / `.get("chapter")` finds NO reader of that dict, so "Building = 第七篇 軍爭" is a documentation string with zero effect on dispatch.
- **Unmapped command → chapter 0**, and chapter 0 is NOT in `COMMERCIAL_CHAPTERS`, so an unmapped command silently routes to Opus with `needs_approval=False`. Any new command must be added to `CHAPTER_COMMANDS` or it becomes invisible to the commercial/Fable route and to approval gating.
- `dispatch_next()` (topology.py:142-168) escalates any command whose chapter is in `COMMERCIAL_CHAPTERS = {1,2,5,11,12}` to `LLM_ROUTING[STRATEGIC]` (cloud_opus) and forces `needs_approval=True`. So **chapter choice is not cosmetic — it decides LLM cost and human gating.**
- `src/core/binh_phap/executor.py` keeps per-chapter `ExecutionResult` with `fallback_chapters`; on action=="fallback" it re-runs fallback chapters and records the first success. A step mapped to a chapter with no registered DAG entry fails with chapter-0 semantics.
- `src/core/binh_phap_dispatcher.py:63,72,156` propagates `chapter` into every action/result dict, so chapter numbering is an observable public contract of the dispatcher output.

**Implication for this plan:** the 25-step mapping must be expressed as `step slug → command already present in CHAPTER_COMMANDS` (or an explicit new command + topology entry), NOT as an abstract chapter number. A mapping that names a chapter without a command in that chapter's list cannot be dispatched.

## Tier namespace — exact runtime truth (Verified 2026-10-21 ~22:10)
`TierKey` (`src/seed/config/tiers_models.py`) has exactly SIX members: `free`, `trial`, `starter`, `growth`, `pro`, `enterprise`. There is **no `MASTER` member**.

`aliases()` collapse map (input → canonical target), dumped at runtime:
- `free` ← `free`, `FREE`
- `trial` ← `trial`, `trial_vn`, `TRIAL`
- `starter` ← `starter`, `starter_vn`, `basic`, `BASIC`, `STARTER`
- `growth` ← `growth`, `growth_vn`, `PREMIUM`, `premium`, `GROWTH`, `team`, `TEAM`
- `pro` ← `pro`, `pro_vn`, **`enterprise`, `ENTERPRISE`, `PRO`, `MASTER`, `master`**
- `enterprise` ← `enterprise_plus`

Two traps, both verified live:
1. **`TierKey('ENTERPRISE')` → the `enterprise` member**, but the **alias** `aliases()['ENTERPRISE']` → `'pro'`. A test written as `TierKey('MASTER') is not TierKey('pro')` passes/fails on the wrong axis. Any correct acceptance command must go through `aliases()`.
2. `TierKey('MASTER') is TierKey('pro')` is True **only because `MASTER` is looked up by name and fails to `pro`'s value via the alias table**, not because a MASTER member exists. So the four-tier naming the brief asserts (BASIC/PREMIUM/ENTERPRISE/MASTER) exists nowhere in this enum — BASIC→starter, PREMIUM→growth, and both MASTER and ENTERPRISE fold toward pro, while `enterprise` (the member) is reachable only via `enterprise_plus`.

This corrects the 20:14 enforcement plan, which stated the MASTER bug as `aliases()` folding `MASTER→pro` AND `ENTERPRISE→pro`. The MAP→pro direction is right; the ENTERPRISE→pro claim conflates the alias input with the enum member.

## PHASE 0 — implemented and verified (2026-10-21 ~15:40 UTC)

### Change
- **New** `src/core/opencore/monetization_gate_probes.py` (104 LOC) — computes `jwt_license_gate_enforced` and `mcu_http402_billing_wired` from repository evidence, plus `expected_verdict()`. No DB, no network, no production state touched; all checks read source text.
- **Changed** `src/core/opencore/phase_560_opencore_saas_readiness_engine.py:135` — `audit_repository` now takes `jwt_license_gate_enforced: bool | None = None` and `mcu_http402_billing_wired: bool | None = None`. When both are `None` it runs the probes; an explicit `False`/`True` still overrides (needed by the synthetic telemetry tests).
- **Changed** `src/cli/commands/opencore_saas_restructuring_command.py:53` — `--jwt-gate` / `--mcu-billing` default to `None` (optional override) instead of `True`, so the CLI also probes by default.
- **Changed** both test files — every `== "PUBLIC_GITHUB_SAAS_READY"` literal now asserts the computed `expected_verdict()`, so a test goes red exactly when enforcement regresses.

### What the probes find today (live)
- `jwt_license_gate_enforced = False` — two reasons:
  1. `src/api/gateway_mission_routes.py` calls `license_gate` **conditionally**, gated on `LICENSE_GATE_ENFORCE` — so the gate can be switched off at runtime.
  2. `src/core/entitlement_enforcer.py` enforces usage counts only and never references `TierKey` — **no tier entitlement is checked at all**.
- `mcu_http402_billing_wired = True` — all five expected emitters carry a literal `402`.

### Result
```
audit_repository('.')  ->  MONETIZATION_GATE_INCOMPLETE
safe_for_public_github_push = True        (public push still safe)
saas_paywall_active = False               (paywall NOT proven — truth)
```
Verified live via both the engine and `opencore_saas audit --verify-fs`.

### Gates
| Check | Result |
|---|---|
| `pytest tests/core/ + both opencore suites` | **1372 passed, 0 failed** |
| `test_loc_invariants_for_deep_brainstorm_modules` | passed (test file 164 ≤ 165) |
| `ruff check` on all 5 touched files | All checks passed |
| Untouched files | none |

### Pre-existing, unrelated to this change
`tests/core/` contains a `PermissionError: [Errno 1] Operation not permitted: '/Users/macbook/.mekong/telemetry-buffer.json'`. Cause: the sandbox cannot write `~/.mekong/`. Reproduced identically before this change; re-run with `HOME=$TMPDIR/...` passes 1372/1372.
