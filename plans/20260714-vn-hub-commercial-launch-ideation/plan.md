# MekongMind VN Commercial Launch — Plan Overview

**Date:** 2026-07-14
**Stage:** Zero → Product-Market Fit
**Verdict:** **GO** (24/30 — conditional)
**Pipeline:** `/idea` complete → ready for `/cook --auto` execution

---

## Executive Summary

MekongMind: "Hệ điều hành AI cho doanh nghiệp 1 người Việt Nam" — $49/mo subscription replacing 5-10 disconnected tools for Vietnamese solo founders (OPCs). GO verdict achieved. All product-market fit signals positive. Main gaps are commercial infrastructure — support, onboarding, legal entity — not technical blockers.

**Outputs in this directory:**
```
plans/20260714-vn-hub-commercial-launch-ideation/
├── plan.md              # This file — overview + handoff
├── go-nogo-report.md    # Full GO/NO-GO validation (24/30)
├── bmc.md               # Business Model Canvas (9 blocks)
├── prd.md               # Product Requirements Document
└── reports/
    ├── market-research-vn-opc-sector.md
    └── competitive-analysis-ai-opc-platforms.md
```

---

## GO/NO-GO Score Summary

| Dimension | Score | Note |
|-----------|-------|------|
| Market Size | 4/5 | 800K-1.2M digital OPCs; $39-58M TAM; $294K-588K Y1 SOM |
| Problem Clarity | 5/5 | Real, specific, partially solved (TT78, Zalo OA wired) |
| Differentiation | 3/5 | Good today; Zalo risk in 12-18mo; white space exists |
| Unit Economics | 4/5 | 87% gross margin; LTV:CAC 12x; watch LLM costs |
| Execution Feasibility | 3/5 | MVP+ ready; commercial infra gaps (support, legal) |
| Agentic Fit | 5/5 | 443 commands across 10 biz layers = native advantage |
| **TOTAL** | **24/30** | **GO** |

---

## Bottomsheet: Go/No-Go

| Area | Status |
|------|--------|
| Market validation | Go — segment real, spend validated |
| Product readiness | Go — 443 defs, TT78 wired, Zalo OA live |
| Pricing | Go — $49/mo justified by value replacement |
| Distribution | Go — Zalo OA + Zalo Mini App + content marketing |
| Unit economics | Go — 87% GM, LTV:CAC 12x |
| Payment infra | Partial — NOWPayments OK, VietQR recurring needs dev |
| Support infra | No-go gap — Zalo triage bot + human escalation TBD |
| Legal entity | No-go gap — VN company registration TBD |
| Customer onboarding | Partial — free pilot exists, paid conversion flow missing |
| Content/marketing | Partial — landing page done, case studies missing |

---

## Critical Path — First 90 Days

```
Week 1-2: ✅ COMPLETE — VietQR recurring billing + subscription lifecycle
  - vietqr_recurring.py: create/renew/get/expire subscriptions, idempotent bank_tx_ref
  - vn_pilot_billing.py: GET /credit-status + POST /renew endpoints
  - StorageBackend: append_subscription + load_subscriptions (JSONL + SQLite)
  - sqlite_migrations.py: subscriptions table + indexes
  - 32/32 VietQR tests pass, 185/185 pilot scope tests pass
  - Committed: 805d25d11
Week 2-4: Pilot → paid conversion (soft paywall + email sequence)
Week 4-6: 5 paying customers closed (testimonial proof)
Week 6-8: Zalo Mini App MVP (viral distribution)
Week 8-12: Content engine (10 VN articles + 5 YouTube videos)
Month 3: Review GO/NO-GO — if 5+ paid conversions, scale marketing
```

### Handoff Commands

```bash
# Option 1: Direct plan execution
/cook --auto ./plans/20260714-vn-hub-commercial-launch-ideation/plan.md

# Option 2: Bootstrap Mekong project (M2+)
mekong company init --lang vi --name "MekongMind"
mekong spec new mekongmind-vn-commercial-launch
mekong cook-auto
```

### Responsibilities Matrix

| Phase | Owner | Deliverable |
|-------|-------|------------|
| align | Founder | Confirm price, ICP, positioning — 30 min |
| define | planner + researcher | This plan + BMC + PRD ✅ DONE |
| build | fullstack-developer | VietQR billing, pilot→paid flow, Zalo Mini App |
| validate | tester | All tests passing (844+) |
| ship | deploy | CF Workers deploy + health check |
| nourish | CTO + agents | Security audit, performance baseline |
| manage | project-manager | Milestone tracking, timeline oversight |
| prep | planner | Customer support playbook (before 100 users) |
| enhance | ui-ux-designer | Marketing page redesign for VN audience |
| capture | pm + planner | Ideas + changelog from first 20 customers |
| comply | CTO + docs-manager | Legal requirement docs (TT78, tax) |

---

## Key Risks (Top 3 + Mitigation)

| # | Risk | Likelihood | Impact | Mitigation | Timeline |
|---|------|-----------|--------|-----------|----------|
| R1 | **Zalo launches native AI** | Medium | High | Build brand + community moat FIRST. Position MekongMind as "expert OPC layer on Zalo" — not a commodity chatbot. Community + case studies before Month 12. | Now → 12mo |
| R2 | **No paying customers** | Medium | High | Close 5-10 pilot → paid conversions in Q3 BEFORE any public marketing. If 0 conversions after 50 pilot activations, revisit pricing. | Month 1-3 |
| R3 | **Domestic billing friction** | Medium | Medium | VietQR recurring billing for VN customers in Week 1-2. Cross-border $49/mo from VN cards has high decline rate. | Week 1-2 |

---

## Financial Projection (Year 1)

| Month | Paid Users | ARPU | MRR | ARR |
|-------|-----------|------|-----|-----|
| 1-3 | 50 | $35 | $1,750 | — |
| 4-6 | 200 | $45 | $9,000 | — |
| 7-9 | 500 | $49 | $24,500 | — |
| 10-12 | 1,000 | $49 | $49,000 | $294K |

- Target: 500-1,000 paying users × $49/mo = $294K-588K ARR
- Burn: $3K/mo (month 1-3) → $21K/mo (month 7-12) → $96K annual
- Break-even: ~Month 8 (MRR covers burn)

---

## Unresolved Questions (from GO/NO-GO + PRD)

1. **VN legal entity:** Cong ty TNHH hay hoạt động cá nhân? Affects invoice legality + payment processing.
2. **Pilot conversion incentive:** Are pilots aware they'll be charged? Need soft paywall + time-limited free period design.
3. **Zalo OA content compliance:** Does AI-generated marketing content violate Zalo policy? Legal review needed.
4. **Support model for non-tech OPCs:** Zalo message → human? AI triage → escalation? Define before 100 users.
5. **TT78 registration:** Does MekongMind register as e-invoice provider with TCT, or does user self-register?

---

*Plan generated 2026-07-14. Pipeline: Validate → BMC → PRD → Plan → Cook.*
*All layers: [Business] + [Agentic] + [Governance]*
*Review GO/NO-GO scores after R1/R2/R3 mitigation actions complete.*
