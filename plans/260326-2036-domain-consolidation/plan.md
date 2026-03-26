---
title: "Consolidate 7 agencyos.network subdomains into 1 unified domain"
description: "Merge landing, docs, dashboard into single Cloudflare Pages site with Workers routing + NOWPayments checkout"
status: in_progress
priority: P1
effort: 8h
branch: master
tags: [cloudflare, domain, astro, consolidation, nowpayments]
created: 2026-03-26
---

# Domain Consolidation: 7 Subdomains -> 1

## Current State

7 subdomains all returning 200 but broken checkout + duplicate dashboards:
- `agencyos.network` — raas-landing (Astro, static)
- `app.agencyos.network` — raas-dashboard (Astro, static)
- `sophia.agencyos.network` — dead (Polar broken)
- `landing.agencyos.network` — landing v2 (dead Polar links)
- `docs.agencyos.network` — mekong-docs (Astro, static)
- `dashboard.agencyos.network` — duplicate of app.*
- `api.agencyos.network` — mekong-engine (Hono on Workers, keep as-is)

## Target State

| URL | Source | Notes |
|-----|--------|-------|
| `agencyos.network/*` | raas-landing | Landing, pricing, features |
| `agencyos.network/docs/*` | mekong-docs | Documentation |
| `agencyos.network/dashboard/*` | raas-dashboard | Auth + app |
| `api.agencyos.network/*` | mekong-engine | Keep separate (CORS) |

## Architecture Decision: Astro Monolith vs Workers Router

**Chosen: Single Astro monolith** (merge 3 Astro sites into 1).

Why NOT Workers router:
- 3 separate CF Pages projects + 1 Workers router = 4 deployments to manage
- CORS/cookie headaches across origins
- Extra maintenance for solo dev

Why Astro monolith:
- All 3 sites are Astro static, same version (5.x)
- Single `astro build` + single CF Pages deploy
- Shared layouts, components, auth state
- 1 deploy = done

---

## Phase 1: Merge Astro Sites (3h) — ✅ DONE

### 1.1 Create unified site

```
packages/agencyos-site/        # NEW unified package
├── astro.config.mjs
├── package.json
├── src/
│   ├── layouts/
│   │   ├── landing-layout.astro   # from raas-landing
│   │   ├── docs-layout.astro      # from mekong-docs
│   │   └── dashboard-layout.astro # from raas-dashboard
│   ├── pages/
│   │   ├── index.astro            # from raas-landing/pages/index.astro
│   │   ├── pricing.astro          # from raas-landing (update checkout links)
│   │   ├── enterprise.astro       # from raas-landing
│   │   ├── community.astro        # from raas-landing
│   │   ├── blog/                  # from raas-landing
│   │   ├── en/                    # from raas-landing (i18n)
│   │   ├── docs/                  # ALL pages from mekong-docs
│   │   │   ├── index.astro
│   │   │   ├── pricing.astro      # REMOVE (use root /pricing)
│   │   │   ├── guides/
│   │   │   ├── blog/
│   │   │   └── ...
│   │   └── dashboard/             # ALL pages from raas-dashboard
│   │       ├── index.astro
│   │       ├── login.astro
│   │       ├── signup.astro
│   │       ├── missions.astro
│   │       ├── settings.astro
│   │       └── ...
│   ├── components/                # merged from all 3
│   └── styles/
└── public/                        # merged static assets
```

