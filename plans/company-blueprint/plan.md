# Mekong CLI — Company Execution Plan

**Planning baseline:** 2026-10-21 (revised; prior baseline 2026-10-17)  
**Stage:** Zero→PSF, based on the existing framework’s report of zero paying customers and no formal beta; reconfirm before external use.  
**12-month target:** $1M ARR, an aspiration rather than a forecast.  
**Governance Doctrine:** Open-Core (MIT Core + Commercial SaaS/RaaS). See [tasks.md](tasks.md) and [brainstorm-25-step-opencore-saas.md](brainstorm-25-step-opencore-saas.md).

## Open-core boundary — verified status (2026-10-26)

The dual-license model is **operational and verified**:

- **Cryptographic signed license gate active.** `src/core/raas_license_verifier.py` (stdlib-pure HMAC-SHA256) and `src/lib/raas-gate.ts` enforce `MEKONG-RAAS-v1` and `SOPHIA-RAAS-v1` tokens on the canonical `BASIC | PREMIUM | ENTERPRISE | MASTER` tiers with full signature and expiry verification.
- **Dual-Rail checkout operational; Polar.sh decommissioned.** `src/raas/checkout_router.py` routes payments through VietQR Napas 247 and NOWPayments USDT; Polar.sh endpoints return HTTP 410 Gone with zero live `api.polar.sh` dependencies.

Verified and working today: MIT community core, the canonical four-tier enum in `src/core/tier_fallback_chain.py`, NOWPayments USDT settlement with IPN verification in `src/raas/nowpayments_provider.py`, and the VietQR domestic engine in `src/core/vietqr_engine.py`.

## Company thesis

Mekong CLI is an open-source, local-first AI agent runtime for solo companies and solo builders. The current repository documents a provider-neutral runtime lifecycle and governance boundaries. The initial ICP hypothesis is a technically capable solo founder or very small team with one recurring workflow that is costly or error-prone today. The commercial model couples an MIT public core with optional paid hosted control plane, enterprise security, and VietQR/PayOS MCU top-up services.

Keep business outcomes separate from implementation volume. Repository size, command counts, agent definitions, synthetic billing events, and roadmap completion do not establish customer traction.

## Operating map

| Layer / department | Key actions | Agent / owner | Governance |
|---|---|---|---|
| Founder | Select ICP and workflow; conduct discovery; set priorities; review monthly evidence | CEO / Founder | Approves commitments, claims, spend, customer promises, and pivots |
| Business and Revenue | Interview, qualify, run design-partner pilots, test one offer and channel | AE/CMO agents / Founder | Consent, opt-out, approved messaging, recorded actuals |
| Product | Translate observed pain into one workflow, onboarding, and success criteria | PM / Product owner | Evidence-linked requirements; explicit exclusions |
| Engineering | Improve selected workflow reliability, verification, install, provider handling, and measurement | ENG / Engineering owner | Review, tests, rollback, cost and permission limits |
| Operations | Track incidents, support, activation, repeat use, and delivery cost | OPS / Operations owner | Minimum necessary telemetry, retention, access controls |
| Governance | Maintain claims ledger, data-flow map, legal questions, contracts, and decision log | Risk agent / Founder with counsel | Qualified review for legal, tax, privacy, AI, and financing matters |

## Six-month roadmap & 5-phase open-core alignment

| Period / Phase | Business outcome | Agentic work | Exit evidence |
|---|---|---|---|
| Months 1–2 (Phases 1–2) | Confirm ICP and recurring job; lock Open-Core boundary | Interview synthesis, workflow demo, claims cleanup, BYOK adapters | 15 interviews planned; clean git index (`apps/` untracked); 0 leaked keys |
| Month 3 (Phase 3) | Test repeat value; wire cloud control plane & MCU billing | Bounded design-partner pilot, license gate, credit metering | Up to three pilot partners; consent and success criteria; HTTP 402 recharge |
| Months 3–4 (Phase 4) | Decide the Polar.sh removal path; build a signed RAAS_LICENSE_KEY verifier on the canonical tier namespace | License-gate design, HMAC signing/verification, migration of `src/lib/raas-gate.ts` off `free/pro/enterprise` | Signed keys verified in tests; Polar endpoints either removed or an explicit founder decision recorded |
| Months 5–6 (Phase 5) | Test paid offer only if the gate enforces it; deploy VietQR & immutable audit ledger | Billing/onboarding planning, VietQR activation, audit ledger | Actual payment records if any; activation, repeat use, support effort |
| Month 6 (Phase 5) | Decide whether to continue, narrow, or scale; CI quality gates | Cohort review, PLG quickstart, automated LOC/leak verification | Decision memo; no scaling if retention or economics remain unknown |

## Months 7–12

Scale only after repeat paid use, retention, acquisition, and contribution margin are measured and acceptable. Update the $1M ARR aspiration from real price, capacity, and cohort evidence. Do not insert a customer-count forecast before pricing and retention are observed.

## North Star and review cadence

At Zero→PSF, track weekly verified workflow completions by target users and the evidence that the result was useful. After paid use begins, add retained paying accounts and actual recurring revenue. Review weekly experiments and incidents; review stage, cash, metrics, risks, and decisions monthly.

## Source and assumption register

- Repository facts: README.md, docs/core-contract.md, docs/autonomy-model.md, HARNESS.md, and LICENSE.
- Vietnam market context: the NSO reported 297.5 thousand newly established and resumed enterprises in 2025. This broad count is not a solo-founder or addressable-customer estimate. [NSO source](https://www.nso.gov.vn/en/data-and-statistics/2026/01/socio-economic-situation-in-the-fourth-quarter-and-2025/).
- Legal starting points and official sources are listed in [Step 02](02-ipo-readiness.md). They are not a legal applicability opinion.
- Unknown until measured: paying users, pricing, conversion, retention, CAC, LTV, gross margin, TAM/SAM/SOM, and product-market fit.
