# Deep Brainstorm Contract: 25-Step Open-Core Public GitHub + SaaS Monetization

**Date:** 2026-10-17 | **Mode:** `/ak-bootstrap` → `/ak-brainstorm --deep` for `/idea`  
**Topic:** 25 bước tái cấu trúc thành dự án mã nguồn mở public GitHub nhưng vẫn thu được SaaS (`--deep`)  
**Stage:** Zero→PSF (Verified baseline: 0 synthetic revenue events, 100% test & hygiene pass)

---

## 1. Brainstorm Contract (4 Mandatory Fields)

- **Outcome:** Transform and lock `mekong-cli` into a dual-surface Open-Core architecture where the MIT-licensed local-first CLI & runtime (`src/core/`, `src/cli/`) can be pushed safely to public GitHub for organic PLG adoption, while monetizing the Hosted Cloud Control Plane via HS256 JWT tier gating (`BASIC` / `PREMIUM` / `ENTERPRISE` / `MASTER`), SQLite/Cloud `MCUBilling` (`HTTP 402 Payment Required`), PayOS VietQR / NOWPayments HMAC-SHA256 webhooks, and an immutable SHA-256 `AuditLedger`.
- **Constraints:**
  1. Every Python module must remain strictly $\le 185\text{ LOC}$ (`development-rules.md` & `test_company_blueprint_sync.py`).
  2. `src/core/` must remain 100% provider-neutral (zero vendor SDK imports; verified by `tests/test_core_boundary.py`).
  3. Private client directories (`apps/`, `billing/`, `.orchestrate/`, `*.pem`, `.env*`) must stay quarantined (`git ls-files apps/ billing/` == 0).
  4. Zero synthetic revenue pollution in `.mekong/company.json` (`revenue_events: []`).
- **Non-Goals:**
  1. Do not publish proprietary client apps (`apps/`) or internal billing operations (`billing/`) to the public Git index.
  2. Do not claim unverified customer counts, TAM forecasts, or synthetic billing events as commercial traction.
  3. Do not replace the MIT license on the public core CLI or require cloud login for offline local BYOK execution.
- **Acceptance Criteria:**
  1. `python3 -m src.main idea run "25 bước tái cấu trúc thành dự án mã nguồn mở public github nhưng vẫn thu được SaaS" --deep --json` exits 0 and emits the full `brainstorm_contract` + 25-step synthesis.
  2. `python3 -m src.main idea brainstorm --deep` and `python3 -m src.main opencore-saas brainstorm --deep` exit 0 with `readiness_verdict == "PUBLIC_GITHUB_SAAS_READY"`.
  3. All 25 steps (`TWENTY_FIVE_OPENCORE_STEPS`) are verified across `tasks.md`, `plan.md`, `.mekong/company.json`, and this brainstorm contract.
  4. `pytest` passes 100% across `test_idea_deep_opencore_brainstorm.py`, `test_company_blueprint_sync.py`, `test_opencore_saas_25_step_suite.py`, and `test_core_boundary.py`.

---

## 2. Live Repository Evidence (Verified State)

