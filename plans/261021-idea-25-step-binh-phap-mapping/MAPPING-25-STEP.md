# Re-run 2026-10-22 — /idea 25 bước chính xác có Ánh xạ Binh Pháp (--deep)

Plan-only re-run against the live tree. Read-only; no source file was modified.
Run root: `/Users/macbook/mekong-cli`. Every row below was re-derived from a command
run in this session, not copied from the 2026-10-21 table.

---

## 1. Honest verdict first

| Check | Command | Live result (2026-10-22) |
|---|---|---|
| Readiness verdict | `audit_repository('.')` | **`MONETIZATION_GATE_INCOMPLETE`** — 100.0% completion, `safe_for_public_github_push=True`, `saas_paywall_active=False` |
| Probe pair | `probe()` | `jwt_license_gate_enforced=False`, `mcu_http402_billing_wired=True` |
| Computed expectation | `expected_verdict()` | `MONETIZATION_GATE_INCOMPLETE` (matches — tests now assert this, not a literal) |
| Filesystem hygiene | `verify_filesystem_hygiene('.')` | `is_clean=True`, `missing_items=()`, `apps_tracked=0`, `leaks=0` |
| Blueprint sync | `audit_blueprint('.')` | `matched_steps_count=25`, `three_lenses_present=True`, `company_json_clean=True`, `synchronized=True` |
| Deep engine | `synthesize(..., deep=True)` | `stage=zero`, `digest_len=64`, `total_steps=25` split 5/5/5/5/5 across the 5 catalog phases |
| Tests | `pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_opencore_saas_25_step_suite.py -q` | **12 passed** |

**The two things this run separates, which the old READY verdict conflated:**
1. *Public-push hygiene is green.* Zero leaked secrets in the working tree, zero tracked
   private files, all 10 BYOK keys placeholder-only, MIT + CLA/Trademark present.
2. *Monetization is not proven.* The JWT license gate is mounted but switchable off, and no
   tier entitlement is compared anywhere. A green verdict was never evidence here.

**Phase 0 landed since the last run** (`src/core/opencore/monetization_gate_probes.py`, 103 LOC),
which is why several rows in the 2026-10-21 table are superseded here — chiefly steps 11 and 24.

---

## 2. Dispatch authority — which surface the mapping follows

`src/core/binh_phap/topology.py` is the only functional resolver, and it holds **57 commands**
across 13 chapters. `COMMERCIAL_CHAPTERS = {1, 2, 5, 11, 12}`; anything resolving to chapter 0
is unmapped and silently drops to Opus with `needs_approval=False`.

This run follows **`CHAPTER_COMMANDS`**, not `standards.py`. The lifecycle strings in
`src/core/binh_phap/standards.py` (Discovery=Ch1, Planning=Ch3, Building=Ch7, Polish=Ch5,
Handoff=Ch12) have no reader — `CTO_FRAMEWORK_PHASES["chapter"]` is never consumed. Verified:
every one of the 25 dispatch commands below resolves to a non-zero chapter.

| Ch | Commercial | Commands |
|---|---|---|
| 1 始計 Lược Kế | yes | swot, annual, founder:validate, okr, venture:five-factors |
| 2 作戰 Tác Chiến | yes | finance, budget, pricing, finance:monthly-close |
| 3 謀攻 Mưu Công | — | plan, brainstorm, scope, product:discovery, ask |
| 4 軍形 Quân Hình | — | cook, code, test, review, fix |
| 5 兵勢 Binh Thế | yes | marketing, sales, growth:experiment, content, launch |
| 6 虛實 Hư Thực | — | research, competitive, venture:void-substance, scout |
| 7 軍爭 Quân Tranh | — | deploy, fix, release:hotfix, release:ship |
| 8 九變 Cửu Biến | — | debug, sre:incident, devops:rollback, ops:health-sweep |
| 9 行軍 Hành Quân | — | sprint, standup, milestone, backlog |
| 10 地形 Địa Hình | — | market, venture:terrain, positioning, tam |
| 11 九地 Cửu Địa | yes | fundraise, founder:negotiate, founder:validate, pivot |
| 12 火攻 Hỏa Công | yes | campaign, outreach, launch, growth:channel-optimize |
| 13 用間 Dụng Gián | — | audit, scout, health, status, security |

A chapter number alone would not be dispatchable, so every row carries its command. Note the
load-bearing consequence: chapter choice sets LLM cost and approval gating. `pricing`, `fundraise`,
and `launch` escalate to `cloud_sonnet` with `needs_approval=True`; `pivot` reaches
`cloud_opus`/STRATEGIC. Twelve commands (`ask`, `budget`, `campaign`, `code`, `competitive`,
`finance`, `plan`, `release:ship`, `research`, `scope`, `security`) are absent from
`ESCALATION_MAP` and default to NOTIFY → `local_mlx`.

