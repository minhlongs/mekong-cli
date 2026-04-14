# RaaS Landing Page UI Audit Report

**Date:** 2026-03-19
**Package:** `@openclaw/raas-landing`
**Framework:** Astro 5.0 (Static Output)
**Language:** i18n (Vietnamese default, English)

---

## 1. Current Page Tree

```
packages/raas-landing/
├── src/
│   ├── pages/
│   │   ├── index.astro          # Vietnamese homepage (main landing)
│   │   ├── pricing.astro        # Vietnamese pricing page
│   │   └── en/
│   │       ├── index.astro      # English homepage
│   │       └── pricing.astro    # English pricing page
│   ├── layouts/
│   │   └── base-layout.astro    # Shared layout with nav + footer
│   ├── i18n/
│   │   ├── vi.json              # Vietnamese translations (8 keys)
│   │   └── en.json              # English translations (8 keys)
│   └── styles/
│       └── global.css           # All styles + animations (1,888 lines)
├── dist/                        # Build output
│   ├── index.html
│   ├── pricing/
│   ├── en/
│   │   ├── index.html
│   │   └── pricing/
│   └── _astro/                  # Hashed assets
├── public/
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

### Live Routes

| Route | Language | Status |
|-------|----------|--------|
| `/` | Vietnamese | Homepage + all sections |
| `/pricing` | Vietnamese | Pricing comparison table |
| `/en` | English | Homepage |
| `/en/pricing` | English | Pricing |

---

## 2. Component Structure Analysis

### Layout Hierarchy

```
BaseLayout (base-layout.astro)
├── Sticky Navigation
│   ├── Logo (OpenClaw gradient text)
│   ├── Nav Links (Features, Pricing, FAQ)
│   ├── Language Switcher (VI | EN)
│   └── CTA Button (Sign up)
├── Main Content (<slot />)
└── Footer
    ├── Product Links
    ├── Company Links
    └── Legal Links (Privacy, Terms)
