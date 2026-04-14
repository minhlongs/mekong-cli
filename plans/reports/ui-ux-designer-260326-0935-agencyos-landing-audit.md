# UI/UX Audit: AgencyOS Landing Page (agencyos.network)

**Date:** 2026-03-26 | **Auditor:** UI/UX Designer
**Source:** `apps/agencyos-landing/src/App.tsx` (~90 lines)
**Live URL:** https://agencyos.network
**Stack:** React 19 + Vite + Cloudflare Pages (NO Tailwind, NO design system)

---

## 1. Current Score Card

| Dimension | Score | Notes |
|---|---|---|
| **Visual Design** | 2/10 | Inline styles, no design system, no visual hierarchy, no imagery |
| **Content Quality** | 2/10 | Generic placeholder copy, incomplete product list, no value props |
| **Conversion Optimization** | 1/10 | Dead CTA links, no signup flow, no social proof, no urgency |
| **Mobile Responsive** | 2/10 | Inline styles with no media queries; `grid auto-fit` provides minimal responsiveness but no actual mobile optimization |
| **Brand Consistency** | 1/10 | Design guidelines doc specifies "Deep Space" glassmorphism system (Space Grotesk + Inter, #030014 bg, neon cyan/purple palette). App.tsx uses NONE of it -- system-ui font, #111827 bg, basic cyan #06b6d4. Zero brand alignment. |
| **TOTAL** | **8/50** (16%) | Far below acceptable threshold |

---

## 2. Critical Architecture Problem

**There are 6 rich components already built** in `src/components/` that are NOT used:
- `features-grid.tsx` -- 6 feature cards with icons, animations
- `how-it-works.tsx` -- 4-step process with timeline
- `pricing-table.tsx` -- 3-tier glassmorphism pricing with Polar checkout
- `terminal-animation.tsx` -- animated terminal demo
- `service-cards.tsx` -- 6 service cards with pricing
- `sections/contact-section.tsx` -- contact form

**BUT** these components are written for Next.js (`"use client"`, `@/components/glass`, `next-intl`, `framer-motion`) and CANNOT run in the current Vite + React setup. The live `App.tsx` is a completely separate, stripped-down fallback.

**This is the #1 problem.** The team built a rich landing page for a different framework, then deployed a skeleton placeholder instead.

---

## 3. Top 10 Issues Ranked by Conversion Impact

### #1. ALL CTAs LINK TO DEAD URLS (Severity: CRITICAL)
- "Try RaaS Free" links to `landing.agencyos.network` -- **does not exist**
- All 4 pricing CTAs link to `landing.agencyos.network` -- **does not exist**
- "Open Dashboard" links to dashboard without auth -- user sees nothing useful
- **Impact:** 100% CTA failure rate. Zero conversions possible.
- **Fix:** Route Free CTA to `/v1/tenants/signup`, paid CTAs to `raas.agencyos.network` checkout

### #2. NO SIGNUP/ONBOARDING FLOW
- `/v1/tenants/signup` endpoint exists and works, but NOTHING on the page links to it
- No email capture, no free trial form, no "Get Started" that actually works
- **Impact:** Even motivated visitors cannot convert

### #3. NO SOCIAL PROOF OR TRUST SIGNALS
- Zero testimonials, zero customer logos, zero usage stats
- No "X missions completed", no "Y agents deployed"
- No GitHub stars count (Mekong CLI is open source)
- **Impact:** B2B SaaS buyers need proof before paying. Trust deficit = 0 conversions.

### #4. INCOMPLETE PRODUCT ECOSYSTEM
- Page shows 3 products. Actual ecosystem has 6+:
  - RaaS Gateway (API) -- shown
  - Dashboard -- shown
  - Mekong CLI -- shown
  - AlgoTrade -- missing
  - SoloOS -- missing
  - Docs -- missing
  - Factory (410 contracts) -- missing
- Mission: agencyos.network = "sun" hub directing to "planet" subdomains
- **Current:** a flat list with wrong URLs

### #5. ZERO VISUAL DIFFERENTIATION
- No images, screenshots, illustrations, or icons
- No terminal demo (one exists in components but not used)
- No product screenshots or GIFs
- Visitors cannot see what they're buying
- **Impact:** SaaS pages with screenshots convert 25-40% better

### #6. GENERIC, LOW-VALUE COPY
Current hero: *"Deploy & Scale AI Agents. Enterprise-grade infrastructure for your AI operations."*
- "Enterprise-grade" is meaningless without proof
- No specific numbers (50+ endpoints, 342+ commands, 410 contracts)
- No pain point addressed, no outcome promised
- Product descriptions are feature lists, not benefit statements

### #7. PRICING DISCONNECT
- Page shows 4 tiers: Free $0, Starter $29, Pro $99, Agency $199
- Existing components show 3 tiers: Free $0, Pro $49, Enterprise custom
- CLAUDE.md shows: Starter $49, Pro $149, Enterprise $499
- **Three different pricing structures** across the codebase
- No tier links to actual Polar checkout

### #8. NO RESPONSIVE DESIGN
- All styling via inline `style={{}}` props
- No `@media` queries, no mobile breakpoints
- Header nav items will overflow on mobile (no hamburger menu)
- Cards will stack but with no mobile-specific spacing
- Touch targets not sized for mobile (no min 44x44px)

### #9. NO ANIMATIONS OR MICRO-INTERACTIONS
- Static page, no scroll animations, no hover states (except browser default)
- No loading states, no transitions
- Terminal animation component exists but is unused
- **Impact:** Page feels like a prototype, not a product

### #10. NO "HOW IT WORKS" EXPLANATION
- Visitors don't understand what RaaS/MCU/agents mean
- No onboarding funnel: explain > demonstrate > convert
- The "How it Works" component exists (4 steps, animated) but is unused
- **Impact:** High bounce rate from confusion

---

## 4. Recommended Page Structure

### Section Order (conversion-optimized)

```
1. NAVIGATION BAR
   - Logo + "AgencyOS" wordmark
   - Links: Products (dropdown), Pricing, Docs, API
   - CTAs: "Sign In" (ghost) + "Get Started Free" (primary)

2. HERO (above the fold)
   - Badge: "Open Source | 342+ Commands | MIT License"
   - H1: outcome-focused headline (see copy below)
   - Subtitle: 1-line value prop
   - 2 CTAs: "Start Free (10 credits)" + "View Demo"
   - Terminal animation (live demo of `mekong cook`)
   - Trust bar: "Powering X missions | Y agents | Z deployments"

3. PRODUCT ECOSYSTEM ("The Hub")
   - H2: "One Platform. Every Business Function."
   - Solar system / orbit visual metaphor
   - 6-8 product cards linking to live subdomains:
     - raas.agencyos.network -- RaaS API Gateway
     - app.agencyos.network -- Dashboard
     - docs.agencyos.network -- Documentation
     - api.agencyos.network -- API Reference
     - CLI (npm install) -- Mekong CLI
     - AlgoTrade, SoloOS, Factory (future)
   - Each card: icon + name + 1-line benefit + live status badge

4. HOW IT WORKS
   - 4 steps: Describe Goal > AI Plans > Agents Execute > Get Results
   - Animated timeline/stepper
   - Each step: icon + title + description

5. FEATURES GRID
   - 6 key differentiators with icons
   - PEV Engine, Self-Healing, Open Source, Pay-per-Result, 5 Business Layers, Cascade

6. SERVICES SHOWCASE
   - Pre-packaged services with credit costs
   - Categories: Business, Tech, Marketing
   - Each: title + description + credits + estimated time

7. SOCIAL PROOF
   - GitHub stars + npm downloads
   - API stats: "50+ endpoints | 410 contracts | 5-layer architecture"
   - Testimonial placeholders (add real ones when available)

8. PRICING
   - 3 tiers (align with Polar checkout):
     - Free: 10 credits, $0
     - Pro: 200 credits, $49/mo (highlighted)
     - Enterprise: Custom, contact
   - CTAs link to actual Polar checkout or signup endpoint
   - FAQ accordion below

9. CTA BANNER
   - "Ready to automate your business?"
   - Email capture or direct signup button
   - Links to /v1/tenants/signup

10. FOOTER
    - Product links (all subdomains)
    - Resources: Docs, API, CLI, GitHub
    - Company: About, Contact, Terms
    - Social: GitHub, Twitter/X
    - "Built with Mekong CLI" badge
```

---

## 5. Specific Copy Recommendations

### Hero Section

**Current:**
> Deploy & Scale AI Agents
> Enterprise-grade infrastructure for your AI operations.

**Recommended Option A (outcome-focused):**
> Your AI Workforce, Ready in Seconds
> Submit a goal in plain language. AI agents plan, execute, and verify -- automatically. 342+ commands. 50+ API endpoints. Pay only for results.

**Recommended Option B (bold/direct):**
> Stop Building. Start Commanding.
> Mekong CLI turns your business goals into executed tasks. One command. Multiple AI agents. Verified results in minutes.

**Recommended Option C (hub positioning):**
> The Operating System for AI-Powered Business
> One platform connecting API Gateway, Dashboard, CLI, and 410+ agent contracts. From strategy to deployment -- fully automated.

### CTA Buttons

| Current | Recommended |
|---|---|
| "Open Dashboard" | "Start Free -- 10 Credits" |
| "Try RaaS Free" | "Watch Demo" or "See It In Action" |

### Product Cards

| Product | Current Desc | Recommended |
|---|---|---|
| RaaS Gateway | "50+ API endpoints, AI mission execution, multi-model" | "50+ endpoints powering AI missions. Submit goals via API, get verified results. Multi-model routing built in." |
| Dashboard | "Real-time analytics, mission tracking, credit management" | "Track every mission in real-time. Monitor agents, manage credits, audit every execution step." |
| Mekong CLI | "17 commands, instant mission submission from terminal" | "342+ commands from your terminal. `mekong cook` turns English into deployed code. MIT licensed, runs anywhere." |

### Pricing CTA

| Current | Recommended |
|---|---|
| "Get Started" / "Subscribe" | "Start Free -- No Card Required" / "Upgrade to Pro" / "Talk to Sales" |

---

## 6. Design System Recommendations

### Use the existing "Deep Space" system from `docs/design-guidelines.md`

The design guidelines already define a comprehensive system. The landing page ignores ALL of it.

#### Colors (from existing guidelines)

| Token | Hex | Usage |
|---|---|---|
| `--bg-deep-space` | `#030014` | Page background (NOT #111827) |
| `--primary` | `#00F5FF` (Neon Cyan) | CTAs, links, accents |
| `--secondary` | `#8B5CF6` (Electric Purple) | Gradients, secondary |
| `--accent` | `#EC4899` (Hot Pink) | Alerts, special moments |
| `--surface` | `white/5` | Card backgrounds |
| `--border` | `white/10` | Card borders |

#### Typography (from existing guidelines)

| Element | Font | Weight | Size |
|---|---|---|---|
| H1 | Space Grotesk | 700 | 3.5rem (mobile: 2.5rem) |
| H2 | Space Grotesk | 700 | 2.5rem (mobile: 2rem) |
| H3 | Space Grotesk | 500 | 1.5rem |
| Body | Inter | 400 | 1rem (16px) |
| Small | Inter | 400 | 0.875rem |
| Mono | JetBrains Mono | 400 | 0.875rem |

#### Effects

- **Noise texture:** SVG overlay at 3% opacity on body
- **Glassmorphism:** `backdrop-blur-xl` + `bg-deep-space/60` + `border white/10`
- **Glows:** Radial gradient behind hero and featured cards
- **Animations:** Framer Motion (already in unused components)

### Implementation Path

**Option A (Quick Win):** Port existing Next.js components to plain React + CSS modules. ~2 days.

**Option B (Proper):** Migrate `agencyos-landing` to use Tailwind CSS. Add the Deep Space tokens. Port components. ~3-4 days.

**Option C (Full):** Rebuild on the same Next.js stack as `raas.agencyos.network` for consistency. Share component library. ~1 week.

**Recommendation:** Option B. Tailwind is already used across other Mekong CLI apps. Add it to this Vite project, import the design tokens, and adapt the 6 existing components.

---

## 7. Quick Wins (< 1 day each)

1. **Fix dead CTAs** -- Route to actual signup/checkout URLs. Instant conversion unlock.
2. **Add terminal animation** -- Port `terminal-animation.tsx` to work without framer-motion (pure CSS). Shows product value immediately.
3. **Update product list** -- Add all subdomains as product cards with correct URLs.
4. **Add trust bar** -- "342+ Commands | 50+ API Endpoints | 410 Agent Contracts | MIT License"
5. **Fix pricing** -- Align with Polar checkout, link to real endpoints.

---

## 8. Competitive Benchmark

For context, award-winning SaaS landing pages (Vercel, Linear, Supabase, Resend) share these traits:

| Trait | AgencyOS Has? |
|---|---|
| Dark mode with depth (glow, grain) | No (flat gray gradient) |
| Animated hero demo | No (exists but unused) |
| Clear H1 with specific numbers | No (generic) |
| Working CTAs to signup | No (dead links) |
| Product screenshots/GIFs | No |
| Social proof section | No |
| Mobile-first responsive | No |
| Smooth scroll animations | No |
| Consistent design system | No |
| Fast load (<1s FCP) | Yes (only advantage -- it's tiny) |

---

## 9. Summary Verdict

The current agencyos.network is a **non-functional placeholder** that cannot convert any visitor. It scores 8/50 (16%). The irony: the team already built 6 polished components with animations, glassmorphism, and proper UX flow -- but they're stuck in a Next.js component format that doesn't run in the live Vite app.

**Priority actions:**
1. Fix CTAs immediately (30 min) -- unblock ANY conversion
2. Add Tailwind to the Vite project (2 hrs)
3. Port the 6 existing components (1 day)
4. Add product ecosystem hub section (0.5 day)
5. Add social proof + trust signals (0.5 day)

**Expected impact:** Going from 8/50 to 35/50+ would make this a credible SaaS landing page capable of converting visitors into paying customers.

---

## Unresolved Questions

1. **Which pricing is canonical?** App.tsx shows 4 tiers ($0/$29/$99/$199), components show 3 tiers ($0/$49/custom), CLAUDE.md shows ($49/$149/$499). Need business decision.
2. **Is Polar checkout currently configured?** `pricing-table.tsx` references `NEXT_PUBLIC_POLAR_PRICE_PRO` env var. Is this set up on Polar.sh?
3. **Should the landing stay on Vite or migrate to Next.js?** The component library assumes Next.js. Migrating would enable code sharing with `raas.agencyos.network`.
4. **What real metrics exist for social proof?** Number of missions completed, API calls, GitHub stars, npm downloads -- need actual data.
5. **Is the `/v1/tenants/signup` endpoint stable for production traffic?** Need to verify before routing CTAs to it.
6. **Target audience:** Is this page for developers (CLI users), business owners (service buyers), or enterprises (platform customers)? Copy strategy depends on this.
