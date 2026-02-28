# Phase 01: Vibe SDK Packaging — Agency-in-a-Box

## Context Links

- Research: [CRO + SDK Packaging](./research/researcher-01-cro-sdk-packaging.md)
- WellNexus source: `apps/well/`
- AgencyOS Web: `apps/agencyos-web/`
- GoHighLevel Snapshot model reference (researcher-01)

## Overview

- **Priority:** P1
- **Status:** pending
- **Effort:** 1 week
- **Description:** Bien WellNexus (Aura Elite design) thanh SDK co the scaffold, theme, va deploy bang 1 lenh. Mo hinh GoHighLevel Snapshot cho F&B vertical.

## Key Insights

- GoHighLevel solo consultant: white-label + niche snapshots = $12K MRR, zero staff
- Vercel template pattern: git repo + vercel.json + env schema + deploy button
- SEA F&B gap: khong co player nao co AI-agent + white-label → co hoi lon
- Theming 3 lop: CSS custom properties > Tailwind config > hard-coded values
- t3-env/Zod validate env tai build time → client khong bao gio thieu var

## Requirements

### Functional
- [ ] CLI tool `npx create-agencyos-app --template f&b --client <name>`
- [ ] Theming system: brand tokens (colors, fonts, logo, border-radius)
- [ ] Env schema validation (Zod/t3-env) — fail build neu thieu var
- [ ] Vercel Deploy Button trong README
- [ ] Pre-seeded Supabase migrations
- [ ] Client config file (name, domain, locale, payment keys)
- [ ] i18n scaffold (vi/en default)

### Non-Functional
- [ ] Scaffold time < 30s
- [ ] Deploy time (Vercel) < 3min
- [ ] Zero manual config cho basic setup
- [ ] Docs: README + SETUP_GUIDE

## Architecture

```
create-agencyos-app CLI
├── templates/
│   ├── f-and-b/              ← Clone tu WellNexus
│   │   ├── theme.config.ts   ← CSS custom properties + Tailwind extend
│   │   ├── client.config.ts  ← Name, domain, locale, Polar keys
│   │   ├── .env.example      ← Annotated env vars
│   │   ├── supabase/
│   │   │   └── migrations/   ← Pre-seeded schema (menu, orders, staff)
│   │   └── vercel.json       ← Deploy config
│   ├── saas-dashboard/       ← Future: agencyos-web template
│   └── landing-page/         ← Future: agencyos-landing template
├── src/
│   ├── cli.ts                ← Typer-style CLI (prompts, flags)
│   ├── scaffold.ts           ← Git clone + variable replacement
│   ├── theme-generator.ts    ← Generate CSS vars tu brand config
│   └── env-validator.ts      ← Zod schema validation
└── package.json              ← Publish to npm as @agencyos/create-app
```

### Theming System

```
Layer 1: CSS Custom Properties (runtime)
  --aura-primary: #6366f1;
  --aura-glass-bg: rgba(255,255,255,0.08);
  --aura-blur: 12px;

Layer 2: Tailwind Config (build-time)
  theme.extend.colors.primary: 'var(--aura-primary)'

Layer 3: theme.config.ts (user-facing)
  export const theme = {
    primary: '#6366f1',
    glassBg: 'rgba(255,255,255,0.08)',
    blur: '12px',
    fonts: { heading: 'Inter', body: 'Inter' },
    borderRadius: '16px',
  }
```

## Related Code Files

### Files to Modify
- `apps/well/` — Extract theme tokens ra `theme.config.ts`
- `apps/well/tailwind.config.ts` — Reference CSS custom properties
- `apps/well/src/` — Replace hardcoded colors voi CSS vars

