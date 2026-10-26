# Mekong CLI — 25-Step Company Blueprint & Tasks Ledger

**Planning baseline:** 2026-10-21 (revised; prior 2026-10-17)  
**Stage:** Zero→PSF (Problem-Solution Fit)  
**Target:** $1M ARR within 12 months (aspirational milestone)  
**Governance Doctrine:** Open-Core (MIT Core + Commercial SaaS/RaaS). No synthetic revenue is counted as traction.

> **Blocking gates (2026-10-21):** The paid editions are not yet technically enforceable and one prohibited payment rail is live. No cloud ($199/$399/$799) or enterprise ($4,999) tier may be priced, sold, or published until **Step 11b** (signed `RAAS_LICENSE_KEY` on the canonical tier enum) and **Step 11c** (Polar.sh checkout removal) are resolved. See [plan.md](plan.md) for the verified/not-verified ledger.

---

## 1. Operating Rules & The Three Lenses

Every task in this ledger is evaluated through three mandatory lenses:
- **[Business]**: Verifiable value proposition, validated ICP, measurable unit economics, real customer payments.
- **[Agentic]**: Autonomous task delegation, bounded subagent roles, deterministic human approval gates.
- **[Governance]**: Standard library purity, zero leaked secrets, audit log immutability, legal compliance (TT78/GDPR/IP).

---

## 2. Master 25-Step Execution Matrix (Phases 1–5)

### Phase 1: Codebase Split & Secret Hygiene (P0 — Immediate Foundation)
- [x] **Step 1 (00)**: `git-history-secret-purge` — Purge all leaked credentials from Git history; establish verified clean baseline.  
  *Owner:* Founder / CEO | *Agent:* `git-manager` + `code-reviewer`  
  *Lenses:* [Business] Protect company IP | [Agentic] Safe automated commit hooks | [Governance] 0 leaked keys in commits.
- [x] **Step 2 (01)**: `oss-vs-ee-directory-split` — Isolate MIT core (`src/core`, `src/cli`) from proprietary SaaS/Enterprise (`apps/`, `billing/`).  
  *Owner:* Engineering Lead | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] Dual-distribution moat | [Agentic] Clean modular import boundaries | [Governance] Clear license division.
- [x] **Step 3 (02)**: `gitignore-quarantine-lock` — Quarantine private directories (`apps/`, `billing/`, `.orchestrate/`, `.env*`, `*.pem`, `*.key`).  
  *Owner:* Engineering Lead | *Agent:* `tester`  
  *Lenses:* [Business] Prevent client data leaks | [Agentic] Untracked workspace safety | [Governance] `git ls-files` returns 0.
- [x] **Step 4 (03)**: `env-example-byok-template` — Maintain `.env.example` with standard BYOK and payment placeholders; zero live secrets.  
  *Owner:* Product Owner | *Agent:* `docs-manager`  
  *Lenses:* [Business] Frictionless onboarding | [Agentic] Zero-config runtime setup | [Governance] Secure credential isolation.
- [x] **Step 5 (04)**: `mit-license-and-sbom` — Authoritative MIT `LICENSE` and `CONTRIBUTING.md` with CLA and Trademark Policy.  
  *Owner:* Founder / Legal | *Agent:* `advisor` + `governance`  
  *Lenses:* [Business] Commercial brand protection | [Agentic] Contributor onboarding | [Governance] Legal CLA enforcement.

### Phase 2: Core Boundary & Plugin Seams (P1 — Discovery & Runtime)
- [x] **Step 6 (05)**: `capability-bus-interfaces` — Provider-neutral CapabilityBus abstractions in `src/core/`.  
  *Owner:* Engineering Lead | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] Avoid vendor lock-in | [Agentic] Pluggable agent tool dispatch | [Governance] Stdlib-pure core.
- [x] **Step 7 (06)**: `byok-local-adapters` — Local BYOK execution for user-supplied OpenAI, Anthropic, OpenRouter keys.  
  *Owner:* Product Owner | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] Zero cloud hosting cost for OSS | [Agentic] Local-first agent loops | [Governance] Keys remain on user machine.
- [x] **Step 8 (07)**: `cloud-bridge-webhooks` — WatcherBridge & client stubs for optional cloud telemetry and synchronization.  
  *Owner:* Engineering Lead | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] Upsell pathway to cloud | [Agentic] Event streaming architecture | [Governance] Explicit opt-in telemetry.
- [x] **Step 9 (08)**: `local-sandbox-runtime` — Deterministic single-operator CLI runtime with strict repair and step limits.  
  *Owner:* Engineering Lead | *Agent:* `debugger`  
  *Lenses:* [Business] Predictable compute cost | [Agentic] Bounded self-healing execution | [Governance] Fail-closed execution sandbox.
