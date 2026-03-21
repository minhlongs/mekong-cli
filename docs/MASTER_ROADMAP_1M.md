# 🎯 MASTER ROADMAP: $1M AgencyOS

**Single Source of Truth** - Consolidates all PRDs and Revenue Plans

Updated: 2026-03-21 | Status: EXECUTION (RaaS GTM Phase — Full Stack Complete + Dashboard Ready)

---

## 💰 REVENUE TARGET: $1,000,000/year

| Stream             | Target | Margin  | Priority   |
| ------------------ | ------ | ------- | ---------- |
| 💳 RaaS Credits    | $300k  | >80%    | 🔴 Phase 1 |
| 🏢 Agency-in-a-Box | $500k  | >70%    | 🟡 Phase 2 |
| 🛒 Marketplace     | $200k  | 30% cut | 🟢 Phase 3 |

---

## 🏗️ ARCHITECTURE (Hub-and-Spoke)

```
        ┌──────────────────────────┐
        │      MONEY LAYER         │  ← $300k RaaS Credits
        │   Next.js + Stripe       │
        └───────────┬──────────────┘
                    │
        ┌───────────▼──────────────┐
        │      ENGINE LAYER        │  ← Core Infrastructure
        │  OpenClaw + BullMQ       │
        └───────────┬──────────────┘
                    │
        ┌───────────▼──────────────┐
        │      VIRAL LAYER         │  ← $200k Marketplace
        │   Mekong CLI + Recipes   │
        └──────────────────────────┘
```

---

## 📅 EXECUTION PHASES

### Phase 1: PMF ($0 → $50k) - Week 1-4

**Goal:** Validate với 10 paying customers

| Task               | Owner                 | Status      |
| ------------------ | --------------------- | ----------- |
| ✅ Mekong CLI Core | genesis.py            | DONE        |
| ✅ ClaudeKit DNA   | 52 skills             | DONE        |
| ✅ vibe-analytics  | CC CLI                | DONE        |
| ✅ Landing Page    | apps/agencyos-landing | DONE        |
| ✅ Stripe Checkout | Pre-order $99         | DONE        |

**Target Audience:** CEO/Shop Owner Lead Gen VN

---

### Phase 2: Scale ($50k → $300k) - Month 2-6

| Task               | Description            |
| ------------------ | ---------------------- |
| ProductHunt Launch | English version        |
| AppSumo LTD        | Bootstrap capital      |
| Enterprise Pilot   | 5 agencies @ $2k/month |

---

### Phase 3: Domination ($300k → $1M) - Month 6-12

| Task            | Description            |
| --------------- | ---------------------- |
| Agency-in-a-Box | $10k setup + $2k/month |
| Marketplace     | 30% cut từ recipes     |
| Franchise Model | White-label license    |

---

## ✅ COMPLETED ITEMS

- [x] MASTER_PRD_AGENCYOS_RAAS.md - Architecture
- [x] PRD_AGENCY_GENESIS.md - Automation Loop
- [x] PRD_MEKONG_GENESIS.md - CLI Blueprint
- [x] ROADMAP_1M.md - Revenue Breakdown
- [x] Mekong CLI Core (agent_base, parser, main.py)
- [x] ClaudeKit DNA extracted (52 skills)
- [x] Proxy Health (Claude + Gemini hybrid)
- [x] CC CLI vibe-analytics bootstrap (researcher 166+ tools)
- [x] AgencyOS Landing Page (Next.js + Tailwind v4)
- [x] Stripe Checkout Integration (Pre-order $99)
- [x] Engine Layer Setup (OpenClaw + BullMQ) - Code Complete
- [x] Engine Layer Database Integration (PostgreSQL + Prisma)
- [x] Mekong CLI Recipe System Integration - Executor & Parser implemented
- [x] Agency-in-a-Box Setup Automation
- [x] Marketplace Foundation - Recipe Registry
- [x] Autonomous Genesis Protocol - LeadHunter, ContentWriter, RecipeCrawler
- [x] Mekong CLI Interactive UI - Module Selector
- [x] Phase 8: Production Hardening - SQLite Integration, Retry Logic, Zombie Job Cleanup
- [x] OpenClaw Worker AGI Level 5 Upgrade (Self-Testing, Self-Scanning, Self-Learning)
- [x] AGI Deep 10x Master Integration (L10-L12):
  - L10: Cross-Session Memory FIX — `self-analyzer.js` + `task-queue.js` track missions per session
  - L11: ClawWork Economic Benchmark — `clawwork-integration.js` generates economic insights
  - L12: Moltbook Agent Identity — `moltbook-integration.js` manages agent metadata persistence
- [x] Vector Service Local Fallback — `vector-service.js` 1536-dim hash embedding fallback
- [x] Evolution Engine Improvements — Actionable failure classification (typescript_error, build_failure, test_failure, etc.)

---

## 🔄 IN PROGRESS

- [ ] ProductHunt Launch preparation
- [ ] Enterprise Pilot campaign (5 agencies @ $2k/month)
- [ ] Deep OpenClaw SDK integration — sub-module facades
- [ ] npm publish — trigger GitHub workflow for 4 packages

