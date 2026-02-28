# Phase 03: Conversion Funnel Tracking

## Context
- Parent: [plan.md](./plan.md)
- Depends on: [Phase 01](./phase-01-posthog-integration.md), [Phase 02](./phase-02-growthbook-ab-testing.md)
- Project: `/Users/macbookprom1/mekong-cli/apps/well`

## Overview
- **Priority**: P1
- **Status**: ⬜ pending
- **Mô tả**: Implement custom event tracking cho conversion funnel: Landing → Pricing → Signup → Dashboard → Purchase

## Key Insights
- Funnel hiện tại không track được — chỉ có pageview cơ bản
- Cần track cả micro-conversions (scroll depth, section views, CTA hovers)
- PostHog Funnels tự động build từ custom events

## Requirements
- Track 6 conversion steps (xem research-01)
- Section visibility tracking (IntersectionObserver)
- CTA click tracking với context (button location, text)
- Signup funnel tracking (start → complete)

## Related Code Files

### Sửa (4 files)
1. `src/lib/analytics.ts` — Thêm funnel-specific tracking methods
2. `src/pages/LandingPage.tsx` — Track section views + CTA clicks
3. `src/pages/Signup.tsx` — Track signup funnel steps
4. `src/pages/Dashboard.tsx` — Track dashboard activation

## Implementation Steps

1. Thêm funnel tracking API vào `src/lib/analytics.ts`:
   ```typescript
   export const funnel = {
     landingView: () => capture('funnel_landing_view'),
     pricingSectionViewed: () => capture('funnel_pricing_viewed'),
     ctaClicked: (location: string, text: string) =>
       capture('funnel_cta_clicked', { location, text }),
     signupStarted: (source: string) =>
       capture('funnel_signup_started', { source }),
     signupCompleted: (method: string) =>
       capture('funnel_signup_completed', { method }),
     firstPurchase: (product: string, amount: number) =>
       capture('funnel_first_purchase', { product, amount }),
   };
   ```

2. Update `LandingPage.tsx`:
   - IntersectionObserver cho pricing section → `pricingSectionViewed()`
   - onClick handlers cho CTA buttons → `ctaClicked(location, text)`
   - Track scroll depth (25%, 50%, 75%, 100%)

3. Update `Signup.tsx`:
   - `signupStarted(source)` khi form render
   - `signupCompleted(method)` sau successful signup

4. Update `Dashboard.tsx`:
   - Track first visit (activation event)

## Todo List
- [ ] Thêm `funnel` namespace vào `analytics.ts`
- [ ] Implement IntersectionObserver tracking trong `LandingPage.tsx`
- [ ] Track CTA clicks với context
- [ ] Track signup funnel trong `Signup.tsx`
- [ ] Track dashboard activation
- [ ] Setup PostHog Funnel dashboard (manual trong UI)
- [ ] Verify: events flow đúng thứ tự trong PostHog

## Success Criteria
- PostHog Funnels hiển thị 6-step conversion path
- Drop-off % visible tại mỗi step
- Scroll depth data available
- CTA click heatmap data populated

## Risk Assessment
- **Event volume**: Autocapture + custom events có thể cao — monitor PostHog quota
- **Performance**: IntersectionObserver = lightweight, không ảnh hưởng
- **Data quality**: Ensure event names consistent — dùng constants, không hardcode strings
