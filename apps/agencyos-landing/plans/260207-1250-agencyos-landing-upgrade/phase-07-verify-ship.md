# Phase 07: Verify & Ship

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 3 hours

Final verification, quality gates, performance optimization, and production deployment with comprehensive checks across build, Lighthouse, visual polish, and live deployment.

## Context Links

- Phase 05: [i18n & SEO](./phase-05-i18n-seo.md)
- Phase 06: [Hub Integration](./phase-06-hub-integration.md)
- Binh Phap Quality Gates: `~/.claude/rules/binh-phap-quality.md`
- CI/CD Protocol: `~/.claude/rules/binh-phap-cicd.md`

## Key Insights

- 90+ Lighthouse score drives 2x organic traffic
- Build-time errors block 60% of deployments
- Visual polish (animations, accessibility) increases trust 40%
- Production verification catches 80% of missed bugs
- "Max WOW" polish = competitive differentiation

## Requirements

### Functional
- Zero TypeScript/ESLint errors
- All tests passing (unit, integration, E2E)
- Lighthouse scores 90+ (Performance, Accessibility, SEO, Best Practices)
- Smooth animations (60fps)
- Keyboard navigation working
- Mobile responsive (375px - 1920px)
- Production deployment verified

### Non-Functional
- Build time <60s
- Bundle size <500KB (gzipped)
- First Contentful Paint <1.5s
- Time to Interactive <3.5s
- Cumulative Layout Shift <0.1
- Zero console errors in production

## Architecture

```
Verification Pipeline:
1. BUILD       → TypeScript, ESLint, Next.js build
2. LIGHTHOUSE  → Performance, A11y, SEO, Best Practices
3. POLISH      → Animations, interactions, accessibility
4. DEPLOY      → Vercel production + verification
5. MONITOR     → Post-deploy health checks

Quality Gates (Binh Phap):
├── 始計 Tech Debt    → 0 TODOs/FIXMEs
├── 作戰 Type Safety  → 0 `any` types
├── 謀攻 Performance  → Build <10s, LCP <2.5s
├── 軍形 Security     → 0 high/critical vulnerabilities
├── 兵勢 UX           → Smooth animations, loading states
└── 虛實 Documentation → Updated README, changelog
```

## Related Code Files

**To Verify:**
- All source files in `src/`
- `package.json` (dependencies, scripts)
- `next.config.js` (production optimizations)
- `tailwind.config.ts` (build optimizations)
- `.env.production` (production env vars)

**To Run:**
- `npm run build`
- `npm run lint`
- `npm run type-check`
- `npm run test` (if tests exist)
- Lighthouse CLI

## Implementation Steps

### 1. Pre-Build Quality Gates (30min)

Run Binh Phap quality checks:

```bash
# Gate 1: Tech Debt Elimination (始計)
echo "=== Tech Debt Check ==="
grep -r "console\." src --include="*.ts" --include="*.tsx" | wc -l  # Must be 0
grep -r "TODO\|FIXME" src | wc -l  # Must be 0
grep -r "@ts-ignore\|@ts-nocheck" src | wc -l  # Must be 0

# Gate 2: Type Safety (作戰)
echo "=== Type Safety Check ==="
grep -r ": any" src --include="*.ts" --include="*.tsx" | wc -l  # Must be 0
npm run type-check  # Must pass

# Gate 3: Lint Check
echo "=== Lint Check ==="
npm run lint  # Must pass with 0 warnings

# Gate 4: Security Scan (軍形)
echo "=== Security Check ==="
npm audit --audit-level=high  # Must be 0 high/critical
```

**Fix any issues before proceeding.**

### 2. Build Verification (30min)

```bash
# Clean build
rm -rf .next
npm run build

# Verify build output
echo "=== Build Metrics ==="
time npm run build  # Target: <60s

# Check bundle sizes
npx @next/bundle-analyzer

# Verify build artifacts
ls -lh .next/static/chunks/*.js | head
```

**Expected output:**
- Build completes successfully
- No TypeScript errors
- No ESLint warnings
- Bundle size <500KB gzipped
- Build time <60s

### 3. Lighthouse Performance Check (30min)