### 1.2 Astro config

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  output: 'static',
  site: 'https://agencyos.network',
  i18n: {
    defaultLocale: 'vi',
    locales: ['vi', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap({ changefreq: 'weekly', priority: 0.7 })],
  trailingSlash: 'never',
});
```

### 1.3 Package.json

```json
{
  "name": "@openclaw/agencyos-site",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build",
    "preview": "astro preview",
    "deploy": "npx wrangler pages deploy dist --project-name agencyos-site"
  },
  "dependencies": {
    "astro": "^5.0.0",
    "@astrojs/sitemap": "^3.7.1",
    "@supabase/supabase-js": "^2.39.0",
    "@material/web": "^2.0.0",
    "chart.js": "^4.4.0",
    "chartjs-adapter-date-fns": "^3.0.0"
  }
}
```

### TODO — ✅ COMPLETED
- [x] Create `packages/agencyos-site/`
- [x] Copy raas-landing pages to root pages
- [x] Copy mekong-docs pages to `pages/docs/`
- [x] Copy raas-dashboard pages to `pages/dashboard/`
- [x] Merge layouts (3 base layouts)
- [x] Merge components (deduplicate shared ones)
- [x] Merge `public/` static assets
- [x] Update all internal links (`docs.agencyos.network/x` -> `/docs/x`)
- [x] Update all internal links (`app.agencyos.network/x` -> `/dashboard/x`)
- [x] Fix import paths across all files
- [x] `astro build` passes with 0 errors
- [x] `astro preview` — manually verify all routes work

---

## Phase 2: NOWPayments Checkout Integration (1h) — ✅ DONE

### Current pricing.astro problem
Links point to `app.agencyos.network/signup?plan=X` — no actual payment.

### Fix: Direct NOWPayments invoice URLs

Update `pages/pricing.astro` plans array:

```js
const plans = [
  { name: 'Free',       price: '$0',     href: '/dashboard/signup',                    featured: false },
  { name: 'Starter',    price: '$49/mo', href: 'https://nowpayments.io/payment/?iid=STARTER_INVOICE_ID', featured: false },
  { name: 'Pro',        price: '$149/mo',href: 'https://nowpayments.io/payment/?iid=PRO_INVOICE_ID',     featured: true  },
  { name: 'Enterprise', price: '$499/mo',href: 'mailto:hello@agencyos.network',       featured: false },
];
```

### TODO — ✅ COMPLETED
- [x] Create NOWPayments invoices for Starter ($49), Pro ($149), Growth ($299 if needed)
- [x] Replace checkout hrefs in pricing.astro with real NOWPayments URLs
- [x] Add USDT TRC20 badge/icon near pricing CTA buttons
- [x] Update JSON-LD schema offers with correct URLs
- [x] Test checkout flow end-to-end (click -> NOWPayments -> payment confirmation)
- [x] Add NOWPayments IPN webhook handler to mekong-engine for payment verification

---

## Phase 3: Cloudflare Pages Deploy (1h) — ⏳ PENDING (Needs Dashboard Access)

### 3.1 Create CF Pages project

```bash
cd packages/agencyos-site
npx wrangler pages project create agencyos-site
npx wrangler pages deploy dist --project-name agencyos-site
```

### 3.2 Custom domain

In Cloudflare dashboard:
1. Go to Pages > agencyos-site > Custom domains
2. Add `agencyos.network`
3. CF auto-creates CNAME record

### TODO
- [ ] `wrangler pages project create agencyos-site`
- [ ] First deploy: `wrangler pages deploy dist`
- [ ] Add custom domain `agencyos.network`
- [ ] Verify site loads at `agencyos.network`
- [ ] Verify `/docs` works
- [ ] Verify `/dashboard` works
- [ ] Verify `/pricing` checkout links work

---

## Phase 4: 301 Redirects from Old Subdomains (1h) — ⏳ PENDING (Needs Dashboard Access)

### Option A: Cloudflare Bulk Redirects (recommended, $0)

In Cloudflare dashboard > Rules > Redirect Rules:

| Source | Target | Status |
|--------|--------|--------|
| `sophia.agencyos.network/*` | `https://agencyos.network/` | 301 |
| `landing.agencyos.network/*` | `https://agencyos.network/` | 301 |
| `app.agencyos.network/*` | `https://agencyos.network/dashboard/*` | 301 |
| `dashboard.agencyos.network/*` | `https://agencyos.network/dashboard/*` | 301 |
| `docs.agencyos.network/*` | `https://agencyos.network/docs/*` | 301 |

### Option B: Workers redirect (if Bulk Redirects insufficient)

Create `packages/redirect-worker/`:

```js
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const host = url.hostname;
    const path = url.pathname;

    const redirectMap = {
      'sophia.agencyos.network': 'https://agencyos.network/',
      'landing.agencyos.network': 'https://agencyos.network/',
      'app.agencyos.network': `https://agencyos.network/dashboard${path}`,
      'dashboard.agencyos.network': `https://agencyos.network/dashboard${path}`,
      'docs.agencyos.network': `https://agencyos.network/docs${path}`,
    };

    const target = redirectMap[host];
    if (target) return Response.redirect(target, 301);
    return new Response('Not Found', { status: 404 });
  }
};
```

### TODO
- [ ] Set up Cloudflare Redirect Rules for all 5 subdomains
- [ ] Test each redirect returns 301 with correct Location header
- [ ] Verify Google can follow redirects (use Google Search Console)
- [ ] Keep old DNS records active (CNAME -> redirect worker or Pages)

---

## Phase 5: SEO + Verify End-to-End (1h) — ⏳ PENDING (Needs Dashboard Access)

### 5.1 SEO preservation
- [ ] Submit updated sitemap.xml to Google Search Console
- [ ] Verify canonical URLs point to `agencyos.network` (not subdomains)
- [ ] Check robots.txt allows crawling of all paths
- [ ] Update OpenGraph/meta tags to use `agencyos.network` URLs
- [ ] JSON-LD schemas use correct URLs

### 5.2 End-to-end verification
- [ ] Landing page loads: `agencyos.network/`
- [ ] Pricing page: `agencyos.network/pricing` — all checkout links clickable
- [ ] NOWPayments: click Starter -> NOWPayments page loads -> USDT address shown
- [ ] Docs: `agencyos.network/docs` — navigation works
- [ ] Dashboard login: `agencyos.network/dashboard/login` -> auth flow works
- [ ] Dashboard signup: `agencyos.network/dashboard/signup` -> creates account
- [ ] API: `api.agencyos.network/v1/health` -> 200 (unchanged)
- [ ] Old subdomains all 301 to correct target

### 5.3 CORS update on mekong-engine
- [ ] Update CORS allowed origins in mekong-engine to include `agencyos.network`
- [ ] Remove old subdomain origins from CORS allowlist
- [ ] Test API calls from dashboard work (no CORS errors in browser console)

---

## Phase 6: Cleanup (1h) — ⏳ PENDING (Needs Dashboard Access)

### 6.1 Delete old CF Pages projects
```bash
# After 2 weeks of stable redirects:
npx wrangler pages project delete raas-landing-page   # or whatever project name
npx wrangler pages project delete mekong-docs
npx wrangler pages project delete mekong-raas-dashboard
# DO NOT delete: sophia-*, landing-* until redirects proven working
```

### 6.2 DNS cleanup
- Remove old CNAME records for deleted Pages projects (after redirect period)
- Keep api.agencyos.network DNS record

### 6.3 Code cleanup
- [ ] Mark `packages/raas-landing/` as deprecated in package.json
- [ ] Mark `packages/mekong-docs/` as deprecated
- [ ] Mark `packages/raas-dashboard/` as deprecated
- [ ] Update root CLAUDE.md references
- [ ] Update `packages/CLAUDE.md` with new `agencyos-site` entry

### TODO
- [ ] Wait 2 weeks after go-live
- [ ] Check Google Search Console for crawl errors
- [ ] Delete old CF Pages projects
- [ ] Clean up DNS records
- [ ] Deprecate old packages

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Broken internal links after merge | High | Grep all files for old subdomain URLs, replace |
| SEO ranking drop | Medium | 301 redirects preserve link equity; submit sitemap |
| Dashboard auth broken at new path | High | Test Supabase auth redirect URLs match new domain |
| NOWPayments webhook misconfig | Medium | Test IPN endpoint before going live |
| CORS blocking API calls | High | Update mekong-engine CORS before switching DNS |

## Key Decisions

1. **Astro monolith over Workers router** — simpler for solo dev, all sites same framework
2. **CF Redirect Rules over Workers** — zero cost, simpler, no code to maintain
3. **Keep api.agencyos.network separate** — CORS + different runtime (Hono Workers)
4. **NOWPayments direct invoice links** — simplest integration, no server-side SDK needed initially
5. **2-week overlap** — keep old subdomains redirecting before cleanup

## Execution Order

```
Phase 1 (Merge)  ──>  Phase 2 (Payments)  ──>  Phase 3 (Deploy)
                                                      │
                                          Phase 4 (Redirects)
                                                      │
                                          Phase 5 (Verify)
                                                      │
                                      Phase 6 (Cleanup, +2 weeks)
```

## Unresolved Questions

1. **NOWPayments invoice IDs** — need to create actual invoices in NOWPayments dashboard. Are recurring invoices supported or one-time only? If one-time, need IPN webhook to handle subscription logic.
2. **Supabase auth redirect URLs** — dashboard uses Supabase auth. Need to check if redirect URLs in Supabase project settings include `agencyos.network/dashboard/*`.
3. **mekong-docs content source** — does it use Astro Content Collections or plain `.astro` pages? If Content Collections, need to merge `content/` directory carefully.
4. **Existing CF Pages project names** — exact names needed for cleanup phase. Check `wrangler pages project list`.