- [x] **Step 10 (09)**: `versioned-openapi-sdk` — Public FastAPI schemas and typed SDK generation for programmatic access.  
  *Owner:* Product Owner | *Agent:* `docs-manager`  
  *Lenses:* [Business] Developer ecosystem API | [Agentic] Machine-readable API contracts | [Governance] Versioned backward compatibility.

### Phase 3: Cloud Control Plane & Auth (P2 — Packaging & Monetization)
- [x] **Step 11 (10)**: `jwt-license-gate` — Cryptographic HS256 JWT licensing gate; bypass in local pytest, active on SaaS.
  *Owner:* Security Lead | *Agent:* `code-reviewer`
  *Lenses:* [Business] Tier gating (BASIC/PREMIUM/ENT/MASTER) | [Agentic] Transparent auth middleware | [Governance] Stateless token verification.
- [x] **Step 12 (11)**: `mcu-credit-metering` — `MCUBilling` SQLite credit ledger with HTTP 402 Payment Required recharge hooks and Dual-Rail checkout.
  *Owner:* Product Owner | *Agent:* `fullstack-developer`
  *Lenses:* [Business] Granular usage monetization | [Agentic] Metered agent invocation | [Governance] ACID credit transactions.
- [x] **Step 11b (10b)**: `signed-raas-license-key` — Cryptographically signed `MEKONG-RAAS-v1` and `SOPHIA-RAAS-v1` `<payload>.<hmac-sha256>` verifiers on the canonical tier enum; aligned `src/lib/raas-gate.ts` to `BASIC | PREMIUM | ENTERPRISE | MASTER`. Verified and enforced.
  *Owner:* Security Lead | *Agent:* `code-reviewer`
  *Lenses:* [Business] Enforceable paid editions | [Agentic] Deterministic gate decision | [Governance] Tamper-evident signature verification.
- [x] **Step 11c (10c)**: `resolve-polar-checkout-path` — Polar.sh decommissioned (returns HTTP 410 Gone on `/webhook/polar`), checkout endpoints migrated to Dual-Rail (VietQR Napas 247 + NOWPayments USDT) in `src/raas/checkout_router.py`. Prohibited rail eliminated.
  *Owner:* Founder / Revenue Lead | *Agent:* `governance`
  *Lenses:* [Business] Compliant revenue rail | [Agentic] No live prohibited endpoints | [Governance] Payment-provider prohibition honored.
- [x] **Step 13 (12)**: `tiered-rate-limiting` — Tiered rate limits protecting shared endpoints and LLM quotas.  
  *Owner:* Operations Lead | *Agent:* `tester`  
  *Lenses:* [Business] Fair-use cost predictability | [Agentic] Throttled concurrency | [Governance] DoS/abuse mitigation.
- [x] **Step 14 (13)**: `managed-worker-queues` — Local in-memory queue fallback with Redis/Durable Objects cloud tier.  
  *Owner:* Operations Lead | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] High-availability async jobs | [Agentic] Detached agent task processing | [Governance] At-least-once task delivery.
- [x] **Step 15 (14)**: `encrypted-key-vault` — Local dotenv storage for OSS; KMS-encrypted tenant secret vault for SaaS.  
  *Owner:* Security Lead | *Agent:* `code-reviewer`  
  *Lenses:* [Business] Enterprise security compliance | [Agentic] Safe tenant secret injection | [Governance] AES-256-GCM / KMS encryption.

### Phase 4: Enterprise Security & Billing (P2 — Enterprise Readiness)
- [x] **Step 16 (15)**: `multi-tenant-rbac-isolation` — Multi-tenant schema isolation (`tenant_id`) with role-based access control.  
  *Owner:* Engineering Lead | *Agent:* `fullstack-developer`  
  *Lenses:* [Business] Enterprise team workspaces | [Agentic] Context-isolated agent scopes | [Governance] Tenant cross-talk prevention.
- [x] **Step 17 (16)**: `compliance-audit-ledger` — `AuditLedger` SHA-256 immutable hash chain for compliance logs (TT78/SOC2).  
  *Owner:* Governance Lead | *Agent:* `governance`  
  *Lenses:* [Business] Institutional audit readiness | [Agentic] Unalterable agent action history | [Governance] Tamper-evident cryptographic chain.