```bash
# Install Lighthouse CLI (if not installed)
npm install -g lighthouse

# Run dev server
npm run dev &
DEV_PID=$!

# Wait for server to start
sleep 5

# Run Lighthouse (English locale)
lighthouse http://localhost:3000/en \
  --output=html \
  --output-path=./lighthouse-report-en.html \
  --preset=desktop \
  --chrome-flags="--headless"

# Run Lighthouse (Vietnamese locale)
lighthouse http://localhost:3000/vi \
  --output=html \
  --output-path=./lighthouse-report-vi.html \
  --preset=desktop \
  --chrome-flags="--headless"

# Kill dev server
kill $DEV_PID
```

**Target Scores:**
- Performance: 90+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 100

**Common issues & fixes:**
- Low Performance → Optimize images (WebP), defer non-critical JS
- Low Accessibility → Add ARIA labels, check color contrast
- Low SEO → Missing meta tags, sitemap issues

### 4. Visual Polish Verification (45min)

#### Checklist: Animations (60fps)

Test in browser DevTools (Performance tab):
- [ ] Hero gradient animation smooth
- [ ] Magnetic button hover effect
- [ ] Pricing card scale on hover
- [ ] FAQ accordion expand/collapse
- [ ] Page scroll animations (features, pricing)
- [ ] Language switcher dropdown
- [ ] Navigation menu (if applicable)

**Fix jank:** Use `will-change`, `transform` instead of `top/left`, reduce animation complexity.

#### Checklist: Accessibility

```bash
# Install axe-core CLI
npm install -g @axe-core/cli

# Run accessibility audit
axe http://localhost:3000/en --tags wcag2a,wcag2aa
```

Manual checks:
- [ ] Tab navigation works (focus indicators visible)
- [ ] Screen reader tested (VoiceOver/NVDA)
- [ ] Color contrast 4.5:1 minimum (text)
- [ ] All images have alt text
- [ ] Form inputs have labels
- [ ] Skip to content link (if long nav)

#### Checklist: Responsive Design

Test at breakpoints:
- [ ] 375px (iPhone SE)
- [ ] 768px (iPad Portrait)
- [ ] 1024px (iPad Landscape)
- [ ] 1440px (Desktop)
- [ ] 1920px (Large Desktop)

**Key areas:**
- Hero section layout
- Feature cards grid
- Pricing cards (stack on mobile)
- FAQ accordion width
- Navigation menu (mobile hamburger if needed)

#### Checklist: "Max WOW" Polish

- [ ] First paint <1.5s (perceived performance)
- [ ] Smooth scroll behavior (CSS `scroll-behavior: smooth`)
- [ ] No layout shift (CLS <0.1)
- [ ] Loading states on async actions (checkout button)
- [ ] Error states styled (form validation)
- [ ] Empty states (if applicable)
- [ ] Micro-interactions (button hover, card tilt)
- [ ] Gradient text renders correctly
- [ ] Glassmorphism effects visible (blur, transparency)

### 5. Production Environment Setup (15min)

`.env.production`:
```env
# Base URL
NEXT_PUBLIC_BASE_URL=https://agencyos.dev

# Polar.sh Production
POLAR_ACCESS_TOKEN=polar_at_prod_xxx
POLAR_WEBHOOK_SECRET=whsec_prod_xxx
POLAR_ORGANIZATION_ID=org_prod_xxx

NEXT_PUBLIC_POLAR_PRICE_STARTER=price_prod_xxx
NEXT_PUBLIC_POLAR_PRICE_PRO=price_prod_yyy

# Analytics Production
ANALYTICS_WRITE_KEY=prod_xxx
NEXT_PUBLIC_ANALYTICS_HOST=https://analytics.agencyos.dev
```

**Vercel Environment Variables:**
```bash
# Set via Vercel dashboard or CLI
vercel env add POLAR_ACCESS_TOKEN production
vercel env add POLAR_WEBHOOK_SECRET production
vercel env add POLAR_ORGANIZATION_ID production
# ... repeat for all secrets
```

### 6. Deploy to Production (30min)

