# Phase 02: CRO Optimization — Target 200% CVR Lift

## Context Links

- Research: [CRO + SDK Packaging](./research/researcher-01-cro-sdk-packaging.md)
- AgencyOS Landing: `apps/agencyos-landing/`
- WellNexus (template showcase): `apps/well/`
- Aura Elite design system (Glassmorphism)

## Overview

- **Priority:** P1
- **Status:** pending
- **Effort:** 1 week
- **Description:** Tang conversion rate 200% cho agencyos-landing bang A/B testing co he thong, Glassmorphism 2.0, micro-interactions, va social proof. Su dung PostHog + GrowthBook + Vercel Edge Middleware.

## Key Insights

- CTA copy optimization alone: +104% (Going.com case study)
- Social proof restructuring: +40% CVR (logos above fold + real metrics)
- Glassmorphism pricing cards: +20% CVR (visual hierarchy clarity)
- Exit-intent recovery: +5-10% cua total exits
- Composite formula: 40% + 30% + 25% + 20% + 15% + 20% = ~150-200% potential
- PostHog la open-source, self-hostable, co A/B + session replay + feature flags

## Requirements

### Functional
- [ ] PostHog integration (event tracking, session replay, A/B)
- [ ] GrowthBook feature flags cho A/B test variants
- [ ] 3 A/B tests cu the (CTA, social proof, pricing)
- [ ] Glassmorphism 2.0 cho pricing cards + hero
- [ ] Micro-interactions (Framer Motion, GSAP ScrollTrigger)
- [ ] Exit-intent popup (last-chance offer)
- [ ] Mobile sticky CTA bar
- [ ] Social proof: logo wall above fold, real-time activity feed

### Non-Functional
- [ ] LCP < 2.5s (khong sacrifice performance cho animations)
- [ ] A/B tests statistically significant (>95% confidence)
- [ ] Zero layout shift tu animations (CLS < 0.1)
- [ ] Accessible: animations respect `prefers-reduced-motion`

## Architecture

### A/B Testing Stack

```
User Request → Vercel Edge Middleware
                ├── Read PostHog cookie / assign variant
                ├── Set feature flags via GrowthBook SDK
                └── Serve variant A or B

PostHog Cloud (hoac self-host)
  ├── Event tracking (page_view, cta_click, checkout_start, checkout_complete)
  ├── Session replay (debug UX issues)
  ├── Funnels (Landing → Pricing → Checkout → Success)
  └── A/B test results dashboard

GrowthBook
  ├── Feature flags (server-side via Edge Middleware)
  ├── Experiment config (traffic split, metrics, goals)
  └── Stats engine (Bayesian)
```

### 3 A/B Tests

#### Test 1: CTA Copy + Placement
```
Control (A): "Get Started" button, 1x above fold
Variant (B): "Launch Your Agency in 5 Minutes" button, 3x placement
             (above fold + 50% scroll + bottom)
Metric: click-through-rate → checkout_start
Expected lift: +30%
```

#### Test 2: Social Proof Above Fold
```
Control (A): Features section first, logos at bottom
Variant (B): Logo wall + "500+ agencies trust us" above fold,
             real-time activity feed ("X just deployed from HCMC")
Metric: scroll_depth + time_on_page + checkout_start
Expected lift: +40%
```

#### Test 3: Glassmorphism Pricing Cards
```
Control (A): Flat design pricing cards
Variant (B): Glassmorphism cards + annual toggle default +
             "Most Popular" badge on middle tier +
             FAQ section below pricing
Metric: pricing_page_view → checkout_start → checkout_complete
Expected lift: +20%
```

### Micro-Interactions Map

```
Hero Section:
  - Framer Motion: fadeInUp on load (stagger children)
  - GSAP: parallax background gradient shift on scroll

CTA Buttons:
  - Framer Motion: whileHover={{ scale: 1.05 }} + spring transition
  - Lottie: success checkmark after form submit

Pricing Cards:
  - Framer Motion: whileHover={{ y: -8 }} on card hover
  - useInView: counter animation for stats ("500+ agencies")

Scroll Sections:
  - GSAP ScrollTrigger: fade + slide sections on scroll
  - Intersection Observer: lazy load heavy components

Mobile:
  - Sticky bottom CTA bar (fixed position, z-50)
  - Swipeable testimonial carousel
```

## Related Code Files

### Files to Modify
- `apps/agencyos-landing/app/layout.tsx` — Add PostHog provider
- `apps/agencyos-landing/app/page.tsx` — Hero + CTA restructure
- `apps/agencyos-landing/middleware.ts` — Edge A/B routing
- `apps/agencyos-landing/components/` — Pricing, Hero, Social proof components
- `apps/agencyos-landing/next.config.ts` — PostHog rewrites

### Files to Create
- `apps/agencyos-landing/lib/posthog.ts` — PostHog client init
- `apps/agencyos-landing/lib/growthbook.ts` — GrowthBook SDK init
- `apps/agencyos-landing/components/social-proof-feed.tsx` — Real-time activity
- `apps/agencyos-landing/components/exit-intent-popup.tsx` — Exit-intent modal
- `apps/agencyos-landing/components/sticky-mobile-cta.tsx` — Mobile CTA bar
- `apps/agencyos-landing/components/glass-pricing-card.tsx` — Glassmorphism card
- `apps/agencyos-landing/components/animated-counter.tsx` — Number counter
- `apps/agencyos-landing/styles/glassmorphism.css` — Glass utility classes

## Implementation Steps

