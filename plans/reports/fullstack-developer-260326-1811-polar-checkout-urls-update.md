# Phase Implementation Report

### Executed Phase
- Phase: polar-checkout-urls-update
- Plan: none (direct task)
- Status: completed

### Files Modified
- `packages/raas-landing/src/pages/pricing.astro` — replaced 4 placeholder `buy.polar.sh/openclaw/*` hrefs with `POLAR_ORG_URL` const; added TODO comment block
- `packages/raas-landing/src/pages/en/pricing.astro` — same changes as above (English version)
- `packages/raas-landing/src/pages/index.astro` — replaced 8 placeholder hrefs (4 monthly + 4 annual) with `POLAR_ORG_URL`; added TODO comment block

### Tasks Completed
- [x] Read Polar research report (plans/reports/researcher-260326-1657-polar-raas-products.md)
- [x] Identified all placeholder `https://buy.polar.sh/openclaw/{tier}` URLs in 3 files
- [x] Replaced all CTA hrefs with `https://polar.sh/mekong-cli` (org page fallback)
- [x] Added structured TODO comments in each file showing exact replacement URLs
- [x] Enterprise tier kept as `mailto:hello@agencyos.network` (no change needed)
- [x] Verified 0 stale `buy.polar.sh/openclaw` references remain

### Tests Status
- Type check: N/A (Astro — no tsc run, syntax verified by inspection)
- Unit tests: N/A
- Integration tests: N/A
- Package is gitignored — no git operations

### Changes Summary

All 3 pricing pages now use a `POLAR_ORG_URL` constant:
```
const POLAR_ORG_URL = 'https://polar.sh/mekong-cli';
```

Each non-Enterprise tier href points to this fallback. Inline comments document the final URL pattern:
```
// TODO: replace with https://buy.polar.sh/mekong-cli/openclaw-{tier}
```

### Next Steps (to activate real checkout)
1. Create 5 Polar products at https://polar.sh/mekong-cli using JSON payloads in the research report
2. Copy product slugs/IDs
3. Replace `POLAR_ORG_URL` per-tier with real checkout URLs:
   - Starter: `https://buy.polar.sh/mekong-cli/openclaw-starter`
   - Pro: `https://buy.polar.sh/mekong-cli/openclaw-pro`
   - Growth: `https://buy.polar.sh/mekong-cli/openclaw-growth`
   - Scale: `https://buy.polar.sh/mekong-cli/openclaw-scale`
4. For index.astro, also update `annualHref` with `-annual` variants

### Issues Encountered
- None. index.astro was >10k tokens so used offset read + grep to locate exact lines.

### Unresolved Questions
- Polar org slug: assumed `mekong-cli` matches https://polar.sh/mekong-cli — confirm org exists before creating products
- Annual product slugs: index.astro has annual variants (`-annual`) — need to decide if Polar products will have annual pricing too