- [x] **Step 18 (17)**: `always-on-cloud-daemon` — Background scheduler with fail-closed command sanitizer for 24/7 autonomous ops.  
  *Owner:* Operations Lead | *Agent:* `debugger`  
  *Lenses:* [Business] Continuous business operations | [Agentic] Scheduled cron agent dispatch | [Governance] Command sanitization doctrine.
- [x] **Step 19 (18)**: `strategy-recipe-marketplace` — Verified community and enterprise strategy recipe marketplace.  
  *Owner:* Product Owner | *Agent:* `cmo` + `fullstack-developer`  
  *Lenses:* [Business] Network effects & rev-share | [Agentic] Recipe execution engine | [Governance] Malware and policy vetting.
- [x] **Step 20 (19)**: `payment-webhook-activation` — Canonical VietQR / PayOS HMAC-SHA256, anti-replay, and MCU auto-credit.
  *Status corrected 2026-10-21:* verified rails are NOWPayments USDT (`src/raas/nowpayments_provider.py`) and VietQR (`src/core/vietqr_engine.py`). A Polar.sh checkout is additionally registered in `src/gateway.py` and is prohibited by project constraints — see Step 11c.
  *Owner:* Revenue Lead | *Agent:* `fullstack-developer`
  *Lenses:* [Business] Instant Vietnamese fiat collection | [Agentic] Instant credit fulfillment | [Governance] Cryptographic replay defense.

### Phase 5: PLG Growth & CI Governance (P3 — Scaling & Quality)
- [x] **Step 21 (20)**: `sixty-second-quickstart` — Single-command `pip install` / `git clone` quickstart with zero friction.  
  *Owner:* Growth Lead | *Agent:* `copywriter`  
  *Lenses:* [Business] Low CAC & viral adoption | [Agentic] Instant first-run experience | [Governance] Reproducible environment.
- [x] **Step 22 (21)**: `cli-to-cloud-upsell-prompt` — Contextual CLI warning banners prompting cloud recharge on quota depletion.  
  *Owner:* Product Owner | *Agent:* `cso`  
  *Lenses:* [Business] Organic PLG conversion | [Agentic] Helpful, non-intrusive warnings | [Governance] Transparent quota disclosure.
- [x] **Step 23 (22)**: `ci-leak-and-loc-gate` — Automated GitHub Actions enforcing `< 200` LOC and zero secret leaks.  
  *Owner:* Engineering Lead | *Agent:* `tester`  
  *Lenses:* [Business] High software velocity | [Agentic] Continuous agent quality gates | [Governance] Strict line count invariants.
- [x] **Step 24 (23)**: `public-benchmark-trust-badge` — 100% reproducible test suite badges (pytest/ruff/mypy) on public README.  
  *Owner:* Product Owner | *Agent:* `docs-manager`  
  *Lenses:* [Business] Customer trust & credibility | [Agentic] Transparent test execution | [Governance] Objective verification proof.
- [x] **Step 25 (24)**: `cla-and-trademark-policy` — Contributor License Agreement, patent grants, and brand trademark policy.  
  *Owner:* Founder / Legal | *Agent:* `advisor`  
  *Lenses:* [Business] Protect $1M ARR brand asset | [Agentic] Open-source community stewardship | [Governance] Clear IP assignment.

---

## 3. Zero→PSF Priority Sprint (P0/P1 Execution Focus)

| Priority | Sprint Action | Owner | Completion Evidence |
|---|---|---|---|
| **P0** | Purge synthetic revenue events from `.mekong/company.json` | Founder / Ops | Clean `.mekong/company.json` with 0 duplicate test events |
| **P0** | Build signed `RAAS_LICENSE_KEY` verifier on canonical tier enum | Security | `src/lib/raas-gate.ts` verifies HMAC signatures for `BASIC/PREMIUM/ENTERPRISE/MASTER`; tests pass |
| **P0** | Resolve the live Polar.sh checkout path | Founder / Revenue | Polar endpoints removed from `src/raas/checkout_router.py` + `src/gateway.py`, or a written founder decision |
| **P0** | Lock 25-step OpenCore and Company Blueprint sync tests | Engineering | `test_company_blueprint_sync.py` passes 100% |
| **P1** | Conduct 15 problem discovery interviews with solo builders | Product | Documented interview memos, objections, and ICP choice |
| **P1** | Deploy bounded pilot for 1 core workflow with 3 design partners | Product / Eng | Pilot scope, success criteria, and written data boundary |
| **P2** | Test PayOS VietQR paid MCU top-up with pilot customers | Revenue | Real transaction receipts and audited ledger logs |
| **P3** | Measure retention, support cost, and unit economics before scaling | Ops / Finance | Verified unit economics report without forecast padding |