---

## ✅ RECENTLY COMPLETED (March 2026)

- [x] OpenClaw Engine SDK v1.0 — publishable TypeScript facade
- [x] Sale RaaS Documentation — onboarding, enterprise pitch, support SOP
- [x] RaaS Gateway v5.0 — 18 feature waves on Cloudflare Workers (Hono + D1/KV/R2)
- [x] RaaS SDK (@mekong/raas-sdk) — typed TypeScript client for gateway API
- [x] CLI Cloud Integration — 11 commands: signup/login/logout/whoami/mission/billing
- [x] ROIaaS DNA v0.4 GATE — License key verification, HMAC, feature gating, tier enforcement
- [x] ROIaaS DNA v0.5 LICENSE UI — Key generator, admin CRUD, audit log, tier migration
- [x] ROIaaS DNA v0.6 WEBHOOK — Polar.sh webhooks, subscription manager, receipt store
- [x] ROIaaS DNA v0.7 METERING — Event collector, JSONL store, analyzer, limiter, cost calculator
- [x] ROIaaS DNA v0.8 ANALYTICS — ROI calculator, AGI scorer, revenue tracker, growth analyzer
- [x] Skill Marketplace — Registry with publish/search/rate/getPopular
- [x] Landing Page — 5 pages: hero, ROI calculator, case studies, CLI demo, pricing+checkout
- [x] Polar.sh Checkout — Full flow: signup → JWT → checkout session → redirect
- [x] Sales Collateral — Competitive battlecard, one-pager, objection handlers
- [x] npm publish workflow — GitHub Actions for 3 public packages (@mekong/raas-sdk, raas-marketplace, mekong-cli-core)
- [x] RaaS Admin Dashboard — tenant/credit/mission management UI (packages/raas-dashboard/public/)
- [x] PEV Bridge — CLI cloud run with Plan→Execute→Verify loop (packages/mekong-cli-core/src/core/pev-bridge.ts)
- [x] E2E Integration Tests — 13 tests covering CLI→Gateway→Polar flow
- [x] XSS Security Fix — dashboard numeric sanitization
- [x] OpenClaw Engine SDK v1.0 — publishable TypeScript facade
- [x] Sale RaaS Documentation — onboarding, enterprise pitch, support SOP
- [x] 1,028+ tests ALL GREEN across packages

---

## 📊 KPIs TO TRACK

| Metric        | Target   | Current   |
| ------------- | -------- | --------- |
| Pre-orders    | 100      | 0         |
| MRR           | $10k     | $0        |
| CLI Downloads | 1,000    | 0         |
| GitHub Stars  | 500      | 0         |
| npm Packages  | 4        | 4 (ready) |
| Gateway Waves | 20       | 20        |
| Test Coverage | 1,000+   | 1,028+    |
| RaaS Commands | 15       | 15        |

---

## 🔄 VERTICAL SYNC (No-Conflict Guard)

All sub-projects MUST align with this master roadmap:

| Vertical                   | Revenue Path         | Status                  |
| -------------------------- | -------------------- | ----------------------- |
| **Apex-OS** (Fintech)      | Agency-in-a-Box $25k | Archived Nov 2025 plans |
| **Sophia** (Video Factory) | $1,200/mo tier       | Active                  |
| **Cơm Ánh Dương** (F&B)    | Turnkey POS          | Active                  |
| **Well** (Ecommerce)       | PayOS VN             | Active (100% Tests Pass, 0 Bugs) |

**Rules:**

1. All specialized agents → packaged as Mekong CLI "Recipes"
2. Single credit pool → all RaaS services
3. Data parity → AgencyOS Pulse analytics

---

## 📂 ARCHIVED PLANS (Historical Reference)

These plans are now DEPRECATED - information merged into this master:

| File                                  | Date     | Notes                                       |
| ------------------------------------- | -------- | ------------------------------------------- |
| `docs/archive/OPTIMAL_STRATEGY_1M.md` | Nov 2025 | Apex-OS Blitzkrieg (7 Binh Pháp principles) |
| `docs/archive/MASTER_PLAN_1M.md`      | Nov 2025 | Apex-OS Agentic Teams                       |
| KI `roadmap_1m_master.md`             | Feb 2026 | Phase-gated execution                       |

---

## 🗂️ RELATED DOCUMENTS

| Document                                      | Purpose                |
| --------------------------------------------- | ---------------------- |
| [MASTER_PRD](./MASTER_PRD.md)   | Technical Architecture |
| [PRD_AGENCY_GENESIS](./PRD_AGENCY_GENESIS.md) | Automation Loop        |
| [PRD_MEKONG_GENESIS](./PRD_MEKONG_GENESIS.md) | CLI Blueprint          |

---

> **⚠️ SINGLE SOURCE OF TRUTH**
>
> This is the ONLY active $1M roadmap. All other files are ARCHIVED.
> Update THIS file when priorities change.
