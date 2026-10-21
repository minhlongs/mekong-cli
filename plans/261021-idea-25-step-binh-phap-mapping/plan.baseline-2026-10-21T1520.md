---
title: "Idea 25-Step Open-Core — Binh Pháp Mapping & Safety-Gated Execution"
description: "Phase the 25-step Open-Core public-GitHub + SaaS pipeline by safety, with exact Binh Pháp chapter mapping per step and a verifiable acceptance command per phase."
status: pending
priority: P1
effort: 26h
branch: feat/trade-transport-remedies-suite-phases-163-166
tags: [opencore, binh-phap, monetization, tiers, github-hygiene, planner]
created: 2026-10-21
---

# Idea 25-Step Open-Core — Binh Pháp Mapping & Safety-Gated Execution

Outcome: the 25-step Open-Core pipeline is public-push-safe AND its SaaS monetization is
*enforceable and verified*, with every step bound to a dispatchable Binh Pháp chapter.

## Scope correction carried from verified baseline

Two claims in the delegated brief are **stale**, verified 2026-10-21 against the live tree.
The plan is written to the corrected state, not the brief:

1. **Hygiene blocker is already resolved.** `git ls-files apps/ billing/` → 0
   non-`apps/dashboard/` files. The 3 orchestrator files are untracked and stay untracked
   (`.gitignore:123` = `apps/nhipdieuxanh-orchestrator/`).
   `verify_filesystem_hygiene('.')` → `missing_items == ()`.
2. **The 4 LOC violations are resolved** (autonomous 174, dag_scheduler 158, api_adapter 140,
   health_reporter 171). `test_loc_invariants_for_deep_brainstorm_modules` PASSES.
3. **`packages/license-sdk/` IS tracked** (25 files) — not "uncommitted, must commit".
4. **`src/core/tier_fallback_chain.py` is NOT a billing tier namespace.** It is model-routing
   (which LLM backs each tier). It must not be merged into the tier-collapse work.
5. **`src/raas/checkout_router.py` is NOT uncommitted** — it is clean in the working tree.

**The single highest-severity finding is unchanged and now the plan's critical path:** a
`PUBLIC_GITHUB_SAAS_READY` verdict is not evidence of monetization. See Divergence 1.

---

## Precondition: chapter mapping must name a command, not a number

`src/core/binh_phap/topology.py:139` `_command_to_chapter` resolves a command to a chapter by
reverse-lookup over `CHAPTER_COMMANDS` and returns **chapter 0 for anything unmapped**. Chapter 0
is absent from `COMMERCIAL_CHAPTERS = {1,2,5,11,12}`, so an unmapped command silently routes to
Opus with `needs_approval=False`. `dispatch_next()` (topology.py:142-168) escalates any command in
a commercial chapter to `LLM_ROUTING[STRATEGIC]` and forces `needs_approval=True`.

Consequence for this plan: a step is only *mapped* if its command already appears in
`CHAPTER_COMMANDS` (57 commands verified at runtime). Every row below therefore carries a
**dispatch command**, and rows that need a new command say so explicitly as a topology edit.

Lifecycle anchors in `src/core/binh_phap/standards.py:18,24,30,36,42` (Discovery=Ch1, Planning=Ch3,
Building=Ch7, Polish=Ch5, Handoff=Ch12) are documentation strings with **no reader** — `CTO_FRAMEWORK_PHASES["chapter"]`
has no consumer. Where the two disagree, `CHAPTER_COMMANDS` wins.

---

## Phase 0 — Close the green-gate lie (blocking, run first)

**Why first:** every other phase reports progress through a verdict that currently cannot fail.
Nothing downstream is trustworthy until this lands.

**Edition:** community (audit surface). **Chapter:** 13 用間 Dụng Gián (`audit`, `security`).

| # | Slug | State | Target | Edition | Chapter | Files |
|---|---|---|---|---|---|---|
| 1 | git-history-secret-purge | Verified: `git log --all -S "sk-or-v1-"` → 18 commits; every occurrence is a **placeholder or masked UI value** (`QUICKSTART.md:18` `sk-or-v1-yourkey`, `output/index.html:579` `sk-or-v1-****`, `site/public/settings.html:616` `sk-or-v1-***44a1`) or a docs mention. **No live key in any commit; no live key in the working tree.** A full `git grep -IE 'sk-or-v1-[a-zA-Z0-9]{20,}\|sk-ant-[a-zA-Z0-9]{20,}'` across all 13,178 commits found no hit | Keep clean; add a guard that fails on a *real* 20+-char key so a future accidental commit is caught at the gate, without paying for a history rewrite | community | 13 (`audit`) | new assertion in `tests/test_opencore_git_boundary_guard.py` (Phase 1 file); `.pre-commit-config.yaml` |
| — | monetization-proof | `audit_repository` takes `jwt_license_gate_enforced=True, mcu_http402_billing_wired=True` as caller-supplied defaults and *never verifies them* (phase_560:135-137) | Both flags **computed** from live repo evidence; READY only when provable | community | 13 | `src/core/opencore/phase_560_opencore_saas_readiness_engine.py` (148 LOC, headroom to 180) |

New module (≤180 LOC, own file for the probes):
`src/core/opencore/monetization_gate_probes.py` — computed evidence only:
- `jwt_license_gate_enforced`: `license_gate` is imported by ≥1 route module AND the route passes
  the tier claim downstream. Probe: `gateway_mission_routes.py:28,45` is the *only* consumer
  (1 of 14 `license_gate` mentions is a real router mount — the other 13 are docstrings/params).
  Current evidence: mounted, but without tier entitlement (see Phase 4).