- **Filesystem & Git Quarantine:** `.gitignore` enforces `apps/`, `billing/`, `*.pem`, `.orchestrate/`; `git ls-files apps/ billing/` returns `0` tracked files.
- **Secret Hygiene:** `.env.example` contains all 10 required BYOK & payment keys (`OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, `ZALO_OA_SECRET_KEY`, `NOWPAYMENTS_API_KEY`, `NOWPAYMENTS_IPN_SECRET`, `PAYOS_CLIENT_ID`, `PAYOS_API_KEY`, `PAYOS_CHECKSUM_KEY`, `JWT_SECRET`) with `0` leaked live prefixes (`sk-or-v1-`, `sk-ant-`, `AIzaSy`).
- **Legal & IP Foundation:** Root `LICENSE` (MIT) and `CONTRIBUTING.md` (CLA + Trademark Policy) verified on disk.
- **Monetization Gates Active:** `src/middleware/license_gate.py` (HS256 JWT + `X-Mekong-License`), `src/core/mcu_billing.py` (1 MCU = 1 credit + HTTP 402), `src/raas/payos_webhook_handler.py` (HMAC-SHA256 + anti-replay), and `src/core/opencore/saas_immutable_audit_ledger.py` (SHA-256 chain) are wired and tested.

---

## 3. Option Exploration & Trade-Off Matrix (YAGNI → KISS → DRY)

| Option | Architecture | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Option A (Recommended)** | **25-Step Open-Core (MIT Public Core + Cloud SaaS Control Plane)** | Zero-CAC GitHub PLG funnel; BYOK local trust; recurring SaaS revenue via JWT tiers, MCU HTTP 402 & PayOS VietQR; strict IP quarantine | Requires automated CI leak & boundary gates (already built in Phase 560) | **SELECTED** |
| **Option B** | **100% Pure Open-Source Monorepo (MIT + Donations)** | Zero boundary maintenance | No recurring SaaS moat; exposes private tenant workflows (`apps/`) | Rejected |
| **Option C** | **100% Closed-Source Proprietary SaaS** | Simple IP containment | Loses GitHub developer adoption, community recipes, and local-first trust | Rejected |

---

## 4. 25-Step Open-Core vs. SaaS Architecture Matrix (5 Phases × 3 Lenses)

### Phase 1: Codebase Split & Secret Hygiene (`PHASE_1_SPLIT_AND_HYGIENE`)
- *Tri-Layer:* **[Business]** Dual-distribution moat | **[Agentic]** Safe commit/worktree guards | **[Governance]** Zero leaked secrets.
1. `git-history-secret-purge` — Clean commit history (OSS) vs. Zero leaked prod keys (SaaS)
2. `oss-vs-ee-directory-split` — `src/core` + `src/cli` MIT (OSS) vs. `apps/` + `billing/` isolated (SaaS)
3. `gitignore-quarantine-lock` — `.gitignore` guardrails (OSS) vs. Private tenant data blocked (SaaS)
4. `env-example-byok-template` — `.env.example` template (OSS) vs. Managed cloud env vault (SaaS)
5. `mit-license-and-sbom` — MIT `LICENSE` + SBOM (OSS) vs. Commercial SLA terms (SaaS)

### Phase 2: Core Boundary & Plugin Seams (`PHASE_2_PLUGIN_AND_SEAMS`)
- *Tri-Layer:* **[Business]** Zero cloud cost for free users | **[Agentic]** Provider-neutral tool dispatch | **[Governance]** Fail-closed local sandbox.
6. `capability-bus-interfaces` — `CapabilityBus` protocol (OSS) vs. Managed cloud providers (SaaS)
7. `byok-local-adapters` — User-supplied API keys (OSS) vs. Zero-config hosted inference (SaaS)
8. `cloud-bridge-webhooks` — `WatcherBridge` client stub (OSS) vs. Hosted webhook ingestion (SaaS)
9. `local-sandbox-runtime` — Single-operator CLI (OSS) vs. Multi-region cloud workers (SaaS)
10. `versioned-openapi-sdk` — Public SDK & schemas (OSS) vs. Metered API gateway (SaaS)

### Phase 3: Cloud Control Plane & Auth (`PHASE_3_CLOUD_CONTROL_PLANE`)
- *Tri-Layer:* **[Business]** Usage & tier monetization | **[Agentic]** Metered autonomous loops | **[Governance]** Stateless JWT & ACID credits.
11. `jwt-license-gate` — Local bypass in pytest (OSS) vs. FastAPI HS256 `license_gate` (SaaS)
12. `mcu-credit-metering` — Mock local credit ledger (OSS) vs. `MCUBilling` + HTTP 402 recharge (SaaS)
13. `tiered-rate-limiting` — FREE tier defaults (OSS) vs. `BASIC`/`PREMIUM`/`ENTERPRISE`/`MASTER` (SaaS)
14. `managed-worker-queues` — In-memory queue (OSS) vs. Redis Cluster + Durable Objects (SaaS)
15. `encrypted-key-vault` — Local dotenv storage (OSS) vs. KMS encrypted tenant keys (SaaS)

### Phase 4: Enterprise Security & Billing (`PHASE_4_ENTERPRISE_MONETIZATION`)
- *Tri-Layer:* **[Business]** Instant VN/global fiat collection | **[Agentic]** 24/7 scheduled cron daemon | **[Governance]** TT78/SOC2 SHA-256 ledger.
16. `multi-tenant-rbac-isolation` — Single local profile (OSS) vs. Tenant isolator + RBAC/SSO (SaaS)
17. `compliance-audit-ledger` — Stdout structured logs (OSS) vs. Immutable TT78/SOC2 `AuditLedger` (SaaS)
18. `always-on-cloud-daemon` — Foreground CLI run (OSS) vs. 24/7 autonomous daemon + SLA (SaaS)
19. `strategy-recipe-marketplace` — Community recipes (OSS) vs. Verified alpha marketplace cut (SaaS)
20. `payment-webhook-activation` — `PaymentProvider` interface (OSS) vs. PayOS / NOWPayments / Polar IPN (SaaS)

### Phase 5: PLG Growth & CI Governance (`PHASE_5_PLG_GROWTH_AND_GOVERNANCE`)
- *Tri-Layer:* **[Business]** Viral CLI-to-Cloud conversion | **[Agentic]** Automated CI LOC/leak enforcement | **[Governance]** CLA & brand protection.
21. `sixty-second-quickstart` — `git clone` + `mekong` (OSS) vs. 1-click cloud workspace (SaaS)
22. `cli-to-cloud-upsell-prompt` — Quota warning banner (OSS) vs. Seamless `recharge_url` upgrade (SaaS)
23. `ci-leak-and-loc-gate` — Pre-commit `ruff` + `pytest` (OSS) vs. Automated boundary enforcement (SaaS)
24. `public-benchmark-trust-badge` — Reproducible test suite (OSS) vs. Enterprise trust verification (SaaS)
25. `cla-and-trademark-policy` — Open PR contributions (OSS) vs. Protected brand & SaaS rights (SaaS)

---

## 5. Downstream Handoff & Unresolved Questions

- **Handoff Path:** Contract & 25-step blueprint locked → `/ak:plan` (`plans/company-blueprint/plan.md` & `tasks.md`) → `/ak:cook` → `/ak:test`.
- **Unresolved Empirical Questions (Require Live Market Evidence, Not Code):**
  1. Which single vertical workflow (Zalo OA automation vs. Tax/TT78 compliance vs. AI Video Factory) yields the highest paid conversion in the first 15 founder interviews?
  2. What optimal VND-per-MCU pricing ratio maximizes repeat PayOS VietQR top-ups among solo founders after initial trial credits deplete?