---

## 3. The 25-row map

State was verified live this session. `Phase` is where work (or the honest recording of "no work")
happens. Chapter names the dispatch authority command, not an abstract number.

| # | Slug | Phase | State | Evidence | Edition | Chapter | Dispatch |
|---|---|---|---|---|---|---|---|
| 1 | git-history-secret-purge | 0 | DONE | `leaked_secrets_detected=0`; every historical `sk-or-v1-` is a placeholder or masked UI value | community | 13 用間 Dụng Gián | `audit` |
| 2 | oss-vs-ee-directory-split | 2 | PARTIAL | `git ls-files apps/ billing/` → 0 non-dashboard, but `.claude/` **1775** + `.agents/` **447** + **4 `.pyc`** tracked | community | 6 虛實 Hư Thực | `scout` |
| 3 | gitignore-quarantine-lock | 1 | DONE | `missing_items=()`; guard test still absent | community | 6 虛實 Hư Thực | `research` |
| 4 | env-example-byok-template | 1 | DONE | all 10 `REQUIRED_ENV_EXAMPLE_KEYS` present, zero live prefixes | community | 6 虛實 Hư Thực | `competitive` |
| 5 | mit-license-and-sbom | 1 | PARTIAL | `LICENSE` MIT verified; **no repo-level SBOM** (only `.venv*/…dist-info/sboms`) | community | 13 用間 Dụng Gián | `security` |
| 6 | capability-bus-interfaces | 3 | PARTIAL | `src/core/capability.py` real; no static vendor-import bar | community | 4 軍形 Quân Hình | `code` |
| 7 | byok-local-adapters | 3 | PARTIAL | 10 keys read via env; missing-key path not asserted | community | 6 虛實 Hư Thực | `research` |
| 8 | cloud-bridge-webhooks | 3 | PARTIAL | `src/core/watcher_bridge.py` real; hosted ingestion unmetered | cloud | 3 謀攻 Mưu Công | `scope` |
| 9 | local-sandbox-runtime | 3 | DONE | `src/core/exec_runtime/` + `sandbox_bridge.py` | community | 4 軍形 Quân Hình | `test` |
| 10 | versioned-openapi-sdk | 3 | PARTIAL | FastAPI `/openapi.json` only; no versioned spec or SDK (`find -iname 'openapi*'` → none) | community | 3 謀攻 Mưu Công | `plan` |
| 11 | jwt-license-gate | 4 | PARTIAL — **now measured, not asserted** | gate mounted at `gateway_mission_routes.py:28,44-45` but conditional on `LICENSE_GATE_ENFORCE`; `entitlement_enforcer.py` has **0** `TierKey` references | cloud | 2 作戰 Tác Chiến | `finance` |
| 12 | mcu-credit-metering | 4 | DONE | 402 literal at all five probe sites (auth_routes 2, gateway_webhook 1, missions_service 3, marketplace_install 2, missions_api 1) | cloud | 2 作戰 Tác Chiến | `pricing` |
| 13 | tiered-rate-limiting | 4 | PARTIAL | limits key off a forgeable, ambiguous tier | cloud | 2 作戰 Tác Chiến | `budget` |
| 14 | managed-worker-queues | 4 | PARTIAL | `src/core/task_queue.py` in-process (711 LOC); no Redis/DO dispatch | cloud | 7 軍爭 Quân Tranh | `deploy` |
| 15 | encrypted-key-vault | 4 | PARTIAL | tenant keys in dotenv; no KMS | cloud | 11 九地 Cửu Địa | `fundraise` |
| 16 | multi-tenant-rbac-isolation | 4 | PARTIAL | `src/auth/rbac.py` + `src/core/auth_tenant.py` real; SSO absent | cloud | 11 九地 Cửu Địa | `pivot` |
| 17 | compliance-audit-ledger | 4 | DONE (community) | `saas_immutable_audit_ledger.py` (151 LOC) real | cloud | 13 用間 Dụng Gián | `health` |
| 18 | always-on-cloud-daemon | 4 | PARTIAL | `src/daemon/` scheduler real; no 24/7 SLA surface | cloud | 7 軍爭 Quân Tranh | `release:ship` |
| 19 | strategy-recipe-marketplace | 4 | PARTIAL | marketplace routers real; `marketplace_router_install.py:108` carries a Polar.sh upsell string | cloud | 5 兵勢 Binh Thế | `launch` |
| 20 | payment-webhook-activation | 5 | PARTIAL | PayOS + NOWPayments live; **17** Polar files still wired (excluding maritime/polymarket false positives) | cloud | 5 兵勢 Binh Thế | `sales` |
| 21 | sixty-second-quickstart | 1 | PARTIAL | `README.md:58` has `git clone`; no one-command start | community | 3 謀攻 Mưu Công | `ask` |
| 22 | cli-to-cloud-upsell-prompt | 4 | PARTIAL | `recharge_url` appears 3× in `license_gate.py`, in 402 detail only | cloud | 12 火攻 Hỏa Công | `campaign` |
| 23 | ci-leak-and-loc-gate | 3 | PARTIAL | `gates.yml` real; `security-hardening.yml:30` trufflehog ends `|| true` | cloud | 13 用間 Dụng Gián | `status` |
| 24 | public-benchmark-trust-badge | 4 | PARTIAL | suite reproducible (12 green); badge not wired to the Phase 0 probes | cloud | 13 用間 Dụng Gián | `audit` |
| 25 | cla-and-trademark-policy | 1 | DONE | CLA + Trademark in `CONTRIBUTING.md` | community | 13 用間 Dụng Gián | `health` |

