# $1M ARR RaaS Bootstrap — Master Plan

## Context
Mekong CLI v5.0 RaaS platform is LIVE with 5 channels, 40+ endpoints, 8 Polar products.
Current MRR: $0. Target: $83K MRR ($1M ARR).
At avg $150/mo blended = need ~550 paying customers.

## Architecture
- API Gateway: raas.agencyos.network (CF Workers + D1 + KV)
- Landing: landing.agencyos.network
- Dashboard: app.agencyos.network
- Docs: docs.agencyos.network (mekong-docs)
- CLI: mekong-raas bridge
- Telegram: @mekongclibot
- Payments: Polar.sh (dynamic checkout)

## Phases (5 Parallel Tracks)

| Phase | Track | Status | Priority |
|-------|-------|--------|----------|
| 01 | Product Hardening | pending | P0 |
| 02 | Growth Engine | pending | P0 |
| 03 | Sales & Conversion | pending | P1 |
| 04 | Ops & Monitoring | pending | P1 |
| 05 | Revenue Optimization | pending | P2 |

### Phase 01: Product Hardening (P0)
- Webhook reliability (dead-letter queue, retry dashboard)
- Mission templates library (20+ pre-built)
- API SDK improvements (Python SDK, Go SDK)
- Rate limit dashboard for tenants
- Mission history search/filter
- File attachments for missions
See: `phase-01-product-hardening.md`

### Phase 02: Growth Engine (P0)
- SEO: 10 more blog posts targeting long-tail keywords
- Content marketing: YouTube tutorials, Twitter threads
- Community: Discord server setup + bot
- Referral program amplification (leaderboard, rewards tiers)
- Partnership: integrate with popular dev tools
- Open-source showcase (GitHub Actions, VS Code extension)
See: `phase-02-growth-engine.md`

### Phase 03: Sales & Conversion (P1)
- Landing page A/B testing framework
- Onboarding flow optimization (time-to-first-mission < 2min)
- Enterprise sales page + contact form
- Case studies / testimonials section
- Free-to-paid conversion nudges (usage-based CTAs)
- Pricing page with calculator
See: `phase-03-sales-conversion.md`

### Phase 04: Ops & Monitoring (P1)
- Sentry error tracking integration
- Uptime monitoring (Openstatus/Betterstack)
- Usage analytics dashboard (admin)
- Automated weekly digest emails
- SLA documentation
- Incident response playbook
See: `phase-04-ops-monitoring.md`

### Phase 05: Revenue Optimization (P2)
- Usage-based pricing (per-token metering)
- Annual billing (2 months free)
- Enterprise custom pricing
- Dunning management (failed payment recovery)
- Churn prevention (exit surveys, win-back emails)
- Revenue analytics dashboard
See: `phase-05-revenue-optimization.md`

## Success Metrics
- MRR tracking: $0 → $10K → $50K → $83K
- Conversion: Free → Paid > 5%
- Churn: < 5% monthly
- NPS: > 50
- Uptime: 99.9%

## Revenue Math
| Tier | Price | Target Customers | MRR |
|------|-------|-----------------|-----|
| Starter $29 | 200 | $5,800 |
| Pro $99 | 250 | $24,750 |
| Agency $199 | 120 | $23,880 |
| Master $399 | 50 | $19,950 |
| Credit Packs | ~300 | $9,000 |
| **Total** | | **920** | **$83,380** |