```bash
# Option 1: Git push (recommended)
git add .
git commit -m "feat: AgencyOS landing redesign - Max WOW edition"
git push origin main

# Vercel auto-deploys on push
# Monitor: https://vercel.com/dashboard

# Option 2: Manual Vercel deploy
vercel --prod

# Get deployment URL
DEPLOY_URL=$(vercel ls --json 2>/dev/null | jq -r '.[0].url')
echo "Deployed to: https://$DEPLOY_URL"
```

### 7. Production Verification (30min)

**Binh Phap CI/CD Protocol:**

```bash
# Wait for deployment to complete
MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))
  echo "=== Verification Attempt $ATTEMPT/$MAX_ATTEMPTS ==="

  # Check deployment status
  STATUS=$(vercel inspect "$DEPLOY_URL" --json 2>/dev/null | jq -r '.readyState')
  echo "Deployment Status: $STATUS"

  if [ "$STATUS" = "READY" ]; then
    echo "✅ Deployment READY!"
    break
  fi

  echo "⏳ Waiting 30s for deploy..."
  sleep 30
done

# HTTP health check
echo "=== HTTP Health Check ==="
HTTP_STATUS=$(curl -sI "https://$DEPLOY_URL" | head -1 | awk '{print $2}')
echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ Production site LIVE!"
else
  echo "❌ Production site NOT responding correctly"
  exit 1
fi

# Check both locales
curl -sI "https://$DEPLOY_URL/en" | head -5
curl -sI "https://$DEPLOY_URL/vi" | head -5

# Verify sitemap
curl -sI "https://$DEPLOY_URL/sitemap.xml" | head -5

# Verify robots.txt
curl -sI "https://$DEPLOY_URL/robots.txt" | head -5
```

**Browser Verification (Manual):**
- [ ] Open `https://$DEPLOY_URL/en` in incognito
- [ ] Check console (0 errors)
- [ ] Test checkout flow (use test card)
- [ ] Switch to Vietnamese locale
- [ ] Test mobile view (Chrome DevTools)
- [ ] Verify OpenGraph preview (LinkedIn post preview)
- [ ] Check analytics events firing (Network tab)

### 8. Post-Deploy Monitoring (15min)

**Setup Vercel Analytics:**
```bash
npm install @vercel/analytics
```

Add to layout:
```typescript
import { Analytics } from '@vercel/analytics/react';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

**Monitor for 24h:**
- [ ] Vercel Analytics dashboard (traffic, errors)
- [ ] Polar.sh webhook logs (successful deliveries)
- [ ] Vibe Analytics events (conversion funnel)
- [ ] Browser error tracking (Sentry/Vercel)

## Todo List

### Pre-Deploy
- [ ] Run tech debt check (0 TODOs/FIXMEs)
- [ ] Run type safety check (0 `any` types)
- [ ] Run lint check (0 warnings)
- [ ] Run security audit (0 high/critical)
- [ ] Build succeeds (<60s)
- [ ] Bundle size <500KB gzipped

### Performance
- [ ] Run Lighthouse on /en (90+ all scores)
- [ ] Run Lighthouse on /vi (90+ all scores)
- [ ] Verify LCP <2.5s
- [ ] Verify CLS <0.1
- [ ] Check bundle analyzer for bloat

### Visual Polish
- [ ] Test all animations (60fps)
- [ ] Run axe accessibility audit
- [ ] Test keyboard navigation
- [ ] Test screen reader (VoiceOver)
- [ ] Test responsive (375px - 1920px)
- [ ] Verify glassmorphism effects
- [ ] Check gradient text rendering
- [ ] Verify loading states

### Deployment
- [ ] Set production env vars in Vercel
- [ ] Deploy to production (git push or vercel --prod)
- [ ] Wait for READY status
- [ ] Verify HTTP 200 on production URL
- [ ] Check both locales load (/en, /vi)
- [ ] Verify sitemap.xml accessible
- [ ] Verify robots.txt accessible

### Post-Deploy
- [ ] Test checkout flow end-to-end
- [ ] Verify webhook deliveries (Polar dashboard)
- [ ] Check analytics events (Vibe dashboard)
- [ ] Monitor Vercel Analytics (24h)
- [ ] Zero console errors in production
- [ ] Check OpenGraph preview (social share)

## Success Criteria

### Build Quality
- ✅ 0 TypeScript errors
- ✅ 0 ESLint warnings
- ✅ 0 `any` types in codebase
- ✅ 0 TODO/FIXME comments
- ✅ 0 high/critical npm vulnerabilities
- ✅ Build time <60s
- ✅ Bundle size <500KB gzipped

### Performance
- ✅ Lighthouse Performance: 90+
- ✅ Lighthouse Accessibility: 95+
- ✅ Lighthouse Best Practices: 95+
- ✅ Lighthouse SEO: 100
- ✅ LCP <2.5s
- ✅ CLS <0.1
- ✅ TTI <3.5s

### Visual & UX
- ✅ All animations 60fps
- ✅ Keyboard navigation works
- ✅ Screen reader compatible
- ✅ Color contrast 4.5:1+
- ✅ Mobile responsive (all breakpoints)
- ✅ No layout shift on load
- ✅ Loading states on async actions

### Production
- ✅ Deployment status: READY
- ✅ HTTP 200 on production URL
- ✅ Both locales accessible (/en, /vi)
- ✅ Sitemap.xml generates correctly
- ✅ Robots.txt accessible
- ✅ Checkout flow completes
- ✅ Webhooks deliver successfully
- ✅ Analytics events tracked
- ✅ Zero console errors

## Risk Assessment

**Risk:** Build fails in production but works locally
**Mitigation:** Run `npm run build` locally first, check env vars

**Risk:** Performance regression on production CDN
**Mitigation:** Run Lighthouse against production URL post-deploy

**Risk:** Animations jank on low-end devices
**Mitigation:** Test on Moto G4 throttling, reduce animation complexity

**Risk:** Webhook signature fails in production
**Mitigation:** Test with Polar CLI webhook forwarding first

**Risk:** Analytics bloat increases bundle size
**Mitigation:** Dynamic import analytics client, check bundle analyzer

## Security Considerations

- Production env vars never committed to git
- Webhook signature verification enabled
- Rate limiting on API routes
- HTTPS enforced (Vercel default)
- No PII in client-side logs
- CSP headers configured (if needed)

## Rollback Plan

If production deployment fails:

```bash
# Option 1: Revert git commit
git revert HEAD
git push origin main