**Coverage:** DONE 5 · PARTIAL 20 · MISSING 0.
**Chapter load:** Ch13 ×7 · Ch2 ×3 · Ch3 ×3 · Ch6 ×3 · Ch4 ×2 · Ch5 ×2 · Ch7 ×2 · Ch11 ×2 · Ch12 ×1.

**Corrections against the 2026-10-21 table:**
- Step 20 Polar surface is **17 files**, not 22 (live grep, excluding confirmed false positives).
- Steps 8, 10, 14 do have dedicated phase rows here; the old table left them undated.
- Step 11 and step 24 now cite computed probe evidence rather than an assumed verdict.

---

## 4. What is new since the last run

Phase 0 landed and is reflected above. Concretely:

- **New** `src/core/opencore/monetization_gate_probes.py` (103 LOC) computes both monetization
  flags from source evidence. It records two gaps, which are the real blocker:
  1. `gateway_mission_routes.py` calls `license_gate` conditionally on `LICENSE_GATE_ENFORCE`,
     so the gate can be turned off at runtime.
  2. `entitlement_enforcer.py` enforces usage counts only and never references `TierKey` — no
     tier entitlement is compared at all.
- `audit_repository()` now defaults both flags to `None` and probes when unset; the CLI's
  `--jwt-gate`/`--mcu-billing` became optional overrides instead of asserted `True`
  (`opencore_saas_restructuring_command.py:57-58`).
- Both test files assert `expected_verdict()` rather than the literal READY string, so a test
  goes red precisely when enforcement regresses.
- LOC budget is comfortable: largest opencore module is 157 against the 185 guard.

---

## 5. Verified defects carried forward (unchanged, still blocking)

| Defect | Evidence |
|---|---|
| **MASTER and ENTERPRISE both fold to `pro`** | `TierKey` members are `FREE, TRIAL, STARTER, GROWTH, PRO, ENTERPRISE` — **no MASTER member**; `aliases()['MASTER']→'pro'`, `aliases()['ENTERPRISE']→'pro'`, 25 aliases total. A $4,999 buyer silently gets PRO. |
| Silent free-quota fallback | `engine/license/jwt_license_generator.py:336` `quotas.get(tier, quotas["free"])` |
| Dev secret is a live fallback | `packages/license-sdk/src/core/verifier.ts:14,21` — `?? DEV_SECRET` |
| Forgeable gate checksum | `src/lib/raas-gate.ts:97,106` — non-crypto 4-hex compare |
| Non-blocking secret scan | `.github/workflows/security-hardening.yml:30` `--only-verified --fail \|\| true` |
| `.claude/` + `.agents/` would publish | 1775 + 447 tracked files, 4 `.pyc`; absent from `REQUIRED_GITIGNORE_RULES`, so hygiene stays green anyway |

Note the testing trap on the first row: `TierKey('ENTERPRISE')` names the `ENTERPRISE` *member*,
while the *alias* `aliases()['ENTERPRISE']` returns `'pro'`. An acceptance check must go through
`aliases()`, not `TierKey(...)`.

---

## 6. Non-goals held

No code was changed in this re-run. The dirty tree (38 entries) was left untouched, no
`.mekong/company.json` edit, no maritime Polar-Code files touched, no git history rewrite, and
the founder decisions on the canonical tier namespace, the price table, `.claude/`/`.agents/`
untracking, and Polar replacement remain open and unstarted.
