---
title: "Chien Dich Go-Live & CRO AgencyOS"
description: "Ke hoach dong goi Vibe SDK, toi uu CRO 200%, va Edge migration < 50ms"
status: pending
priority: P1
effort: 3w
branch: master
tags: [strategy, cro, edge, sdk, f&b]
created: 2026-02-27
---

# Chien Dich Go-Live & CRO AgencyOS

## Tong Quan

AgencyOS chuyen tu internal tool thanh **RaaS platform** qua 3 truc chien luoc:
1. Dong goi WellNexus thanh Vibe SDK (Agency-in-a-Box)
2. Tang CVR 200% bang CRO co he thong
3. Edge backend migration giam latency xuong < 50ms

## Kien Truc Hien Tai

```
agencyos-landing (Next.js) → Marketing + CRO
agencyos-web (Next.js)     → Dashboard + Admin
well (React/Vite)          → WellNexus template (Aura Elite)
openclaw-worker (Node.js)  → Tom Hum daemon
Cloudflare Workers         → API Gateway (da co)
PostgreSQL + Supabase Auth → Data layer
Polar.sh                   → Payment (ONLY provider)
```

## Phases

| # | Phase | Effort | Priority | Status |
|---|-------|--------|----------|--------|
| 1 | [Vibe SDK Packaging](./phase-01-vibe-sdk-packaging.md) | 1w | P1 | pending |
| 2 | [CRO Optimization 200%](./phase-02-cro-optimization-200.md) | 1w | P1 | pending |
| 3 | [Edge Backend Migration](./phase-03-edge-backend-migration.md) | 1w | P2 | pending |

## Dependencies

```
Phase 1 (SDK) ←→ Phase 2 (CRO): Doc lap, chay song song
Phase 3 (Edge) ← Phase 1: SDK can Edge endpoints de demo latency
```

## Research Reports

- [CRO + SDK Packaging](./research/researcher-01-cro-sdk-packaging.md)
- [Edge Backend + SEA Market](./research/researcher-02-edge-backend-sea-market.md)

## KPIs

| Metric | Baseline | Target | Timeline |
|--------|----------|--------|----------|
| Landing CVR | ~1-2% (est.) | 4-6% | 4 weeks |
| API Latency (global) | 150-300ms | < 50ms | 2 weeks |
| SDK scaffold time | manual ~2h | < 5min | 1 week |
| F&B template deployments | 0 | 5 pilot clients | 6 weeks |

## Risk Tong Hop

- Chua co CVR baseline → can PostHog truoc khi A/B test
- Polar.sh chua ro ho tro VND → can verify
- BullMQ tren Workers chua chac tuong thich → giu VPS cho job queue

## Unresolved Questions

1. PostHog da duoc instrument tren agencyos-landing chua?
2. Polar.sh embedded checkout can plan nao?
3. Hyperdrive latency thuc te voi Supabase Singapore?
4. BullMQ Redis protocol qua `cloudflare:sockets` — da test chua?

## Validation Log

### Session 1 — 2026-02-27
**Trigger:** Initial plan creation validation
**Questions asked:** 6

#### Questions & Answers

1. **[Architecture]** Phase 1 (Vibe SDK): Ban muon SDK template dung co che nao de sync updates tu WellNexus goc?
   - Options: Git submodule (Recommended) | Static copy + release | Turborepo package
   - **Answer:** Git submodule (Recommended)
   - **Rationale:** Template link toi WellNexus repo, auto-pull updates. Maintenance thap, dam bao template luon cap nhat voi source.

2. **[Assumptions]** Phase 2 (CRO): agencyos-landing hien co traffic thuc de chay A/B test khong?
   - Options: Co traffic (>1K/thang) | It traffic (<1K/thang) | Chua launch / Khong co data
   - **Answer:** Co traffic (>1K/thang)
   - **Rationale:** Du traffic de A/B test truyen thong. Plan giu nguyen 3 A/B tests voi PostHog + GrowthBook. Can 2-4 tuan cho statistical significance.

3. **[Architecture]** Phase 3 (Edge): BullMQ + VPS Hub co tiep tuc giu lau dai khong?
   - Options: Giu VPS hybrid (Recommended) | Full edge migration | Bo VPS, dung serverless GCP
   - **Answer:** Giu VPS hybrid (Recommended)
   - **Rationale:** Workers xu ly read/stateless, VPS giu BullMQ + long-running jobs. Thuc te va on dinh. Khong can thay doi plan Phase 3.

4. **[Scope]** Pricing mo hinh SDK: Muc gia $199-299/client/thang co phu hop voi thi truong SEA F&B khong?
   - Options: $199-299/mo (Recommended) | $49-99/mo (SME-friendly) | Freemium + Premium
   - **Answer:** $199-299/mo (Recommended)
   - **Rationale:** Premium positioning, margin cao. Phu hop mid-market F&B chains (10+ cua hang). Giu nguyen pricing trong Phase 1.

5. **[Tradeoffs]** Thu tu uu tien trien khai: Bat dau tu phase nao truoc?
   - Options: Phase 2 (CRO) truoc | Phase 1 (SDK) truoc | Phase 1+2 song song (Recommended)
   - **Answer:** Phase 2 (CRO) truoc
   - **Rationale:** Co traffic roi, CRO tao revenue nhanh nhat. SDK packaging co the lam sau khi CRO da co baseline tot.

6. **[Assumptions]** Social proof cho landing page: da co client logos / testimonials thuc chua?
   - Options: Co, du dung | Co it, can bo sung | Chua co
   - **Answer:** Co, du dung
   - **Rationale:** Da co client logos va testimonials co the dung ngay cho logo wall. Khong can fake data — Phase 2 dung real assets.

#### Confirmed Decisions
- **Template sync:** Git submodule — auto-pull updates tu WellNexus
- **A/B testing:** Go ahead — du traffic (>1K/thang) cho statistical significance
- **VPS strategy:** Hybrid lau dai — Workers read, VPS write/jobs
- **Pricing:** $199-299/mo — premium mid-market positioning
- **Execution order:** Phase 2 (CRO) uu tien → Phase 1 (SDK) → Phase 3 (Edge)
- **Social proof:** Real client logos available — dung ngay

#### Action Items
- [ ] Update Phase priority order: P2 CRO → P1, SDK → P1 (start after CRO foundation)
- [ ] Phase 1: Specify git submodule mechanism trong architecture section
- [ ] Phase 2: Confirm real logos available, khong can fake data plan

#### Impact on Phases
- Phase 1: Update architecture section — template dung git submodule thay vi static copy
- Phase 2: Nang uu tien — bat dau truoc Phase 1. Social proof dung real logos (da co)
- Phase 3: Khong doi — VPS hybrid confirmed
