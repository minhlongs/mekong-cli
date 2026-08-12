# Phase 13 — Phase 01.13: Performance Optimization

**Date:** 260811 · **Status:** pending

## Task
Optimize images (next/image, AVIF/WebP, blur placeholders). Self-host fonts with preload. Configure caching headers. Add Vercel Analytics / GA4. Implement resource hints (preconnect, dns-prefetch).

## Files

- next.config.js
- src/components/ui/image.tsx
- src/lib/analytics.ts
- public/fonts/

## Acceptance criteria

Lighthouse Performance > 90. CLS < 0.1. FID < 100ms. Images served in next-gen formats. Fonts load with font-display: swap. No layout shift from images/fonts.
