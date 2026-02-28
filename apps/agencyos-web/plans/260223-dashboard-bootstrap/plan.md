# AgencyOS Web — Dashboard Bootstrap Plan

**Date:** 2026-02-23
**Priority:** CRITICAL
**Status:** In Progress

## Objective
Bootstrap the `/dashboard` route for agencyos-web — the RaaS command center.
Middleware already redirects auth correctly; dashboard pages are completely missing.

## Stack
- Next.js 16 App Router + TypeScript + Tailwind CSS v4
- Supabase Auth (SSR client already set up)
- shadcn/ui components (button, card, avatar, etc. already installed)
- Dark theme: black/zinc-900/purple gradient (matching landing page)

## Phases

| Phase | File | Status |
|-------|------|--------|
| [Phase 1](phase-01-dashboard-core.md) | Dashboard layout + overview + missions + agents + auth callback | 🔄 In Progress |
| [Phase 2](phase-02-revenue-settings.md) | Revenue page + Settings page + logout action | ⏳ Pending |
| [Phase 3](phase-03-build-verify.md) | TypeScript build verify + lint fix | ⏳ Pending |

## File Limit Rule
MAX 5 files per mission. Report remaining if more needed.

## Mission 1 Files (5 max)
1. `app/dashboard/layout.tsx` — sidebar + header
2. `app/dashboard/page.tsx` — overview stats
3. `app/dashboard/missions/page.tsx` — missions table
4. `app/dashboard/agents/page.tsx` — agent cards
5. `app/auth/callback/route.ts` — Supabase OAuth callback

## Mission 2 Files (planned)
- `app/dashboard/revenue/page.tsx`
- `app/dashboard/settings/page.tsx`
- `app/actions/auth.ts` — server action for logout

## Success Criteria
- `pnpm build` exits 0
- `/dashboard` redirects to login when unauthenticated
- All pages render without runtime errors
- Dark theme consistent across all pages
