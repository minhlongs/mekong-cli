---
description: "Scaffold new RaaS project — generates full Next.js SaaS with auth, billing, dashboard. 1 command, ~15 min."
argument-hint: [project-name --type saas --stack next+cf]
allowed-tools: Read, Write, Bash, Task
---

# /raas:scaffold — Generate RaaS SaaS Project

## Engine command

```bash
mekong raas scaffold $ARGUMENTS
```

## Fallback (if engine not ready)

Generate a full Next.js SaaS project in apps/{project-name}/:

1. Run: `bash mekong/infra/scaffold.sh {project-name} startup`
2. Create src/ directory structure:
   - `app/layout.tsx` (root layout with Tailwind)
   - `app/page.tsx` (landing page with hero, features, pricing)
   - `app/dashboard/page.tsx` (protected dashboard)
   - `app/api/auth/route.ts` (auth endpoint)
   - `app/api/billing/route.ts` (billing webhook — Polar.sh only)
   - `components/hero.tsx`
   - `components/pricing.tsx`
   - `components/dashboard-stats.tsx`
   - `lib/auth.ts`
   - `lib/billing.ts`
3. Install deps: `cd apps/{project-name} && pnpm install`
4. First build: `pnpm build`
5. Git commit: `feat: scaffold {project-name} RaaS SaaS`

## Output

```
RaaS Project Scaffolded: {project-name}
  app/page.tsx              <- Landing page
  app/dashboard/page.tsx    <- Dashboard
  app/api/auth/route.ts     <- Auth
  app/api/billing/route.ts  <- Billing (Polar.sh)
  components/               <- UI components
  lib/                      <- Business logic

Next: /cook "{project-name}: build core features"
```

## CRITICAL

This command creates ACTUAL CODE in apps/{project-name}/src/.
NOT reports. NOT analysis. Working TypeScript code.

## Goal context

<goal>$ARGUMENTS</goal>
