# 5-Layer Command Audit — MEKONG CLI RaaS

**Date:** 2026-03-19 | **Scope:** `.claude/commands/` (137 commands)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Commands | 137 |
| Layers Covered | 5/5 (100%) |
| RaaS-Specific | 0 (gap) |
| Coverage | 81% (137/169 target) |

---

## Layer Distribution

| Layer | Target | Actual | Gap | Status |
|-------|--------|--------|-----|--------|
| 👑 Founder | 46 | 18 | -28 | 🔴 |
| 💼 Business | 32 | 24 | -8 | 🟡 |
| 🎯 Product | 17 | 19 | +2 | ✅ |
| ⚙️ Engineering | 47 | 49 | +2 | ✅ |
| 🔧 Ops | 27 | 27 | 0 | ✅ |

---

## Critical Gaps (P0 — RaaS GTM)

| Gap | Layer | Command Needed |
|-----|-------|----------------|
| Marketplace launch strategy | Founder | `/founder:marketplace-launch` |
| RaaS pricing tier strategy | Founder | `/founder:raas-pricing` |
| Provider onboarding (B2B) | Business | `/business:provider-onboard` |
| Rental pricing optimization | Business | `/business:rental-pricing` |
| Marketplace matching engine | Engineering | `/dev:marketplace-matching` |
| Payment split/escrow | Engineering | `/dev:payment-escrow` |
| Marketplace SLA monitoring | Ops | `/ops:marketplace-sla` |

---

## Recommendations

### Phase 1: P0 Commands (Week 1-2)
Create 7 critical commands for RaaS GTM launch.

### Phase 2: P1 Commands (Week 3-4)
- `/founder:unit-economics-raas`
- `/business:revenue-share`
- `/dev:provider-verification`
- `/dev:rental-state-machine`
- `/product:provider-dashboard`
- `/ux:rental-flow`
- `/ops:provider-incident`

### Phase 3: P2 Commands (Week 5-6)
- `/founder:marketplace-metrics`
- `/business:take-rate-analysis`
- `/business:marketplace-balance`
- `/legal:provider-terms`
- `/ops:rental-dispute`

---

## Unresolved Questions

1. RaaS model: B2B2C or B2B software rental?
2. Does Polar.sh support marketplace split payments?
3. Geographic scope: Vietnam or global at launch?
4. Provider verification: manual KYC or automated?
5. Revenue model: commission %, subscription, or hybrid?

---

**Full report:** `plans/reports/5layer-command-audit-260319-raas.md`