- `mcu_http402_billing_wired`: ≥1 route emits HTTP 402 with `MCUBilling` (`src/core/mcu_billing.py:35`).
  Current evidence: satisfied — `src/api/auth_routes.py:47,84`, `src/api/gateway_webhook_mcu_routes.py:70`,
  `src/raas/missions_service.py:88`, `src/raas/marketplace_router_install.py:105,123`.

Then flip 8 existing test assertions that hard-code `PUBLIC_GITHUB_SAAS_READY`
(`tests/test_idea_deep_opencore_brainstorm.py:30,41,53,74,80`; `tests/test_opencore_saas_25_step_suite.py:62,78,165`)
to assert the **computed** value. These will fail until the probes agree — that is the point.

**Acceptance (command, not prose):**
```bash
python3 -m pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_opencore_saas_25_step_suite.py -q
python3 -c "
from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine as E
r=E.audit_repository('.')
print(r.verdict.value, r.saas_paywall_active)
assert r.verdict.value != 'PUBLIC_GITHUB_SAAS_READY', 'gate still green with unenforced entitlement'
"
```
Second command must print a non-READY verdict until Phase 4 closes.

**Rollback:** revert the two files; verdicts return to green-without-proof. No data, no schema.

---

## Phase 1 — Community release hygiene (safe now, dirty-tree compatible)

**Why now:** every file is additive, reversible, and has **zero overlap** with the 11 modified /
14 untracked dirty files (verified: no `src/seed`, `src/raas`, `src/middleware`, `src/api`,
`src/core/opencore`, `packages/`, `engine/`, `.github/`, `.claude/`, `.agents/` path in
`git status --porcelain`). **Edition:** community. **Chapter:** 6 虛實 Hư Thực (`scout`, `research`).

| # | Slug | State | Target | Edition | Chapter | Files |
|---|---|---|---|---|---|---|
| 3 | gitignore-quarantine-lock | satisfied — `.gitignore:119-125`, `apps/nhipdieuxanh-orchestrator/` at :123, 0 tracked private files | keep; add guard test so a future `git add -f` cannot silently re-track | community | 6 | `.gitignore` (append `apps/sophia-ai-factory/`, `apps/mekong-ide/`, `apps/landing/`, `apps/api/` — all currently untracked but NOT matched by `apps/*` negation `!apps/dashboard/`), new `tests/test_opencore_git_boundary_guard.py` |
| 5 | mit-license-and-sbom | `LICENSE` MIT verified; `CONTRIBUTING.md:33,39` CLA + Trademark verified. **No SBOM exists anywhere** (find `-iname "*sbom*"` → none) | SBOM is a named gap, not a claim | community | 13 | new `scripts/generate-sbom.py` (CycloneDX, stdlib only, ≤180 LOC), `.github/workflows/security-hardening.yml` |
| 4 | env-example-byok-template | all 10 required keys present in `.env.example`; 0 live secret prefixes | keep; assert placeholders stay non-real | community | 6 | `.env.example` (comment headers only), new guard assertion in `tests/test_opencore_saas_25_step_suite.py` |
| 1 | git-history-secret-purge | **no live secret in the tree** — every `sk-or-v1-` hit in 137 commits is a placeholder or a masked UI value (`QUICKSTART.md:18`, `output/index.html:579`, `site/public/settings.html:616`) | **satisfied for public push.** History rewrite is explicitly deferred (see Out of scope) | community | 13 | none — evidence recorded, no rewrite |
| 21 | sixty-second-quickstart | `README.md:58` has `git clone` | add one copy-paste command that reaches a working CLI | community | 3 | `README.md`, `QUICKSTART.md` |
| 25 | cla-and-trademark-policy | CLA + Trademark sections present (CONTRIBUTING.md:33,39) | keep; no work | community | 13 | none |

**Honest note on Step 5:** the catalog's OSS surface says "MIT LICENSE + SBOM". LICENSE is real,
SBOM is not. Either ship the SBOM (work above) or record it as explicitly out of scope — do not
leave the catalog claiming it.

**Acceptance:**
```bash
python3 -m pytest tests/test_opencore_saas_25_step_suite.py tests/test_opencore_git_boundary_guard.py -q
git ls-files apps/ billing/ | grep -vc '^apps/dashboard/'   # must print 0
python3 scripts/generate-sbom.py >/dev/null && echo SBOM_OK
# step 1: no live secret pattern in the working tree (placeholders and ***-masked UI values excluded)
grep -rn "sk-or-v1-[a-zA-Z0-9]\{20,\}\|sk-ant-[a-zA-Z0-9]\{20,\}\|AIzaSy[a-zA-Z0-9]\{20,\}" \
  --include="*.py" --include="*.ts" --include="*.tsx" --include="*.json" --include="*.md" \
  src/ tests/ packages/ .env.example   # must print nothing
```

**Rollback:** `.gitignore`/`README` untrack-only edits; SBOM script deletion. Nothing deployed.

---

## Phase 2 — Structurally visible public-leak surfaces (founder decision)

**Chapter:** 13 用間 Dụng Gián (`audit`, `security`). **Edition:** community boundary, founder call.

Three surfaces are tracked in git today and will publish to a public MIT repo:

