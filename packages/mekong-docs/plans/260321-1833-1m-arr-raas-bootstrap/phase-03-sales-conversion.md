# Phase 03: Sales & Conversion

## Priority: P1
## Status: pending

## Tasks

### 3.1 Onboarding Flow Optimization
- Auto-create first mission on signup (welcome mission)
- Show result immediately → "See what RaaS can do"
- Reduce time-to-first-value to < 60 seconds

### 3.2 Enterprise Contact Page
- /enterprise page on docs site
- Contact form → sends to Telegram bot
- Enterprise features list (SSO, SLA, custom models, dedicated support)

### 3.3 Pricing Calculator
- Interactive pricing calculator on docs /pricing page
- Input: missions/month, complexity mix
- Output: recommended tier + estimated cost

### 3.4 Usage-Based CTAs
- When balance < 5: show upgrade CTA in API response
- When hitting rate limit: include upgrade URL
- Weekly digest: include upgrade suggestion if usage > 80% of tier limit

### 3.5 Case Studies Template
- /case-studies page on docs
- Template: problem, solution, results, quote
- 3 hypothetical case studies (solo founder, agency, enterprise)

### 3.6 Free Trial Extension
- /v1/tenants/trial-extend — one-time +10 credits for sharing on Twitter
- Viral loop: share → get credits → use more → pay

## Files to Create/Modify
- packages/mekong-docs/src/pages/enterprise.astro
- packages/mekong-docs/src/pages/case-studies.astro
- packages/mekong-docs/src/pages/pricing.astro (calculator)
- apps/raas-gateway/src/routes/tenants.ts (trial-extend, onboarding)
- apps/raas-gateway/src/services/credit-service.ts (CTA logic)

## Success Criteria
- Enterprise page live
- Pricing calculator interactive
- Auto-welcome mission on signup
- CTAs appearing at low balance