### Step 1: Analytics Foundation (Day 1)
1. Install PostHog SDK: `pnpm add posthog-js posthog-node`
2. Tao `lib/posthog.ts` — client-side init voi project API key
3. Add PostHogProvider vao `app/layout.tsx`
4. Track core events: `page_view`, `cta_click`, `pricing_view`, `checkout_start`
5. Setup funnel: Landing → Pricing → Checkout → Success
6. Cho 48h thu thap baseline data

### Step 2: A/B Testing Infrastructure (Day 1-2)
1. Install GrowthBook SDK: `pnpm add @growthbook/growthbook-react`
2. Tao `lib/growthbook.ts` — init voi feature flags
3. Config Vercel Edge Middleware cho traffic splitting
4. Setup 3 experiments trong GrowthBook dashboard
5. Wire PostHog events lam metrics cho experiments

### Step 3: Glassmorphism 2.0 (Day 2-3)
1. Tao `styles/glassmorphism.css` voi utility classes
2. Redesign pricing cards: frosted glass + gradient border
3. Add "Most Popular" badge voi glow effect
4. Annual/Monthly toggle (annual default)
5. FAQ accordion below pricing
6. Test contrast ratio (WCAG AA compliance)

### Step 4: Micro-Interactions (Day 3-4)
1. Install: `pnpm add framer-motion gsap @gsap/react lottie-react`
2. Hero: fadeInUp stagger + parallax gradient
3. CTA buttons: whileHover spring + tactile feedback
4. Pricing cards: hover lift + useInView counter
5. Scroll sections: GSAP ScrollTrigger reveal
6. Respect `prefers-reduced-motion` — disable all animations

### Step 5: Social Proof + CTA (Day 4-5)
1. Logo wall component: above fold, grayscale → color on hover
2. Real-time activity feed: "X vua dang ky tu HCMC" (co the fake initial data, sau do real)
3. CTA placement: 3 vi tri (above fold, 50% scroll, bottom)
4. Benefit-led copy: "Launch Your Agency in 5 Minutes"
5. Exit-intent popup: detect mouse leave viewport, show modal voi offer
6. Mobile sticky CTA bar: fixed bottom, z-50

### Step 6: Performance Guard (Day 5)
1. Lighthouse audit: LCP < 2.5s, CLS < 0.1
2. Lazy load GSAP + Lottie (dynamic import)
3. Image optimization: WebP + Vercel Image CDN
4. Font subsetting: chi load glyphs can thiet
5. Bundle analysis: ensure animations < 50KB gzipped

### Step 7: Launch + Monitor (Day 5-7)
1. Deploy A/B variants
2. Monitor PostHog funnels daily
3. Cho 1-2 tuan thu thap du data
4. Analyze ket qua: statistical significance > 95%
5. Roll out winning variants

## Todo List

- [ ] Install + config PostHog
- [ ] Install + config GrowthBook
- [ ] Setup Vercel Edge Middleware A/B routing
- [ ] Track baseline CVR (48h)
- [ ] Design Glassmorphism pricing cards
- [ ] Implement glass CSS utilities
- [ ] Add Framer Motion micro-interactions
- [ ] Add GSAP ScrollTrigger
- [ ] Tao social proof logo wall
- [ ] Tao real-time activity feed
- [ ] Tao exit-intent popup
- [ ] Tao mobile sticky CTA
- [ ] Optimize CTA copy (benefit-led)
- [ ] Performance audit (LCP < 2.5s)
- [ ] Launch 3 A/B tests
- [ ] Monitor 1-2 tuan
- [ ] Roll out winning variants

## Success Criteria

- PostHog tracking 100% page views + CTA clicks
- 3 A/B tests running dong thoi
- CVR tang it nhat 100% sau 2 tuan (tren duong toi 200%)
- LCP < 2.5s (khong thoai lui performance)
- CLS < 0.1 (khong layout shift tu animations)
- Exit-intent recovery > 5% cua exits
- Mobile CTA click rate > desktop (sticky bar effective)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Animations lam cham page | LCP > 2.5s | Lazy load, code split, budget 50KB |
| A/B test khong du traffic | Khong dat statistical significance | Chay lau hon (3-4 tuan) |
| Glassmorphism contrast issues | Accessibility fail | Test contrast ratio, fallback solid bg |
| PostHog self-host cost | Unexpected infra cost | Dung PostHog Cloud free tier truoc |
| GrowthBook + PostHog conflict | Event duplication | Dung PostHog lam sole event source |

## Security Considerations

- PostHog API key la public (client-side) — khong chua secrets
- GrowthBook SDK key cung public — feature flags khong chua sensitive data
- Exit-intent popup KHONG collect PII — chi show offer
- Real-time activity feed: dung anonymized data, khong show real names
<!-- Updated: Validation Session 1 - Social proof dung real client logos, du traffic cho A/B (>1K/thang) -->
- Vercel Edge Middleware: khong log user data

## Next Steps

- Sau khi co winning variants → hardcode thay A/B
- Tao CRO playbook cho SDK templates (moi client duoc CRO best practices)
- Setup automated weekly CRO report (PostHog → Slack/Telegram)
- Phase 2.5: Video testimonials + case study pages

## Unresolved Questions

1. agencyos-landing hien tai co PostHog chua? (can check `package.json`)
2. Baseline CVR la bao nhieu? (can analytics access)
3. ~~Logo wall: da co brand logos chua hay can thu thap?~~ → CONFIRMED: Co du logos (Validation Session 1)
4. GrowthBook free tier gioi han bao nhieu experiments?
5. Framer Motion da installed trong agencyos-landing chua?
6. Real-time activity feed — data source tu dau? (Supabase realtime? Fake initial?)
