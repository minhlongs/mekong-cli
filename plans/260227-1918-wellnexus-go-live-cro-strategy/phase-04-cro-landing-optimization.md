# Phase 04: CRO Landing Page Optimization

## Context
- Parent: [plan.md](./plan.md)
- Depends on: [Phase 03](./phase-03-conversion-funnel-tracking.md) — cần data trước khi optimize
- Research: [Glassmorphism CRO](./research/researcher-02-glassmorphism-cro-golive.md)
- Project: `/Users/macbookprom1/mekong-cli/apps/well`

## Overview
- **Priority**: P2
- **Status**: ⬜ pending
- **Mô tả**: Optimize landing page cho conversion dựa trên Glassmorphism 2.0 patterns + GrowthBook experiments

## Key Insights
- Landing page đã có Aura Elite design — cần tinh chỉnh cho conversion, không redesign
- Hero section, pricing cards, CTAs = 3 điểm impact cao nhất
- Framer Motion đã có trong stack — leverage cho micro-interactions
- GrowthBook feature flags cho A/B test các variants

## Requirements
- Hero section: Clear value prop + single CTA + social proof
- Pricing section: Highlighted recommended tier + accent glass
- CTAs: Gradient accent + hover glow animation
- A/B test ready: Wrap key elements trong GrowthBook feature flags

## Related Code Files

### Sửa (4 files)
1. `src/components/landing/landing-hero-section.tsx` — CTA optimization + social proof
2. `src/components/landing/landing-roadmap-section.tsx` — Trust signals (có thể rename thành pricing/features)
3. `src/styles/design-system.css` — Thêm CRO-specific utility classes
4. `src/pages/LandingPage.tsx` — Section ordering + GrowthBook flag wrappers

## Implementation Steps

1. **Hero CTA Optimization** (`landing-hero-section.tsx`):
   - CTA text A/B test via GrowthBook: `useFeatureValue('hero_cta_text', 'Bắt Đầu Ngay')`
   - Thêm social proof row dưới CTA (customer count, rating)
   - Hover animation: `whileHover={{ scale: 1.05 }}` + glow effect

2. **Pricing Section Enhancement**:
   - Recommended tier: `glass-accent` class + "Phổ Biến Nhất" badge
   - Annual/Monthly toggle A/B test
   - Feature comparison collapse

3. **Design System CRO Classes** (`design-system.css`):
   ```css
   .cta-glow { box-shadow: 0 0 20px rgba(102,126,234,0.4); }
   .cta-glow:hover { box-shadow: 0 0 30px rgba(102,126,234,0.6); }
   .badge-recommended { /* accent gradient badge */ }
   ```

4. **GrowthBook Wrappers** (`LandingPage.tsx`):
   - Wrap hero CTA trong `useFeatureValue` cho text variant
   - Wrap pricing section trong feature flag cho layout variant

## Todo List
- [ ] Optimize hero CTA với animation + social proof
- [ ] Highlight recommended pricing tier
- [ ] Thêm CRO utility classes vào design system
- [ ] Wrap A/B test elements với GrowthBook flags
- [ ] Test: cả dark và light mode
- [ ] Verify: i18n keys sync (vi + en)

## Success Criteria
- Hero CTA click rate tăng (baseline từ Phase 03 data)
- Pricing section engagement tăng
- GrowthBook experiments running
- No visual regression cả 2 themes
- i18n keys sync 100%

## Risk Assessment
- **i18n break**: CRITICAL — phải grep t() calls và verify keys tồn tại (Rule 1 trong CLAUDE.md)
- **Design regression**: Test cả dark + light mode
- **A/B test pollution**: Ensure proper experiment exposure tracking
