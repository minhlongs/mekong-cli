# Mekong CLI — AI-Powered Business Operations for Vietnam

[![English](https://img.shields.io/badge/Language-English-blue.svg)](#)
[![Tiếng Việt](https://img.shields.io/badge/Ngôn%20Ngữ-Tiếng%20Việt-red.svg)](README.vi.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Open-Core: 25/25 Ready](https://img.shields.io/badge/Open--Core-25%2F25%20Ready-brightgreen.svg)](#25-step-open-core-architecture)
[![CycloneDX 1.5](https://img.shields.io/badge/SBOM-CycloneDX%201.5-blueviolet.svg)](#)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](#)
[![Dual-Rail: VietQR + NOWPayments](https://img.shields.io/badge/Dual--Rail-VietQR%20%7C%20NOWPayments-success.svg)](#commercial-raas-pricing--dual-rail-checkout)

> Open-source autonomous AI runtime for Solo Companies, Solo Vibe Coders, and Vietnamese SMEs.
> Run a full back-office team with AI agents — accounting, tax compliance, marketing video generation, and customer communication — all operating on your own infrastructure.

---

## What is Mekong CLI?

Mekong CLI is an **open-source autonomous runtime** designed for Vietnamese one-person companies and small businesses. One operator delegates business goals to specialized AI agents that plan, execute, verify, repair, and pay for tools — running locally or across managed cloud workers.

It directly powers the AI enterprise platform [mekongmind.com](https://www.mekongmind.com).

### Three Core Business Funnels

1. **Zalo OA (`zalo_oa`)** — Automated customer communication, real-time messaging, and lead capture via Zalo Official Account.
2. **Tax & Accounting (`thue_dnvn` / `ke_toan`)** — Full Vietnamese regulatory compliance: TNCN (Personal Income Tax), TNDN (Corporate Income Tax), GTGT (VAT), and Decree 123 / Circular 78 (`TT78`) electronic invoice issuance.
3. **AI Video Factory (`sophia`)** — Automated AI marketing video generation pipelines running on edge infrastructure.

Across all funnels, **39 Typer CLI command groups** are wired through `build_app()` (`python3 -c "from src.cli.app_setup import build_app; print(len(build_app().registered_groups))"`), guided by our deterministic Plan-Execute-Verify (PEV) harness.

---

## 25-Step Open-Core Architecture

Mekong CLI strictly adopts the **25-Step Open-Core Architecture**, separating the MIT-licensed local autonomous runtime from the enterprise Cloud RaaS (Robot-as-a-Service) Control Plane. This catalog is cryptographically audited and validated at 100% readiness via `src/core/opencore/phase_560_opencore_saas_readiness_engine.py`.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               Mekong CLI (MIT Open-Core)               │
                    │   Local Runtime • CapabilityBus • BYOK • 39 Commands   │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                          PLG Upsell Bridge / BYOK / Status Polling
                                                │
                                                ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               Cloud RaaS Control Plane                 │
                    │     HMAC-SHA256 RAAS_LICENSE_KEY • MCUBilling          │
                    │  Dual-Rail Checkout: VietQR (Napas) | NOWPayments (USDT)│
                    │  Multi-Tenant RBAC • Immutable TT78/SOC2 Audit Ledger  │
                    └────────────────────────────────────────────────────────┘
```

The 25 canonical steps across 5 lifecycle phases:

### Phase 1: `PHASE_1_SPLIT_AND_HYGIENE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 01 | `git-history-secret-purge` | Clean commit history without credentials | Zero leaked production keys |
| 02 | `oss-vs-ee-directory-split` | `src/core` + `src/cli` (MIT Public) | `apps/` + `billing/` private isolation |
| 03 | `gitignore-quarantine-lock` | Strict `.gitignore` quarantine guardrails | Private tenant data blocked from git |
| 04 | `env-example-byok-template` | `.env.example` BYOK config template | Managed cloud environment vault |
| 05 | `mit-license-and-sbom` | MIT `LICENSE` + CycloneDX 1.5 SBOM | Commercial SLA & enterprise terms |

### Phase 2: `PHASE_2_PLUGIN_AND_SEAMS`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 06 | `capability-bus-interfaces` | `CapabilityBus` protocol (`InMemoryCapabilityBus`) | Managed cloud providers & swarms |
| 07 | `byok-local-adapters` | User-supplied LLM API keys (BYOK) | Zero-config hosted inference |
| 08 | `cloud-bridge-webhooks` | `WatcherBridge` client & event stubs | Hosted webhook ingestion & distribution |
| 09 | `local-sandbox-runtime` | Single-operator CLI sandbox execution | Multi-region cloud worker pool |
| 10 | `versioned-openapi-sdk` | Public SDK client & OpenAPI schemas | Metered API gateway (`api.cashclaw.cc`) |

### Phase 3: `PHASE_3_CLOUD_CONTROL_PLANE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 11 | `jwt-license-gate` | Local bypass in test harness | FastAPI HMAC-SHA256 `license_gate` |
| 12 | `mcu-credit-metering` | Mock local credit balance ledger | `MCUBilling` + HTTP 402 recharge flow |
| 13 | `tiered-rate-limiting` | Unthrottled single-user local runs | Strict tier limits (`BASIC` to `MASTER`) |
| 14 | `managed-worker-queues` | In-memory synchronous / async task queues | Redis Cluster + Cloudflare Durable Objects |
| 15 | `encrypted-key-vault` | Local `.env` storage with sanitizers | Cloud KMS-encrypted tenant credential vault |

### Phase 4: `PHASE_4_ENTERPRISE_MONETIZATION`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 16 | `multi-tenant-rbac-isolation` | Single local operator profile | Multi-tenant organization isolation + RBAC |
| 17 | `compliance-audit-ledger` | Structured stdout logs & trace telemetry | Immutable TT78 / SOC2 SHA-256 audit ledger |
| 18 | `always-on-cloud-daemon` | Foreground CLI command run | 24/7 autonomous cloud daemon with 99.9% SLA |
| 19 | `strategy-recipe-marketplace` | Local & community recipes | Curated enterprise alpha recipe marketplace |
| 20 | `payment-webhook-activation` | `PaymentProvider` interface abstraction | Replay-safe Dual-Rail IPN (VietQR / NOWPayments) |

### Phase 5: `PHASE_5_PLG_GROWTH_AND_GOVERNANCE`
| Step | Canonical Slug | MIT Open-Core (OSS) | Cloud RaaS (EE / SaaS) |
|:---:|:---|:---|:---|
| 21 | `sixty-second-quickstart` | 60-second clone & run (`git clone + mekong`)| 1-click cloud workspace provisioning |
| 22 | `cli-to-cloud-upsell-prompt` | Quota warning banner on credit depletion | Seamless `recharge_url` upgrade experience |
| 23 | `ci-leak-and-loc-gate` | Pre-commit ruff, LOC checks (`<= 185 LOC`) | Automated boundary enforcement in CI |
| 24 | `public-benchmark-trust-badge` | Reproducible pytest test suite | Enterprise trust verification & telemetry |
| 25 | `cla-and-trademark-policy` | Open-source PR contribution guide (`CLA`) | Protected trademark & commercial SaaS rights |

---

## 60-Second Quickstart (Step 21: `sixty-second-quickstart`)

Get running in less than a minute on macOS or Linux:

```bash
# 1. Clone repository
git clone https://github.com/minhlongs/mekong-cli.git
cd mekong-cli

# 2. Initialize environment & shell wrapper
source scripts/shell-init.sh

# 3. Configure Bring-Your-Own-Key (BYOK)
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-v1-your-key-here"
export LLM_MODEL="anthropic/claude-sonnet-4"

# 4. Run the CLI
mekong
```

### Try an Autonomous Goal:

```bash
# Autonomous tax calculation run with PEV verification
mekong run --goal "Tinh thue TNDN quy 1 nam 2026 cho doanh nghiep thuong mai dien tu"
```

---

## Commercial RaaS Pricing & Dual-Rail Checkout

When your business scales beyond local execution, upgrade seamlessly to the **Mekong Cloud RaaS Control Plane** for hosted worker swarms, 24/7 cloud daemons, and immutable compliance ledgers.

Our commercial tiers are backed by **Dual-Rail Checkout**:
- **Domestic Vietnam Rail:** `vietqr` (Napas 247 Instant Transfer with dynamic EMVCo QR and auto-reconciliation).
- **International Web3 Rail:** `nowpayments` (USDT / Crypto IPN with instant automated credit top-up).
- *Polar.sh Decommission:* `POST /webhook/polar` is decommissioned and permanently returns `HTTP 410 Gone` (`polar_rail_decommissioned`).

| Tier | Price (USD) | Price (VND) | Monthly Quota (MCU) | Included Features |
|:---|:---:|:---:|:---:|:---|
| **`BASIC`** | **$199** /mo | **4,975,000 ₫** | **1,500 MCU** | Hosted Control Plane, basic CLI agents, BYOK standard, VietQR payment. |
| **`PREMIUM`** | **$399** /mo | **9,975,000 ₫** | **4,000 MCU** | Multi-Agent Swarm, cloud task queues, telemetry synchronization. |
| **`ENTERPRISE`** | **$799** /mo | **19,975,000 ₫** | **10,000 MCU** | Multi-Tenant RBAC, immutable TT78 audit ledger, encrypted key vault (KMS). |
| **`MASTER`** | **$4,999** /yr | **124,975,000 ₫** | **100,000 MCU** | White-label portal, 24/7 always-on cloud daemon, custom SLA & SLA guarantee. |

*(MCU: Mekong Compute Unit. 1 credit = 1 unit of autonomous agent compute. Exchange rate: 25,000 VND / USD).*

### Instant Checkout API

```bash
# Create VietQR Napas 247 checkout session
curl -X POST https://api.cashclaw.cc/v1/checkout \
  -H "Content-Type: application/json" \
  -d '{"tier": "PREMIUM", "rail": "vietqr", "email": "founder@example.vn"}'

# Activate cryptographically signed token (Step 11b)
mekong license activate --key "MEKONG-RAAS-v1.<payload_b64>.<sig>"
```

---

## Design Intelligence

Native design-quality evaluation system adapted from Hallmark (MIT). Audit, study, and construct design systems with structured schemas and deterministic gates:

```bash
mekong ui audit page.html                 # Deterministic gate execution + 9-axis score
mekong ui study page.html --name landing # Generate DesignDNA (design.md / design.json)
mekong ui approve landing                # Persist approved DNA for multi-agent reuse
mekong ui benchmark                      # Anti-gaming fixture verification suite
```

---

## Verification & Quality Gates

Every pull request and release is verified against strict automated gates:

```bash
# 1. Verify 25-Step Open-Core & RaaS Boundary Suites
pytest tests/test_opencore_saas_25_step_suite.py \
       tests/test_core_boundary.py \
       tests/test_dual_rail_checkout.py \
       tests/test_raas_license_verifier.py \
       tests/test_durian_grab_honest_diagnosis.py \
       tests/test_idea_run_blueprint_writing.py \
       tests/test_opencore_git_boundary_guard.py \
       tests/test_github_content_25_step_sync.py -v

# 2. Check Repository Open-Core Readiness (100.0%)
python3 -c "from src.core.opencore.phase_560_opencore_saas_readiness_engine import OpenCoreSaasReadinessEngine as E; r=E.audit_repository('.'); assert r.verdict.value=='PUBLIC_GITHUB_SAAS_READY' and r.completion_pct==100.0; print('Open-Core Audit:', r.verdict.value, r.completion_pct)"

# 3. Assert Zero Codebase Drift on Core Catalog
git diff --exit-code src/core/opencore/phase_559_opencore_25_step_catalog.py
```

---

## Contributing & Governance

We welcome contributions under our Open-Core model:
- Read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).
- Security disclosures: please consult [SECURITY.md](SECURITY.md).
- Architectural specifications: see [docs/architecture.md](docs/architecture.md).

## License

Mekong CLI core is open-source software licensed under the [MIT License](LICENSE).
Copyright (c) 2026 Mekong CLI Contributors.
