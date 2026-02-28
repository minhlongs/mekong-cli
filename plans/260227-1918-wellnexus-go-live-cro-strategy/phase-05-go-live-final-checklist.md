# Phase 05: Go-Live Final Checklist

## Context
- Parent: [plan.md](./plan.md)
- Depends on: Tất cả phases trước
- Research: [Go-Live Checklist](./research/researcher-02-glassmorphism-cro-golive.md#4-go-live-technical-checklist)
- Project: `/Users/macbookprom1/mekong-cli/apps/well`

## Overview
- **Priority**: P1
- **Status**: ⬜ pending
- **Mô tả**: Final verification + missing pieces trước Go-Live chính thức

## Key Insights
- Nhiều items đã hoàn thành (SEO, Sentry, CSP, i18n, theme)
- Thiếu: structured data, cookie consent, uptime monitoring, performance budget
- Cookie consent BẮT BUỘC vì PostHog tracking (Phase 01)

## Requirements
- Cookie consent banner (simple, glassmorphism style)
- JSON-LD structured data cho Organization + Product
- Lighthouse audit > 90 all categories
- Uptime monitoring setup

## Related Code Files

<!-- Updated: Validation Session 1 - Cookie consent moved to Phase 01 -->
### Sửa (2 files)
1. `index.html` — Thêm JSON-LD structured data
2. `vercel.json` — Performance headers tuning (nếu cần)

## Implementation Steps

1. **JSON-LD Structured Data** (`index.html`):
   <!-- Cookie consent đã chuyển sang Phase 01 -->

   ```html
   <script type="application/ld+json">
   {
     "@context": "https://schema.org",
     "@type": "Organization",
     "name": "WellNexus",
     "url": "https://wellnexus.vn",
     "logo": "https://wellnexus.vn/logo.png"
   }
   </script>
   ```

3. **Conditional Analytics Init** (`main.tsx`):
   - Check `localStorage.getItem('wellnexus-consent')`
   - Consent = 'accepted' → init PostHog + GrowthBook
   - Consent = 'rejected' → skip tracking, basic pageviews only

## Todo List
- [ ] Tạo `cookie-consent.tsx` component
- [ ] Thêm JSON-LD vào `index.html`
- [ ] Conditional PostHog init trong `main.tsx`
- [ ] Lighthouse audit: performance, a11y, SEO, best practices
- [ ] Test consent flow: accept → tracking works, reject → no tracking
- [ ] Setup uptime monitoring (BetterStack/UptimeRobot — manual)

## Pre-Launch Verification

### Đã Hoàn Thành ✅
- [x] Meta tags + OG images
- [x] robots.txt + sitemap.xml
- [x] Sentry error tracking
- [x] CSP + HSTS headers
- [x] i18n vi/en
- [x] Dark/Light theme
- [x] 254/254 tests passing
- [x] 0 TypeScript errors

### Cần Hoàn Thành ⬜
- [ ] PostHog analytics (Phase 01)
- [ ] GrowthBook A/B (Phase 02)
- [ ] Conversion funnel (Phase 03)
- [ ] CRO optimization (Phase 04)
- [ ] Cookie consent (Phase 05)
- [ ] JSON-LD structured data (Phase 05)
- [ ] Lighthouse > 90 (Phase 05)
- [ ] Uptime monitoring (manual setup)

## Success Criteria
- Cookie consent hoạt động đúng (accept/reject)
- JSON-LD valid (test với Google Rich Results)
- Lighthouse: Performance ≥ 90, A11y ≥ 95, SEO ≥ 95, BP ≥ 90
- Tất cả Phase 01-04 verified

## Risk Assessment
- **Cookie consent blocker**: Nếu user reject, PostHog không init — funnel data sẽ incomplete. Đây là trade-off compliance cần chấp nhận.
- **Performance regression**: PostHog + GrowthBook thêm ~60KB — monitor bundle size

## Unresolved Questions
1. PostHog Cloud (US/EU) hay self-hosted? → Recommend US Cloud cho MVP, migrate sau nếu cần
2. GrowthBook Cloud free tier đủ không? → Free = 3 experiments, đủ cho 3 tháng đầu
3. Uptime monitoring tool nào? → BetterStack (free tier, Slack alerts)
4. Domain wellnexus.vn đã point đúng chưa? → Cần verify DNS trước go-live
