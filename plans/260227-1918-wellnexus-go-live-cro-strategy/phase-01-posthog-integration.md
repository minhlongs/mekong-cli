# Phase 01: PostHog Integration

## Context
- Parent: [plan.md](./plan.md)
- Research: [PostHog + GrowthBook CRO](./research/researcher-01-posthog-growthbook-cro.md)
- Project: `/Users/macbookprom1/mekong-cli/apps/well`

## Overview
- **Priority**: P0 — Nền tảng cho toàn bộ CRO strategy
- **Status**: ⬜ pending
- **Mô tả**: Tích hợp PostHog SDK vào WellNexus, thay thế Vercel Analytics cơ bản

## Key Insights
- Hiện tại chỉ có `window.va` (Vercel Analytics) — không có funnel, heatmap, session replay
- `src/lib/analytics.ts` là analytics module hiện tại — cần mở rộng, KHÔNG thay thế
- Sentry đã có — PostHog bổ sung behavioral analytics, không overlap

## Requirements
- PostHog provider wrap app ở root
- Autocapture enabled (clicks, pageviews)
- Session replay enabled (50% sampling production)
- Custom events API tương thích interface hiện tại
- Cookie consent trước khi init tracking
- Env vars: `VITE_POSTHOG_KEY`, `VITE_POSTHOG_HOST`

## Related Code Files

<!-- Updated: Validation Session 1 - Cookie consent moved from Phase 05 to Phase 01 -->
### Sửa (5 files)
1. `src/lib/analytics.ts` — Mở rộng thêm PostHog tracking methods
2. `src/main.tsx` — Thêm PostHogProvider wrap + cookie consent mount
3. `.env.example` — Thêm PostHog env vars
4. `package.json` — Thêm `posthog-js` dependency
5. `src/components/ui/cookie-consent.tsx` — TẠO MỚI: Cookie consent banner (glassmorphism)

## Implementation Steps

1. Install PostHog SDK
   ```bash
   cd apps/well && pnpm add posthog-js
   ```

2. Thêm env vars vào `.env.example`
   ```
   VITE_POSTHOG_KEY=phc_xxx
   VITE_POSTHOG_HOST=https://us.i.posthog.com
   ```

3. Mở rộng `src/lib/analytics.ts`:
   - Import `posthog-js`
   - Init PostHog trong `init()` method mới
   - Giữ nguyên `window.va` calls (backward compatible)
   - Thêm: `identify()`, `capture()`, `group()`, `reset()`
   - Thêm consent check trước mọi tracking call

4. Tạo `src/components/ui/cookie-consent.tsx`:
   - Glassmorphism styled, fixed bottom
   - 2 buttons: "Chấp Nhận" (accent gradient) + "Từ Chối" (ghost)
   - Lưu preference vào localStorage key `wellnexus-consent`
   - Export `hasConsent()` helper cho analytics init check
   - Respect `prefers-reduced-motion`

5. Update `src/main.tsx`:
   - Import PostHogProvider từ `posthog-js/react`
   - Import CookieConsent component
   - Wrap app: `<PostHogProvider client={posthog}>`
   - Init PostHog chỉ khi `hasConsent() === true`

## Todo List
- [ ] Install `posthog-js`
- [ ] Update `.env.example` với PostHog vars
- [ ] Mở rộng `src/lib/analytics.ts` với PostHog methods
- [ ] Wrap PostHogProvider trong `src/main.tsx`
- [ ] Test: verify events gửi đến PostHog dashboard
- [ ] Verify: không break existing Vercel Analytics

## Success Criteria
- PostHog nhận được pageview events từ WellNexus
- Session replay hoạt động (xem lại user session)
- Autocapture bắt click events
- Existing analytics (`window.va`) vẫn hoạt động
- Build passes, 0 TS errors

## Risk Assessment
- **PostHog bundle size**: ~40KB gzipped — acceptable cho SaaS
- **Performance impact**: Async loading, không block render
- **Privacy**: Cần cookie consent trước init — implement đơn giản banner trước

## Security
- API key là public (client-side) — PostHog design cho phép
- Không track PII tự động (tên, email) trừ khi explicit `identify()`
- Session replay có thể mask sensitive inputs