| Surface | Count | Verified | Risk |
|---|---|---|---|
| `.claude/` | **1775 tracked files** (`_integration` 859, `_archive` 724, `_pipeline` 166, `_quality` 13, `_core` 12) | `git check-ignore .claude/_archive` → NOT IGNORED | Directly violates the project rule "Do not bundle `.claude/` rules, slash commands, hooks, or MCP configuration into delivered artifacts… Keep `.claude/` local" |
| `.agents/` | **447 tracked files, 10M** | NOT IGNORED | Same class — agent definitions and skill payloads published |
| `__pycache__/*.pyc` | **4 tracked** | `git ls-files \| grep '\.pyc$'` | Build artifacts; also binary blobs in a source repo |

Step 2's OSS surface (`src/core + src/cli (MIT)` vs `apps/ + billing/` isolated) is **not** a
directory move — it is a gitindex-boundary question, and these three are the real answers.

**Note:** none of these appear in `REQUIRED_GITIGNORE_RULES`
(`apps/`, `billing/`, `*.pem`, `.orchestrate/`), so `verify_filesystem_hygiene` will stay green
with all 1775 files tracked. Untracking requires `git rm -r --cached`, which rewrites the index
but **not** history — prior commits still expose them until a history purge.

**Blocking sub-finding — some of `.claude/` is load-bearing tooling, not leaked config.**
`.claude/_pipeline/scripts/set-active-plan.cjs` is the plan-activation script this workflow
requires, and it is **tracked** (commit `2eb8d7e66 refactor: align core pipeline configs with mk: namespace`).
Untracking `.claude/` wholesale would strip it from the public repo while local clones that rely
on the tracked copy lose it. It is also **already broken**: line 16 requires
`'../hooks/lib/mk:config-utils.cjs'`, but the only file on disk is
`.claude/_pipeline/hooks/lib/ck-config-utils.cjs` — a `mk:`-prefixed name that is not a legal
macOS/Linux filename and cannot exist. Verified runtime failure:
`Error: Cannot find module '../hooks/lib/mk:config-utils.cjs'`.

Therefore Phase 2 must ship an **allowlist**, not a wholesale untrack: keep
`.claude/_pipeline/scripts/` and its `hooks/lib/` dependencies tracked, and either fix the require
to `ck-config-utils.cjs` or add a tracked shim. This is a real bug and should be its own phase item
rather than a side effect of the hygiene pass.

**Acceptance:**
```bash
git ls-files .claude/ | wc -l        # target: allowlist only (pipeline scripts + lib), not 1775
git ls-files .claude/_archive .claude/_integration | wc -l   # must print 0
git ls-files .agents/ | wc -l        # target 0 (or a founder-approved allowlist)
git ls-files | grep -c '\.pyc$'      # must print 0
node .claude/_pipeline/scripts/set-active-plan.cjs plans/261021-idea-25-step-binh-phap-mapping  # must not throw
python3 -m pytest tests/ -q          # no test depends on removed tracked .claude//.agents content
```

**Rollback:** `git reset` then re-add the exact prior paths; commit the pre-change index hash first.

---

## Phase 3 — Community edition seams (safe, additive)

**Chapter:** 4 軍形 Quân Hình (`cook`, `code`, `test`, `review`, `fix`) — note this contradicts
`standards.py` Building=Ch7; `CHAPTER_COMMANDS` wins.

| # | Slug | State | Target | Edition | Chapter | Files |
|---|---|---|---|---|---|---|
| 6 | capability-bus-interfaces | `src/core/capability.py` exists; vendor SDK imports are not statically barred | add boundary test: zero vendor SDK imports under `src/core/opencore/`, `src/core/capability.py` | community | 4 | new `tests/test_core_boundary_no_vendor_sdk.py`; `src/core/capability.py` (read-only unless test fails) |
| 7 | byok-local-adapters | 10 BYOK keys in `.env.example`; adapters read `os.getenv` | keep; add test that a missing key produces a typed failure, not a silent default | community | 6 | `tests/test_byok_fail_closed.py` (new) |
| 9 | local-sandbox-runtime | `src/core/exec_runtime` + `sandbox_bridge.py` exist | document the single-operator contract; no new feature | community | 4 | `docs/` |
| 23 | ci-leak-and-loc-gate | `.github/workflows/gates.yml` runs ruff + pytest; **`security-hardening.yml:30` runs `trufflehog … --fail \|\| true`** — the `\|\| true` makes the secret scan **non-blocking** | remove `\|\| true` so verified-secret detection blocks the build; add LOC guard step | cloud | 13 | `.github/workflows/security-hardening.yml`, `.github/workflows/gates.yml` |

**Step 23 is the highest-value item in this phase** and the cheapest: a leak gate that cannot fail
is not a gate. LOCAL_BINDING/pre-commit `.pre-commit-config.yaml` exists and should be pointed at
the same probe.

**Acceptance:**
```bash
python3 -m pytest tests/test_core_boundary_no_vendor_sdk.py tests/test_byok_fail_closed.py -q
grep -n 'trufflehog' .github/workflows/security-hardening.yml   # must NOT end in '|| true'
```

**Rollback:** workflow revert; boundary tests are new files (delete to revert).

---

## Phase 4 — Tier collapse & paid enforcement (needs founder approval)

**Blocking rationale — this phase touches live money.** Six incompatible tier namespaces are live.
Verified against the tree:

