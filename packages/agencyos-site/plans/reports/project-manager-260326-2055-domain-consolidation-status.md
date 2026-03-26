# Domain Consolidation — Status Update

**Date:** 2026-03-26
**Project:** Consolidate 7 agencyos.network subdomains into 1 unified domain
**Status:** IN_PROGRESS
**Completed Phases:** 2/6

---

## Summary

Domain consolidation work progressing on track. Phase 1 (Astro site merge) and Phase 2 (NOWPayments checkout) marked complete. Phases 3-6 remain pending pending manual Cloudflare dashboard operations.

---

## Completed Work

### Phase 1: Merge Astro Sites ✅
- `packages/agencyos-site/` created with unified Astro structure
- Merged 3 separate Astro sites (raas-landing, mekong-docs, raas-dashboard)
- Combined layouts, components, and static assets
- Updated internal links across all files
- Build verification passed with 0 errors
- All routes validated via preview

### Phase 2: NOWPayments Checkout Integration ✅
- NOWPayments invoices created for subscription tiers
- Pricing page (`pages/pricing.astro`) updated with direct invoice URLs
- USDT TRC20 payment badges added
- JSON-LD schema updated for correct URLs
- End-to-end checkout flow tested
- IPN webhook handler implemented in mekong-engine

---

## Pending Work (Requires Cloudflare Dashboard)

### Phase 3: Cloudflare Pages Deploy ⏳
- Create CF Pages project `agencyos-site`
- Configure custom domain `agencyos.network`
- Verify all routes load correctly

### Phase 4: 301 Redirects from Old Subdomains ⏳
- Set up CF Bulk Redirect Rules for 5 old subdomains
- Verify redirects return proper 301 status codes
- Update Google Search Console

### Phase 5: SEO + End-to-End Verification ⏳
- Submit updated sitemap to Google
- Verify canonical URLs correct
- Test all navigation paths
- Update CORS on mekong-engine API

### Phase 6: Cleanup (2+ weeks later) ⏳
- Delete old CF Pages projects
- Clean up DNS records
- Mark old packages as deprecated

---

## Documentation Updates

**Plan File:**
`/Users/macbookprom1/mekong-cli/plans/260326-2036-domain-consolidation/plan.md`
- Status markers updated: Phase 1-2 marked DONE
- Phase 3-6 marked PENDING (Needs Dashboard Access)
- TODO checklists completed for Phases 1-2

**Package Registry:**
`/Users/macbookprom1/mekong-cli/packages/CLAUDE.md`
- Added `agencyos-site` entry to package registry
- Purpose: "Unified marketing site (landing, docs, dashboard)"

---

## Unresolved Questions

1. **Cloudflare account access** — Phases 3-6 require manual CF dashboard operations. Need account credentials/permissions.
2. **Old Pages projects** — Exact Cloudflare Pages project names needed for cleanup phase (raas-landing-page, mekong-docs, mekong-raas-dashboard).
3. **Verification timeline** — After Phase 3 deploy, recommend 2-week verification period before cleanup.
