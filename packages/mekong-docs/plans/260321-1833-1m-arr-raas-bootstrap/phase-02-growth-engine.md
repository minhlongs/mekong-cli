# Phase 02: Growth Engine

## Priority: P0
## Status: pending

## Tasks

### 2.1 SEO Blog Posts (5 more)
- solo-founder-automation.astro
- cli-vs-gui-productivity.astro
- robot-as-a-service-explained.astro
- mekong-cli-vs-alternatives.astro
- building-saas-with-zero-employees.astro
- Each: 800+ words, meta tags, OG images, internal links

### 2.2 Referral Leaderboard
- GET /v1/tenants/referrals/leaderboard — top 10 referrers
- Display on landing page
- Monthly prizes description

### 2.3 Marketplace Enhancements
- Add ratings/reviews to marketplace missions
- GET /marketplace/:id/reviews
- POST /marketplace/:id/reviews (auth required)
- Average rating display

### 2.4 Social Proof Section
- Stats bar on landing: "X missions completed, Y users, Z countries"
- Live counter via /marketplace/stats endpoint
- Add to docs homepage too

### 2.5 GitHub Actions Integration
- Create github-action for running missions from CI/CD
- Publish to GitHub Marketplace description
- README with usage examples

## Files to Create/Modify
- packages/mekong-docs/src/pages/blog/ (5 new .astro files)
- apps/raas-gateway/src/routes/marketplace.ts (reviews)
- apps/raas-gateway/migrations/ (reviews table)
- apps/raas-landing/public/index.html (social proof)

## Success Criteria
- 5 blog posts live on docs site
- Referral leaderboard API working
- Marketplace has review system
- Social proof visible on landing