```

### Homepage Sections (index.astro - 700+ lines)

| Section | Purpose | Key Features |
|---------|---------|--------------|
| Hero | Above fold conversion | FOMO badge, mesh gradient orbs, terminal demo, social proof counters, customer logos |
| Features | Value proposition | 4-card grid (AI Receptionist, Content Creator, CRM, Reports) |
| How It Works | Onboarding flow | 3-step process with connector dots |
| Platform Power | Platform stats | 5 stat cards (319 commands, 540 skills, etc.) |
| Testimonials | Social proof | Auto-playing carousel (6 testimonials with results) |
| Pricing | Tier preview | 4-card pricing grid with toggle |
| FAQ | Objection handling | 5 expandable questions |
| CTA Banner | Bottom conversion | Gradient banner with signup |

### Pricing Page (pricing.astro)

| Section | Purpose |
|---------|---------|
| Header | Gradient hero with CTA |
| Comparison Table | 10-row feature matrix (4 tiers) |
| Contact Section | Support CTA |

### Component Patterns

**Reusable UI Components (inline in pages):**
- `.badge` — Label badges
- `.btn-primary` / `.btn-outline` — Button variants
- `.card` / `.card-glass` — Content cards with glassmorphism
- `.grid-2` / `.grid-3` / `.grid-4` — Responsive grids
- `.terminal` — Code demo mockup
- `.testimonial-carousel` — Auto-playing testimonial slider

**Animation Classes:**
- `.animate-in` — Fade up on load
- `.animate-on-scroll` — Intersection Observer trigger
- `.btn-pulse` — Pulsing CTA ring
- `.gradient-text` — Cyan-to-purple gradient text

---

## 3. JSON-LD Schema Coverage

| Schema Type | Location | Status |
|-------------|----------|--------|
| `Organization` | base-layout.astro | Implemented |
| `WebSite` | base-layout.astro | Implemented |
| `Article` | base-layout.astro | Conditional (for blog) |
| `SoftwareApplication` | index.astro | Implemented |
| `Service` (RaaS) | index.astro | Implemented |
| `FAQPage` | index.astro | Implemented |
| `Product` (pricing) | pricing.astro | Implemented |
| `BreadcrumbList` | Both pages | Implemented |

---

## 4. i18n Structure

### Current Translation Keys (8 keys)

```json
{
  "nav": { "features", "pricing", "faq", "cta" },
  "hero": { "title", "subtitle", "cta", "demo" },
  "features": { "title", "ai", "aiDesc", "content", "contentDesc", "crm", "crmDesc", "report", "reportDesc" },
  "pricing": { "title", "free", "starter", "pro", "enterprise", "popular", "cta" },
  "faq": { "title" },
  "footer": { "product", "dashboard", "docs", "contact" }
}
```

**Issue:** i18n JSON files exist but pages use **hardcoded Vietnamese text** directly. The `vi.json` and `en.json` files are unused.

---

## 5. Responsive Design Status

### Breakpoints

| Breakpoint | Trigger | Behavior |
|------------|---------|----------|
| Desktop | > 1024px | 4-column grids, full hero layout |
| Tablet | 768px - 1024px | 2-column grids, hero stacks |
| Mobile | < 768px | Single column, condensed spacing |
| Small Mobile | < 640px | Extra condensing, hides decorative elements |

### Responsive Issues Identified

| Issue | Severity | Impact |
|-------|----------|--------|
| Hero terminal pushes content on small screens | Medium | May cause horizontal scroll on < 380px |
| Testimonial carousel dots overflow | Low | Visual glitch on very narrow screens |
| Pricing table horizontal scroll | Medium | Comparison table requires scroll < 640px |
| Footer grid stacks awkwardly | Low | Could use better mobile spacing |

### Accessibility Features

- **Skip to content link** (`.skip-link`) — Implemented
- **ARIA labels** on nav, buttons, carousel — Partially implemented
- **Focus visible** styles — Implemented for nav links
- **Reduced motion** support — `@media (prefers-reduced-motion)` implemented
- **High contrast** support — Basic styles present
- **Print styles** — Minimal but present

---

## 6. Gaps for 5-Layer Command Hierarchy Integration

### Current Navigation (3 items)

```
Features | Pricing | FAQ | [VI|EN] | [CTA Button]
```

### Required 5-Layer Navigation

Based on mekong-cli command hierarchy:

| Layer | Commands | Proposed Nav Label |
|-------|----------|-------------------|
| **Founder** | `/annual`, `/okr`, `/fundraise`, `/swot` | `Strategy` |
| **Business** | `/sales`, `/marketing`, `/finance`, `/hr` | `Business` |
| **Product** | `/plan`, `/sprint`, `/roadmap` | `Product` |
| **Engineering** | `/cook`, `/code`, `/test`, `/deploy` | `Engineering` |
| **Ops** | `/audit`, `/health`, `/security` | `Ops` |

### Required Changes

1. **Navigation Expansion**
   - Current: 3 links + lang + CTA
   - Required: 5 layer dropdowns OR mega-menu

2. **New Pages Needed**
   - `/commands` — Full command catalog (319 commands)
   - `/commands/{layer}` — Per-layer command index
   - `/skills` — AI Skills catalog (540 skills)
   - `/agents` — Agent directory (17 agents)
   - `/contracts` — Machine contracts (410 contracts)

3. **Footer Updates**
   - Add layer-specific quick links
   - Add command/skill search
   - Add CLI quickstart link

4. **Hero Section Updates**
   - Current hero focuses on RaaS features
   - Need to also highlight 5-layer command hierarchy
   - Consider dual-CTA: "Try RaaS" + "Explore Commands"

5. **Search Functionality**
   - No search currently implemented
   - Add command search (Algolia/DocSearch)

---

## 7. Technical Debt

| Issue | File | Lines | Fix Effort |
|-------|------|-------|------------|
| Hardcoded text (not using i18n JSON) | `index.astro` | ~500 | 2-3h |
| Inline styles in Astro (should use CSS variables) | `index.astro` | ~200 | 4-6h |
| Global CSS file too large | `global.css` | 1,888 | Split into modules |
| Carousel JS in Astro script tag | `index.astro` | ~150 | Extract to `.ts` |
| No TypeScript types for props | `layouts/base-layout.astro` | — | Add interfaces |
| Duplicate pricing data | `index.astro` + `pricing.astro` | — | Extract to shared JSON |

---

## 8. Recommendations

### Priority 1 (Critical for 5-Layer Integration)

1. **Create navigation mega-menu component**
   - 5 dropdowns for each layer
   - Show top 3-5 commands per layer
   - Link to full command catalog

2. **Add command catalog page**
   - Filterable by layer (Founder/Business/Product/Engineering/Ops)
   - Search by keyword
   - MCU cost badges

3. **Update homepage hero**
   - Dual value prop: RaaS + CLI
   - Add terminal demo showing 5-layer commands
   - Update stats (319 commands, 540 skills, etc.)

### Priority 2 (UX Improvements)

1. **Fix i18n implementation**
   - Import and use `vi.json` / `en.json`
   - Remove hardcoded strings
   - Add missing translation keys

2. **Extract CSS modules**
   - `components/` folder for reusable styles
   - Split `global.css` into: `base.css`, `components.css`, `animations.css`, `responsive.css`

3. **Add command search**
   - DocSearch integration
   - Keyboard shortcut (Cmd+K)

### Priority 3 (Polish)

1. **Add missing pages**
   - `/docs` — Documentation index
   - `/changelog` — Version history
   - `/blog` — Technical blog (use Astro Content Collections)

2. **Improve responsive tables**
   - Pricing comparison on mobile
   - Consider card layout for < 640px

3. **Add analytics**
   - Track CTA clicks
   - Track command page views
   - Funnel analysis for signup flow

---

## 9. File References

| File | Absolute Path |
|------|---------------|
| Homepage (VI) | `/Users/macbook/mekong-cli/packages/raas-landing/src/pages/index.astro` |
| Pricing (VI) | `/Users/macbook/mekong-cli/packages/raas-landing/src/pages/pricing.astro` |
| Homepage (EN) | `/Users/macbook/mekong-cli/packages/raas-landing/src/pages/en/index.astro` |
| Pricing (EN) | `/Users/macbook/mekong-cli/packages/raas-landing/src/pages/en/pricing.astro` |
| Base Layout | `/Users/macbook/mekong-cli/packages/raas-landing/src/layouts/base-layout.astro` |
| Global Styles | `/Users/macbook/mekong-cli/packages/raas-landing/src/styles/global.css` |
| i18n VI | `/Users/macbook/mekong-cli/packages/raas-landing/src/i18n/vi.json` |
| i18n EN | `/Users/macbook/mekong-cli/packages/raas-landing/src/i18n/en.json` |
| Astro Config | `/Users/macbook/mekong-cli/packages/raas-landing/astro.config.mjs` |

---

## 10. Summary

**Current State:**
- 2-page landing (Home + Pricing) with i18n (VI/EN)
- Strong visual design with animations and social proof
- Comprehensive JSON-LD SEO schemas
- Responsive but has minor mobile issues

**Gaps for 5-Layer Integration:**
- Navigation only has 3 links (needs 5-layer structure)
- No command catalog or skill directory pages
- Homepage focuses on RaaS, not CLI capabilities
- i18n JSON files exist but are unused
- No search functionality

**Next Steps:**
1. Design 5-layer navigation mega-menu
2. Create command catalog page with filters
3. Update hero to showcase CLI + RaaS
4. Fix i18n implementation
5. Add search (DocSearch)