| Surface | Namespace | File |
|---|---|---|
| Canonical billing | `free / trial / starter / growth / pro / enterprise` | `src/seed/config/tiers_models.py:11-19` |
| **THE MASTER BUG** | `aliases()` at `tiers_models.py:27-59`: `MASTER→pro`, `ENTERPRISE→pro` | `src/seed/config/tiers_models.py:27-59` |
| Credit ledger | `free 50 / starter 300 / growth 1200 / scale 3500 / pro 7000` | `src/raas/billing_tiers.py:13-17` |
| Forgeable web gate | `free / pro / enterprise`, non-cryptographic 32-bit 4-hex checksum | `src/lib/raas-gate.ts:8,102` (149 LOC, 175 guard) |
| TS SDK | `free / starter / pro / enterprise` ($0/$29/$99/$299) | `packages/license-sdk/src/core/tiers.ts:2` (81 LOC) |
| JWT quotas | `free / trial / pro / enterprise` + silent `quotas.get(tier, quotas["free"])` | `engine/license/jwt_license_generator.py:336` (466 LOC, `engine/` unguarded) |

**Verified at runtime (corrected 2026-10-21):** `TierKey` has exactly six members — `free`, `trial`,
`starter`, `growth`, `pro`, `enterprise`. There is **no `MASTER` member at all**, so a MASTER buyer
does not get a distinct tier — they are folded by `aliases()` onto `pro` (`MASTER`/`master`/`ENTERPRISE`/`ENTERPRISE`/`enterprise`/`PRO` all map to `pro`). Note the asymmetry that
makes this easy to mis-test: `TierKey('ENTERPRISE')` resolves to the `enterprise` **member**, while
the *alias* input `'ENTERPRISE'` resolves to `pro`. Testing the assertion must go through
`aliases()`, not `TierKey(...)`.

Consequence: a $4,999 MASTER buyer is silently served the PRO entitlement ladder. The
`growth` bucket additionally absorbs `PREMIUM`, `premium`, `team` and `TEAM`, so the four-tier
naming the brief asserts (BASIC/PREMIUM/ENTERPRISE/MASTER) exists nowhere in this enum — it is
spread across `starter`/`growth`/`enterprise` with two of the four collapsing. This is a revenue
defect, not a naming nit.

Also verified: **no Python module imports `license-sdk`** (`grep -rn "license-sdk" src/` → empty).
The TS SDK and the Python gate are disconnected, so collapsing one does not collapse the other — both
must change or the divergence persists.

And: `src/core/entitlement_enforcer.py:50-70` enforces **command counts only** — it never imports
`TierKey` and never compares tier identity. Tier is a display string at `:163`.