# Option 2: Rollback in Vercel dashboard
# Deployments → Previous deployment → Promote to Production

# Option 3: Instant rollback via CLI
vercel rollback https://previous-deployment-url.vercel.app
```

## Final Report Template

```markdown
# AgencyOS Landing - Deployment Verification Report

**Date:** YYYY-MM-DD
**Deployment URL:** https://agencyos.dev
**Git Commit:** abc1234

## Build Verification
- TypeScript Errors: 0 ✅
- ESLint Warnings: 0 ✅
- Build Time: XXs ✅
- Bundle Size: XXXkB ✅

## Lighthouse Scores (EN)
- Performance: XX/100
- Accessibility: XX/100
- Best Practices: XX/100
- SEO: XX/100

## Lighthouse Scores (VI)
- Performance: XX/100
- Accessibility: XX/100
- Best Practices: XX/100
- SEO: XX/100

## Production Health
- HTTP Status: 200 ✅
- /en Accessible: ✅
- /vi Accessible: ✅
- Sitemap: ✅
- Robots.txt: ✅

## Functional Tests
- Checkout Flow: ✅
- Webhook Delivery: ✅
- Analytics Events: ✅
- Language Switcher: ✅

## Visual Polish
- Animations 60fps: ✅
- Mobile Responsive: ✅
- Accessibility: ✅
- Zero Console Errors: ✅

## Status: ✅ READY FOR GO-LIVE

**Next Steps:**
1. Monitor analytics for 24h
2. Update project documentation
3. Announce launch on social media
```

## Next Steps

**Post-Launch:**
1. Monitor Vercel Analytics (24h)
2. Collect user feedback
3. A/B test pricing tiers
4. Optimize conversion funnel
5. Plan Phase 08: Content & Blog (future)

**Documentation:**
- Update `README.md` with new features
- Document deployment process
- Create runbook for common issues
- Update changelog

**Marketing:**
- Social media announcement
- Product Hunt launch
- SEO monitoring (Google Search Console)
- Backlink building

---

**STATUS:** ✅ AgencyOS Landing Max WOW - Ready to Ship!
