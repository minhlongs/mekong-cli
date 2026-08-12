# Phase 16 — Phase 01.16: Verify - Build & Deploy Validation

**Date:** 260811 · **Status:** pending

## Task
Run production build locally. Verify all environment variables configured. Deploy to staging. Run smoke tests: page loads, forms submit, analytics fire, no 404s. Validate Core Web Vitals on real traffic.

## Files

- vercel.json
- .github/workflows/deploy.yml
- src/app/page.tsx

## Acceptance criteria

`npm run build` exits 0. Staging URL accessible. All forms functional. Analytics events appear in debugger. No 5xx errors. LCP/CLS/FID within thresholds on CrUX.
