# SEO Optimization Plan — packages/raas-landing

**Date:** 2026-03-18
**Status:** ✅ Complete
**Progress:** 100%
**SEO Score:** 88/100 (Production Ready)

---

## Overview

SEO optimization for raas-landing Astro project with bilingual support (vi/en).

---

## Completed Tasks

| Task | Status | Details |
|------|--------|---------|
| Meta tags | ✅ Complete | title, description, keywords, robots, author |
| OpenGraph tags | ✅ Complete | Full OG suite with locale alternates |
| Twitter Card | ✅ Complete | summary_large_image with @agencyos |
| Hreflang i18n | ✅ Complete | Bidirectional vi ↔ EN links |
| JSON-LD: Organization | ✅ Complete | Via base-layout.astro |
| JSON-LD: WebSite | ✅ Complete | With SearchAction |
| JSON-LD: SoftwareApplication | ✅ Complete | EN homepage |
| JSON-LD: FAQPage | ✅ Complete | EN homepage (5 FAQs) |
| JSON-LD: Product | ✅ Complete | Both pricing pages |
| JSON-LD: BreadcrumbList | ✅ Complete | Both pricing pages |
| sitemap.xml | ✅ Complete | 4 URLs with hreflang annotations |
| robots.txt | ✅ Complete | Sitemap + sensitive path blocking |

---

## Build Verification

- **Build Time:** 594ms
- **Pages Built:** 4 (index, pricing, en/index, en/pricing)
- **Output:** Static SSG
- **All SEO elements:** ✅ Injected in HTML

---

## Reports

- [SEO Code Review](./reports/code-reviewer-2026-03-18-seo-optimization.md) — Score: 88/100
- [Build Verification](./reports/tester-2026-03-18-seo-verification.md) — All checks passed

---

## Recommendations (Next Sprint)

### Must Fix
1. Add Organization + WebSite schema to VI homepage (currently only via layout)
2. Verify canonical URL edge cases for nested routes

### Should Fix
3. Add Review schema for testimonials
4. Enhance robots.txt (block query strings, /_astro/)
5. Add og:updated_time, article:publisher

### Nice to Have
6. Speakable schema for FAQ
7. VideoObject schema for demo video

---

## Files Modified

| File | Changes |
|------|---------|
| `src/layouts/base-layout.astro` | Meta tags, OpenGraph, Twitter, hreflang, Organization + WebSite JSON-LD |
| `src/pages/index.astro` | Already has JSON-LD from layout |
| `src/pages/pricing.astro` | Added Product + BreadcrumbList JSON-LD |
| `src/pages/en/index.astro` | Added SoftwareApplication + FAQPage + BreadcrumbList JSON-LD |
| `src/pages/en/pricing.astro` | Added Product + BreadcrumbList JSON-LD |
| `public/sitemap.xml` | Created with 4 URLs + hreflang |
| `public/robots.txt` | Updated sitemap location |

---

## Deployment Checklist

- [x] Build passes (exit code 0)
- [x] All meta tags present
- [x] All JSON-LD schemas valid
- [x] Hreflang bidirectional correct
- [x] Sitemap.xml valid
- [x] robots.txt valid
- [ ] Core Web Vitals audit (future)
- [ ] 404 page customization (future)
- [ ] 301 redirects (if needed)

---

**Next Step:** Deploy to production (git push → Cloudflare Pages)