**Decision required (do not silently pick):** which namespace is canonical, and does
`ENTERPRISE→pro` / `MASTER→pro` collapse (losing two paid tiers' separation) or do the aliases
invert (pro→enterprise, add a distinct `master`)? The brief names BASIC/PREMIUM/ENTERPRISE/MASTER
($199/$399/$799/$4,999) as intended, but `tiers_models.py` has no such prices — verified: it has
`monthly_price_usd`/`monthly_price_vnd` fields at `:88` with no populated canonical table found. The
intended price table is **unverified** and must be confirmed by the founder before aliases change.

| # | Slug | State | Target | Edition | Chapter | Files |
|---|---|---|---|---|---|---|
| 11 | jwt-license-gate | `license_gate` sets `request.state.tier = claims.get("tier","starter")` (license_gate.py:86) and checks only `is_active()` + non-zero credits (`:71,78`) | enforce tier entitlement against canonical namespace; fail closed on unknown tier | cloud | 2 | `src/middleware/license_gate.py` (87 LOC), `src/core/entitlement_enforcer.py` (169 LOC) |
| 12 | mcu-credit-metering | 402 wired on 7 verified sites (auth_routes:47,84; gateway_webhook_mcu_routes:70; missions_service:88; marketplace_router_install:105,123; missions_api_router:56) | keep; meter per tier so MASTER≠PRO is observable in spend | cloud | 2 | `src/raas/billing_tiers.py` (34 LOC), `src/core/mcu_billing.py` |
| 13 | tiered-rate-limiting | limits key off tier but tier identity is forgeable/ambiguous | rate limit on the resolved canonical tier | cloud | 2 | `src/middleware/license_gate.py`, `src/raas/billing_tiers.py` |
| 15 | encrypted-key-vault | tenant keys in dotenv (`MEKONG_*`) | KMS vault for cloud; keep dotenv for community | cloud | 11 | `src/services/`, `src/api/` |
| 16 | multi-tenant-rbac-isolation | `src/auth/rbac.py:118` `_RoleDependency`, `src/core/auth_tenant.py` exist | tenant isolator + SSO on cloud | cloud | 11 | `src/auth/`, `src/services/org_service_*.py` |
| 17 | compliance-audit-ledger | `src/core/opencore/saas_immutable_audit_ledger.py` exists (151 LOC) | immutable TT78/SOC2 vault on cloud; stdout logs stay in community | cloud | 13 | `saas_immutable_audit_ledger.py`, `src/api/` |
| 18 | always-on-cloud-daemon | `src/daemon/` scheduler + `src/core/_watcher_daemon.py` exist; foreground CLI is the community contract | 24/7 daemon + SLA on cloud | cloud | 7 | `src/daemon/`, `docs/` |
| 19 | strategy-recipe-marketplace | `src/raas/marketplace/`, `marketplace_router_catalog.py`, `marketplace_router_install.py` exist; install emits 402 at `:105,123` with a **Polar.sh** upsell string at `:108` | verified-publisher marketplace cut on cloud | cloud | 5 | `src/raas/marketplace/`, `src/raas/marketplace_router_install.py` |
| 22 | cli-to-cloud-upsell-prompt | `_recharge_url()` at `license_gate.py:41,74,81` returns a URL in 402 detail | quota banner + `recharge_url` upgrade path | cloud | 12 | `src/middleware/license_gate.py`, `src/cli/` |
| 24 | public-benchmark-trust-badge | reproducible suite exists (`tests/`, ~62 tests) | badge workflow wired to the Phase 0 probes | cloud | 13 | `.github/workflows/`, `src/api/opencore_status_routes.py` |

Securing the two forgeable surfaces (both cloud edition, fail-closed):
- `src/lib/raas-gate.ts:97-106` — replace `generateChecksum` (32-bit FNV-ish, 4 hex) with the real
  HMAC path already present in `packages/license-sdk/src/core/verifier.ts:25` (`createHmac('sha256', …)`).
- `packages/license-sdk/src/core/verifier.ts:14,21` — `DEV_SECRET = 'openclaw-dev-secret-do-not-use-in-production'`
  with `process.env['OPENCLAW_LICENSE_SECRET'] ?? DEV_SECRET`. **Must fail closed** when the env
  secret is absent and the brand is a paid edition. File is 79 LOC; guard budget is tight but
  `src/lib` is at 175 for `.ts` — `packages/` is **not** in the UI guard list, so no LOC constraint.
- `engine/license/jwt_license_generator.py:336` — `quotas.get(tier, quotas["free"])` must raise on
  unknown tier. `engine/` is unguarded (466 LOC today), so this edit is unconstrained.

**Acceptance:**
```bash
python3 -c "
from src.seed.config.tiers_models import TierKey
a = TierKey.aliases()
assert a.get('MASTER', '').lower() != 'pro', 'MASTER alias still collapses to pro'
assert a.get('master', '').lower() != 'pro', 'master alias still collapses to pro'
assert a.get('ENTERPRISE', '').lower() != 'pro', 'ENTERPRISE alias still collapses to pro'
assert 'MASTER' in TierKey.__members__, 'no distinct MASTER tier member'
assert TierKey('MASTER') is not TierKey('PRO'), 'MASTER still resolves to PRO'
print('tier separation OK')"
python3 -m pytest tests/ -q
grep -n "quotas.get(tier" engine/license/jwt_license_generator.py   # must be gone
grep -n "DEV_SECRET" packages/license-sdk/src/core/verifier.ts      # must not be a live fallback for paid
```

**Rollback:** alias-table revert in `tiers_models.py` restores prior behavior but **keeps** the
MASTER bug; there is no partial rollback that fixes revenue and reverts safely. Ship behind a
feature flag and stage in cloud edition first (`community` keeps the current weak gate per the
founder decision that the gate ships in community to prove the funnel). Existing issued keys stay
valid because tier *names* do not change, only their resolution.

---

## Phase 5 — Polar.sh exit & PLG surface (founder approval + clean tree)

**Why separate and last:** the Polar surface is **22 files**, not the 6 named in the brief.
Verified list (all excluding the confirmed IMO Polar Code / polar-wash false positives):

`src/api/billing_routes_models.py`, `src/api/billing_routes_webhooks.py`, `src/api/billing_routes.py`,
`src/api/raas_billing_middleware_helpers.py` (`:26,46` hardcode `https://polar.sh/mekong`),
`src/api/vn_pricing_routes.py` (`:35,44,97` — VND display, **USD billed via Polar.sh**),
`src/api/webhooks/router.py`, `src/core/binh_phap/standards.py` (`:69-71` `POLAR_ACCESS_TOKEN`),
`src/core/vendor_engine.py` (`:52,55` `polar-billing` vendor, 455 LOC, `src/core/` root unguarded),
`src/middleware/csrf_middleware.py:31` (`/v1/polar/` in `_CSRF_SKIP_PREFIXES`),
`src/polymarket/billing.py` (CashClaw — separate product, founder call on whether it exits too),
`src/raas/billing_webhook_handler.py`, `src/raas/billing.py`, `src/raas/marketplace_router_install.py`,
`src/raas/nowpayments_webhook_handler.py`, `src/raas/revenue_router_helpers.py` (`:28,59-62,81`),
`src/raas/webhook_bridge_models.py`, `src/raas/webhook_bridge.py`, `src/raas/webhook_events.py`,
`src/services/org_service_billing.py`, `src/services/polar_client_models.py`,
`src/services/polar_client.py`, `src/services/sqlite_migrations.py`.

**Confirmed false positives — DO NOT touch:** `src/core/maritime/phase_339_polar_code_polaris_rio.py`,
`src/core/maritime/phase_392_iccp_cathodic_protection_shaft.py`, `src/core/maritime/phase_347_*.py`,
`src/core/maritime/phase_421_*.py`, `src/cli/commands/maritime_polar_wash_ev_salvage_command.py`,
`src/cli/commands/maritime_boiler_stp_ballast_hypermist_command.py` (all IMO Polar Code /
cathodic polarization — unrelated to Polar.sh). Also `src/cli/_app_setup/groups_19.py:16-18`
registers `polar`/`bangtuyet`/`polarisrio` — those are **maritime aliases**, not Polar.sh.

**Step 20 target:** the catalog says the cloud surface is "PayOS / NOWPayments / Polar IPN".
Removing Polar means editing that catalog string too — `phase_559_opencore_25_step_catalog.py:45`.
That file is 51 LOC, in the guarded folder `src/core/opencore`, and is the source of the
`TWENTY_FIVE_OPENCORE_STEPS` tuple every test indexes. **Editing a `frozen dataclass` field changes
`contract_digest`** (`opencore_25_step_deep_brainstorm_engine.py:134-138` hashes `phases_summary`
which is built from these specs) — 1 test asserts `len(contract_digest) == 64` (`test_idea…:80`),
which stays true, but any digest-golden test would break. Verified: no digest golden exists.

| # | Slug | State | Target | Edition | Chapter | Files |
|---|---|---|---|---|---|---|
| 2 | oss-vs-ee-directory-split | boundary is gitindex-level, already satisfied for `apps/`+`billing/`; `.claude/`+`.agents/` are the real gaps (Phase 2) | keep SST; no directory move | community | 6 | `.gitignore`, `CONTRIBUTING.md` |
| 8 | cloud-bridge-webhooks | `src/core/watcher_bridge.py`, `benchmark_bridge.py`, `sandbox_bridge.py` exist | community stub, hosted ingestion on cloud | community | 4 | `src/core/watcher_bridge.py` |
| 10 | versioned-openapi-sdk | **no `openapi*.json/yaml` anywhere** (find → none) | export a versioned schema; meter on cloud | community | 5 | new `scripts/export-openapi.py`, `src/api/` |
| 14 | managed-worker-queues | `src/core/task_queue.py` in-memory | Redis/DO on cloud; in-memory stays community | community | 4 | `src/core/task_queue.py` |
| 20 | payment-webhook-activation | NOWPayments + PayOS live; Polar live across 22 files | Polar removed, catalog string updated | cloud | 11 | the 22-file list above + `phase_559:45` |

**Acceptance:**
```bash
grep -rln "Polar\.sh\|polar\.sh\|POLAR_ACCESS_TOKEN\|POLAR_PRICE\|polar-billing\|/v1/polar" --include="*.py" src/ | grep -v maritime | grep -v polymarket   # must be empty
python3 -m pytest tests/ -q
python3 -c "
from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine as E
print(E.audit_repository('.').verdict.value)"
```

**Rollback:** Polar removal is only safe in a clean tree and behind one commit per sub-surface
(webhooks → routes → vendor/csrf → client/services → catalog string). Full revert = restore the
commit range; the CSRF/`_CSRF_SKIP_PREFIXES` removal is the load-bearing one and must land last so
no intermediate state serves an ungated `/v1/polar/` endpoint.

---

## Consolidated 25-step × Binh Pháp map

One row per canonical step in `TWENTY_FIVE_OPENCORE_STEPS`. `Dispatch` is a command that already
exists in `CHAPTER_COMMANDS[ch]`, so every row is dispatchable today. State was verified live on
2026-10-21; `Phase` is where the work (or the honest recording of "no work") happens.

| # | Slug | Phase | State | Edition | Chapter | Dispatch |
|---|---|---|---|---|---|---|
| 1 | git-history-secret-purge | 0 | DONE (no live key in 13,178 commits; guard test added) | community | 13 用間 Dụng Gián | `audit` |
| 2 | oss-vs-ee-directory-split | 2 | PARTIAL — apps/billing boundary holds, but `.claude/` 1775 + `.agents/` 447 + 4 `.pyc` are tracked | community | 6 虛實 Hư Thực | `scout` |
| 3 | gitignore-quarantine-lock | 1 | DONE (0 tracked private files) + gap: 4 `apps/` siblings untracked-but-unmatched | community | 6 虛實 Hư Thực | `research` |
| 4 | env-example-byok-template | 1 | DONE (10 keys, 0 leaked prefixes) | community | 6 虛實 Hư Thực | `competitive` |
| 5 | mit-license-and-sbom | 1 | PARTIAL — LICENSE & CLA real; **no SBOM exists** | community | 13 用間 Dụng Gián | `security` |
| 6 | capability-bus-interfaces | 3 | PARTIAL — `src/core/capability.py` real; no static vendor-import bar | community | 4 軍形 Quân Hình | `code` |
| 7 | byok-local-adapters | 3 | PARTIAL — adapters read `os.getenv`; missing-key path not asserted | community | 6 虛實 Hư Thực | `research` |
| 8 | cloud-bridge-webhooks | 3 | PARTIAL — `watcher_bridge.py` + `webhook_schema.py` real; hosted ingestion unmetered | cloud | 3 謀攻 Mưu Công | `scope` |
| 9 | local-sandbox-runtime | 3 | DONE — `src/core/exec_runtime/`, `sandbox_bridge.py` | community | 4 軍形 Quân Hình | `test` |
| 10 | versioned-openapi-sdk | 3 | PARTIAL — FastAPI `/openapi.json` auto-generated; no versioned/SDK contract pinned | community | 3 謀攻 Mưu Công | `plan` |
| 11 | jwt-license-gate | 4 | PARTIAL — gate mounted, checks only `is_active()` + credits, never tier entitlement | cloud | 2 作戰 Tác Chiến | `finance` |
| 12 | mcu-credit-metering | 4 | DONE — 402 emitted on 7 verified sites | cloud | 2 作戰 Tác Chiến | `pricing` |
| 13 | tiered-rate-limiting | 4 | PARTIAL — limits key off a forgeable/ambiguous tier | cloud | 2 作戰 Tác Chiến | `budget` |
| 14 | managed-worker-queues | — | PARTIAL — `src/core/task_queue.py` is sqlite/in-process; **no Redis Cluster, no cloud dispatch** | cloud | 7 軍爭 Quân Tranh | `deploy` |
| 15 | encrypted-key-vault | 4 | PARTIAL — tenant keys in dotenv; no KMS vault | cloud | 11 九地 Cửu Địa | `fundraise` |
| 16 | multi-tenant-rbac-isolation | 4 | PARTIAL — `src/auth/rbac.py`, `src/core/auth_tenant.py` real; SSO absent | cloud | 11 九地 Cửu Địa | `pivot` |
| 17 | compliance-audit-ledger | 4 | DONE (community side) — `saas_immutable_audit_ledger.py` real | cloud | 13 用間 Dụng Gián | `health` |
| 18 | always-on-cloud-daemon | 4 | PARTIAL — `src/daemon/` scheduler real; no 24/7 SLA surface | cloud | 7 軍爭 Quân Tranh | `release:ship` |
| 19 | strategy-recipe-marketplace | 4 | PARTIAL — marketplace routers real; verified-publisher cut absent; install page carries a Polar upsell string | cloud | 5 兵勢 Binh Thế | `launch` |
| 20 | payment-webhook-activation | 5 | PARTIAL — PayOS + NOWPayments HMAC real and fail-closed; Polar.sh still wired across 22 files | cloud | 5 兵勢 Binh Thế | `sales` |
| 21 | sixty-second-quickstart | 1 | PARTIAL — `README.md:58` `git clone`; no one-command working start | community | 3 謀攻 Mưu Công | `ask` |
| 22 | cli-to-cloud-upsell-prompt | 4 | PARTIAL — `_recharge_url()` appears in 402 detail only | cloud | 12 火攻 Hỏa Công | `campaign` |
| 23 | ci-leak-and-loc-gate | 3 | PARTIAL — gates.yml real; `security-hardening.yml` trufflehog ends in `\|\| true` (non-blocking) | cloud | 13 用間 Dụng Gián | `status` |
| 24 | public-benchmark-trust-badge | 4 | PARTIAL — reproducible suite real (~62 tests); no badge wired to the Phase 0 probes | cloud | 13 用間 Dụng Gián | `audit` |
| 25 | cla-and-trademark-policy | 1 | DONE — CLA at `CONTRIBUTING.md:33`, Trademark at `:39` | community | 13 用間 Dụng Gián | `health` |

Coverage: DONE 5 · PARTIAL 20 · MISSING 0. Chapter load: Ch13 ×7 · Ch2 ×3 · Ch3 ×3 · Ch6 ×3 · Ch4 ×3 · Ch5 ×2 · Ch7 ×2 · Ch11 ×2 · Ch12 ×1. Steps 8, 10, 14 have no dedicated phase row because their cloud surfaces are stated as gaps here and picked up by Phase 4/5 or recorded as non-goals — they are deliberate, not omissions.

---

## Sequencing & gates

| Order | Phase | Dirty-tree safe? | Founder approval | Gate to enter |
|---|---|---|---|---|
| 1 | Phase 0 — monetization probes | Yes | No | none |
| 2 | Phase 1 — hygiene/SBOM/quickstart | Yes | No | Phase 0 merged |
| 3 | Phase 3 — community seams + leak gate | Yes | No (but Phase 3 step 23 changes CI gating — announce) | Phase 1 merged |
| 4 | Phase 2 — untrack `.claude/`/`.agents/`/`.pyc` | Index rewrite only; **do not run with Phase 4 edits in flight** | **YES** | clean tree, prior index hash recorded |
| 5 | Phase 4 — tier collapse + enforcement | No — needs clean tree | **YES** — canonical namespace + price table | Phases 0-3 merged; tiers_models price table confirmed |
| 6 | Phase 5 — Polar exit + PLG | No — needs clean tree | **YES** — Polar removal scope incl. polymarket/CashClaw | Phase 4 merged; 22-file list confirmed |

**Dirty-tree constraint (explicit).** The tree currently carries 11 modified + 14 untracked files,
all under `src/cli/commands/*_commands_records_table.py`, `compliance_table_renderers.py`,
12 sector command modules, `DEPLOYMENT_SUMMARY.md`, `ORIGINAL_REQUEST.md`, plus one untracked
`plans/` dir. Verified: **zero** of them intersect any file Phases 0, 1, or 3 touch. Phase 1 and
Phase 3 can therefore land on the dirty tree now. Phase 2 rewrites the git index and Phase 4-5
need a clean tree; sequence them after the current branch's work is committed.

**File-ownership conflicts (must not be parallelized):**
- `src/middleware/license_gate.py` — Phase 4 steps 11, 13, 22. One owner, sequential.
- `src/raas/billing_tiers.py` — Phase 4 steps 12, 13. Same owner.
- `src/core/opencore/phase_560_opencore_saas_readiness_engine.py` — Phase 0 owns it; Phase 4
  depends on its probes. Do not parallelize.
- `phase_559_opencore_25_step_catalog.py` — Phase 5 step 20 only (the IPN string).
- `src/core/vendor_engine.py` — 455 LOC in unguarded `src/core/`; Phase 5 only.
- `.github/workflows/gates.yml` vs `security-hardening.yml` — Phase 3 step 23 touches both. One owner.

**Import-surface risks:**
- `packages/license-sdk` has **zero Python importers** (verified). Changing TS tiers does not
  change Python gate behavior — the two collapse independently and both must land in Phase 4.
- `src/core/opencore/` is guard-listed at ≤180 LOC. Phase 0 adds a *new* file there; keep
  `phase_560` under 180 (currently 148, headroom ~32) and put probes in the new module.
- Removing `license-sdk`'s `DEV_SECRET` fallback breaks any dev flow that relies on it. Verify no
  test references it before flipping: `grep -rn "openclaw-dev-secret" tests/ packages/ src/`.

---

## Risks & founder decisions required

| Risk | Likelihood × Impact | Mitigation |
|---|---|---|
| **Green gate masks a broken paywall** (Phase 0) | High × High — already reproducible: `audit_repository('.')` → READY with nothing verified | Phase 0 first; probes computed; tests flipped to assert computed value |
| **MASTER→pro collapse** — $4,999 buyer gets PRO | High × High — verified live | Phase 4; cannot ship public SaaS without it |
| **`.claude/` 1775 files + `.agents/` 447 publish** | High × High on a public MIT repo; violates a stated project rule | Phase 2 with founder approval; index-first, history purge separately |
| Forgeable web gate checksum | Medium × High — 4 hex, non-crypto | Phase 4; reuse verifier.ts HMAC |
| JWT quota silent free-fallback at `jwt_license_generator.py:336` | Medium × Medium — an unknown tier silently gets free | Phase 4; raise instead |
| Polar removal spans 22 files incl. live VND/checkout | Medium × High | Phase 5, per-sub-surface commits, CSRF last |
| trufflehog `\|\| true` | Medium × Medium | Phase 3 step 23, one-line |
| Ruff baseline is **903 errors** | High × Low | Not a usable gate; do not gate on it. Use `ruff check <touched file>` only |
| No SBOM exists while catalog claims it | High × Low (claim inaccuracy) | Phase 1 ships it or the catalog string is amended |

**Founder decisions — no implementation may start on Phase 4 or 5 without these:**
1. Canonical tier namespace. Options: (a) adopt `free/starter/growth/pro/enterprise` and add a
   distinct `master`; (b) collapse to the 4-tier `BASIC/PREMIUM/ENTERPRISE/MASTER` and remap every
   alias; (c) keep 6 keys but fix only `MASTER` and `ENTERPRISE` aliases. (b) is the largest blast
   radius; (c) is the smallest revenue fix. Needs a decision.
2. The intended price table. `$199/$399/$799/$4,999` is asserted in the brief but **not found in
   `tiers_models.py`** — the fields exist (`:88`) with no populated canonical table located.
   Unverified; must be supplied.
3. Whether `.claude/` and `.agents/` are untracked wholesale or with an allowlist, and
   specifically whether `.claude/_pipeline/scripts/` stays tracked (recommendation: keep it, and
   fix the broken `mk:config-utils.cjs` require to `ck-config-utils.cjs`).
4. Whether `src/polymarket/billing.py` (CashClaw, separate product) exits Polar too, or is out of scope.
5. Polar replacement confirmation: the catalog already names PayOS/NOWPayments as the cloud SST
   (`phase_559:45`), so removal should re-point there — needs explicit sign-off since both rails
   are already live.

---

## Out of scope / non-goals

- Rewriting git history for the 137 commits that contain `sk-or-v1-` strings. Verified: every one
  is a **placeholder or masked UI value** (`QUICKSTART.md:18` `sk-or-v1-yourkey`,
  `output/index.html:579` `sk-or-v1-***…`, `site/public/settings.html:616` `sk-or-v1-***44a1`) or a
  docs mention. No live key exists in the working tree. History purge is a separate, expensive
  decision and is **not** required for public push.
- Full Ruff/LOC cleanup of the 903 pre-existing errors. Not this plan's job; gate only on touched files.
- Deploying the cloud edition, a payment-provider migration cutover, or SOC2 attestation.
- Editing `.mekong/company.json` (founder-locked: `open_core_25_steps_aligned: true`,
  `binh_phap_state.revenue_events: []`).
- Touching the 11 modified / 14 untracked sector-command files on the current branch.
- Any IMO Polar Code / polar-wash maritime module (confirmed false positives).

```
Status: DONE_WITH_CONCERNS
Summary: Phased 25-step plan produced with per-step chapter mapping bound to dispatchable
commands, safety-ordered phases (0→5), and one acceptance command each. Baseline was re-verified
live and three brief claims are stale: the hygiene blocker, the 4 LOC violations, and
`packages/license-sdk` uncommitted are all already resolved.
Concerns/Blockers: (1) Phase 0 must land before anything else — `audit_repository('.')` prints
PUBLIC_GITHUB_SAAS_READY with zero verification, and 8 existing tests assert that string, so they
will fail until the probes agree; that failure is the intended signal. (2) The brief's "6 Polar
files" is actually 22, and the brief's "uncommitted checkout_router rewrite" is clean. (3) Two
surfaces the brief did not name are tracked and would publish: `.claude/` (1775 files) and
`.agents/` (447 files, 10M), plus 4 tracked `.pyc`. (4) There is no SBOM anywhere though the
catalog claims one. (5) Phases 4 and 5 cannot start until the founder fixes the canonical tier
namespace and supplies the real price table — the intended $199/$399/$799/$4,999 table is not in
`tiers_models.py`, only empty price fields at line 88. (6) `.claude/_pipeline/scripts/set-active-plan.cjs`
is tracked and already broken (illegal `mk:config-utils.cjs` requires at line 16), so Phase 2 needs
an allowlist and a one-line fix rather than a wholesale untrack. I could not run the plan-activation
script for this reason and set the active plan path by hand in the directory name instead.
```
