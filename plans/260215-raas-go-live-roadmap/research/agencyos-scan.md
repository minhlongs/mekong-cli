# Research Report: AgencyOS Landing & Web Scan

## 1. AgencyOS Landing Page (`apps/agencyos-landing`)

### Build Status
- **Framework**: Next.js 16.1.6, React 19.2.3.
- **Scripts**: `dev`, `build`, `start`, `lint`, `typecheck`, `test` (vitest).
- **Quality**: Uses Turbopack, React Compiler, and Vitest.
- **Readiness**: High. Build configuration is modern and optimized.

### Deploy Configuration
- **Vercel**: `vercel.json` present with security headers and CSP.
- **Docker**: `Dockerfile` present (standalone output mode).
- **Environment**: Requires `NEXT_PUBLIC_POLAR_PRICE_*` vars for checkout.

### Features & Gaps
- **Payments**: Integrated with Polar.sh. Standard checkouts for Starter/Pro/Enterprise.
- **I18n**: Full support via `next-intl` (`[locale]` routing).
- **Animations**: Framer Motion + Lenis smooth scroll.
- **Missing**:
  - Verification of all legal pages (Privacy/Terms).
  - Specific agent ecosystem details in some sections (placeholder content).

---

## 2. AgencyOS Web Dashboard (`apps/agencyos-web`)

### Build Status
- **Framework**: Next.js 16.1.6, React 19.2.3.
- **Scripts**: `dev`, `build`, `start`, `lint`.
- **Quality**: Uses Supabase SSR, Shadcn/UI, Tailwind 4.
- **Readiness**: Moderate. Lacks a visible `test` script in `package.json` despite having testing dependencies.

### Deploy Configuration
- **Status**: Standard Vercel auto-deploy suspected (no `vercel.json` found, uses standard Next.js build).
- **Auth**: Supabase Auth integration.

### Features & Gaps
- **Core**: Auth (Login/Register), Dashboard Layout.
- **Routes Found**:
  - `/auth/login`
  - `/auth/register` (implied by layout)
  - `/dashboard` (implied, checking...)
- **Missing**:
  - `WithdrawalPage` and `NetworkPage` mentioned in `CLAUDE.md` need verification in `app/` structure.
  - Test suite needs to be wired up in `scripts`.
  - Content for specific agent management tools.

---

## 3. WellNexus (`apps/wellnexus`)

### Status
- **Discovery**: Current directory contains BMAD planning artifacts (PRDs, Workflows).
- **Implementation**: The actual codebase appears to be symlinked to `/Users/macbookprom1/Well`.
- **Roadmap Note**: Need to treat this as a "Planning-First" project or follow the symlink for implementation scan.

---

## Priority Order (Go-Live)

1. **84tea**: Production-ready. Immediate go-live.
2. **AgencyOS Landing**: High priority for marketing and acquisition.
3. **Anima119**: High priority for rebranding/launching new vertical.
4. **AgencyOS Web**: Essential for post-purchase user management.
5. **WellNexus**: Research/Planning phase.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
