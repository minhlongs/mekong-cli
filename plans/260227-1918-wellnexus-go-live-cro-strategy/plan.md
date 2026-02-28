---
title: "WellNexus Go-Live & CRO Strategy"
description: "Kế hoạch Go-Live và CRO cho WellNexus — PostHog/GrowthBook analytics + Glassmorphism 2.0 conversion optimization"
status: pending
priority: P1
effort: 8h
branch: master
tags: [cro, analytics, posthog, growthbook, go-live, wellnexus]
created: 2026-02-27
---

# Chiến Dịch Bình Pháp: WellNexus Go-Live & CRO Strategy

> 始計 — Tính toán trước khi xuất quân. Data trước, optimization sau.

## Tình Hình Hiện Tại

| Hạng mục | Trạng thái |
|----------|-----------|
| Analytics | Vercel Analytics cơ bản (`window.va`) — thiếu funnel tracking |
| A/B Testing | Chưa có |
| Error tracking | Sentry ✅ |
| SEO cơ bản | Meta tags, sitemap, robots.txt ✅ |
| Design System | Aura Elite (Glassmorphism 2.0) ✅ |
| i18n | Vi/En ✅ |
| Theme | Dark/Light ✅ |

## Chiến Lược: Data-First CRO

```
Phase 1 → Đặt nền tảng đo lường (PostHog)
Phase 2 → Kích hoạt thí nghiệm (GrowthBook)
Phase 3 → Track conversion funnel
Phase 4 → CRO optimization dựa trên data
Phase 5 → Go-Live checklist final
```

## Tổng Quan Phases

| Phase | Tên | Files | Effort | Status |
|-------|-----|-------|--------|--------|
| 01 | [PostHog Integration](./phase-01-posthog-integration.md) | 4 | 2h | ⬜ pending |
| 02 | [GrowthBook A/B Testing](./phase-02-growthbook-ab-testing.md) | 3 | 1.5h | ⬜ pending |
| 03 | [Conversion Funnel Tracking](./phase-03-conversion-funnel-tracking.md) | 4 | 1.5h | ⬜ pending |
| 04 | [CRO Landing Optimization](./phase-04-cro-landing-optimization.md) | 4 | 2h | ⬜ pending |
| 05 | [Go-Live Final Checklist](./phase-05-go-live-final-checklist.md) | 3 | 1h | ⬜ pending |

## Dependencies

```
Phase 1 (PostHog) ──→ Phase 2 (GrowthBook) ──→ Phase 3 (Funnel)
                                                      │
Phase 4 (CRO) ◄──────────────────────────────────────┘
                                                      │
Phase 5 (Go-Live) ◄──────────────────────────────────┘
```

## Ràng Buộc

- Mỗi mission sửa **< 5 file**
- Project path: `/Users/macbookprom1/mekong-cli/apps/well`
- Giữ nguyên Aura Elite design system
- Không breaking changes cho user flow hiện tại

## Research

- [PostHog + GrowthBook CRO](./research/researcher-01-posthog-growthbook-cro.md)
- [Glassmorphism 2.0 + Go-Live](./research/researcher-02-glassmorphism-cro-golive.md)

## Validation Log

### Session 1 — 2026-02-27
**Trigger:** Initial plan creation validation
**Questions asked:** 4

#### Questions & Answers

1. **[Architecture]** PostHog hosting: US Cloud, EU Cloud, hay Self-hosted? Ảnh hưởng data residency và Nghị định 13/2023 về BVDL cá nhân.
   - Options: US Cloud (Recommended) | EU Cloud | Self-hosted
   - **Answer:** US Cloud
   - **Rationale:** Nhanh nhất setup, free tier 1M events/tháng. Đủ cho MVP. Migrate EU/self-hosted sau nếu compliance yêu cầu.

2. **[Scope]** Cookie consent nên implement ở phase nào? Phase 05 (cuối) hay Phase 01 (cùng PostHog)?
   - Options: Phase 01 - cùng PostHog (Recommended) | Phase 05 - cuối cùng
   - **Answer:** Phase 01 - cùng PostHog
   - **Rationale:** PostHog cần consent trước khi init. Implement ngay Phase 01 đảm bảo compliance từ đầu. Phase 05 giảm scope.

3. **[Scope]** GrowthBook có cần thiết cho MVP go-live không? Hay chỉ cần PostHog trước, thêm GrowthBook sau khi có data?
   - Options: Cả PostHog + GrowthBook (Recommended) | Chỉ PostHog trước | Chỉ PostHog + Funnel
   - **Answer:** Cả PostHog + GrowthBook
   - **Rationale:** Full stack analytics + A/B testing từ đầu. 8h effort như plan gốc. Không cắt scope.

4. **[Tradeoffs]** Vercel Analytics (window.va) hiện tại nên giữ hay thay thế hoàn toàn bằng PostHog?
   - Options: Giữ cả hai (Recommended) | Thay thế hoàn toàn
   - **Answer:** Giữ cả hai
   - **Rationale:** PostHog cho deep analytics, Vercel Analytics cho overview dashboard nhanh. Không conflict, không mất data.

#### Confirmed Decisions
- PostHog hosting: **US Cloud** — fast setup, free tier đủ MVP
- Cookie consent: **Phase 01** — compliance from day one
- GrowthBook scope: **Full implementation** — 5 phases giữ nguyên
- Vercel Analytics: **Giữ song song** — backward compatible

#### Action Items
- [ ] Di chuyển cookie consent từ Phase 05 sang Phase 01
- [ ] Phase 01 tăng từ 4 files → 5 files (thêm cookie-consent.tsx)
- [ ] Phase 05 giảm scope (bỏ cookie consent, giữ JSON-LD + Lighthouse)

#### Impact on Phases
- Phase 01: Thêm cookie-consent.tsx component, tăng effort +30min, files = 5
- Phase 05: Bỏ cookie-consent.tsx (đã chuyển P01), giảm files = 2, giảm effort