### Files to Create
<!-- Updated: Validation Session 1 - Template dung git submodule thay vi static copy -->
- `packages/create-agencyos-app/` — CLI package moi
- `packages/create-agencyos-app/src/cli.ts`
- `packages/create-agencyos-app/src/scaffold.ts` — Dung git submodule add thay vi copy
- `packages/create-agencyos-app/src/theme-generator.ts`
- `packages/create-agencyos-app/templates/f-and-b/` — Git submodule link toi WellNexus repo
- `packages/create-agencyos-app/templates/f-and-b/theme.config.ts`
- `packages/create-agencyos-app/templates/f-and-b/client.config.ts`
- `packages/create-agencyos-app/templates/f-and-b/.env.example`
- `packages/create-agencyos-app/templates/f-and-b/vercel.json`

## Implementation Steps

1. **Extract theme tokens tu WellNexus**
   - Grep tat ca hardcoded colors, fonts, border-radius trong `apps/well/src/`
   - Tao `theme.config.ts` voi tat ca tokens
   - Replace hardcoded values bang CSS custom properties

2. **Tao env schema**
   - Liet ke tat ca env vars tu `apps/well/.env.example`
   - Tao Zod schema validate tai build time
   - Tich hop t3-env vao `apps/well/`

3. **Tao CLI scaffold tool**
   - Init `packages/create-agencyos-app/`
   - Implement `cli.ts`: interactive prompts (client name, domain, brand colors)
   - Implement `scaffold.ts`: git clone template + replace variables
   - Implement `theme-generator.ts`: generate CSS tu brand config

4. **Tao F&B template**
   - Copy WellNexus vao `templates/f-and-b/`
   - Add pre-seeded Supabase migrations (menu_items, orders, staff)
   - Add `vercel.json` voi deploy config
   - Add `client.config.ts` template

5. **Vercel Deploy Button**
   - Tao deploy URL voi env var prompts
   - Add badge vao README

6. **Test end-to-end**
   - `npx create-agencyos-app --template f&b --client test-restaurant`
   - Verify scaffold output
   - Deploy to Vercel preview
   - Verify theme customization

## Todo List

- [ ] Grep + extract theme tokens tu WellNexus
- [ ] Tao `theme.config.ts` schema
- [ ] Tao Zod env validation
- [ ] Init `packages/create-agencyos-app/`
- [ ] Implement CLI voi interactive prompts
- [ ] Implement scaffold engine
- [ ] Implement theme generator
- [ ] Tao F&B template tu WellNexus
- [ ] Tao Supabase seed migrations
- [ ] Tao Vercel deploy button
- [ ] Write README + SETUP_GUIDE
- [ ] Test scaffold → deploy flow
- [ ] Publish to npm (beta)

## Success Criteria

- `npx create-agencyos-app` chay thanh cong, scaffold < 30s
- Deploy button dua len Vercel < 3min
- Theme customization (doi mau, font) phan anh dung
- Env validation block build khi thieu var
- i18n (vi/en) hoat dong out of the box

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| WellNexus hardcoded values qua nhieu | Cham extract | Grep systematic, lam theo component |
| Template outdated nhanh | Maintenance burden | Git submodule link, khong copy static |
| Supabase migrations conflict | Client setup fail | Version migrations, idempotent SQL |
| npm package naming conflict | Publish fail | Check `@agencyos/create-app` availability |

## Security Considerations

- `.env.example` KHONG chua real keys — chi co placeholders
- Zod validate env tai build → khong deploy voi thieu secrets
- Template KHONG bundle API keys — client tu fill
- Supabase RLS enabled trong seed migrations
- `vercel.json` khong expose internal routes

## Next Steps

- Phase 2 (CRO): Landing page cua SDK cung can CRO
- Pricing page cho SDK tren agencyos-landing
- GoHighLevel Snapshot model: tao pre-configured workflows per vertical
- Partner program: agency re-sell SDK voi custom branding

## Unresolved Questions

1. WellNexus hien tai co bao nhieu hardcoded colors/fonts? (can grep audit)
2. `packages/` directory da co monorepo config (turborepo/nx) chua?
3. Supabase project cua WellNexus — schema hien tai nhu the nao?
4. npm org `@agencyos` da register chua?
5. Template nen dung git clone hay degit (lighter)?
