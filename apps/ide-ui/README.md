# @mekong/ide-ui

Mekong IDE marketing UI — 2-screen MVP (landing + Engineering dept).

**Stack:** Next.js 15 App Router · Tailwind 4 · MD3 tokens · Static export → CF Pages

## Screens

| Route | Description |
|---|---|
| `/` | Landing: hero, 3-feature grid, pricing with Polar buy buttons |
| `/departments/engineering` | 10 engineering commands with MCU costs |

## Setup

```bash
# From monorepo root
pnpm install

# Dev server (port 3010)
pnpm --filter @mekong/ide-ui dev

# Type check
pnpm --filter @mekong/ide-ui typecheck

# Build static export → ./out
pnpm --filter @mekong/ide-ui build
```

## Deploy to Cloudflare Pages

```bash
# Manual deploy
wrangler pages deploy out --project-name mekong-ide-ui

# Smoke test
curl -I https://mekong-ide-ui.pages.dev
```

## Design System

Uses MD3 (Material Design 3) tokens from `styles/md3-tokens.css`.
No raw Tailwind colors — always use `var(--md-sys-color-*)` and `var(--md-sys-shape-*)`.

See `.claude/rules/m3-strict.md` for full token rules.

## File size rule

All files capped at 180 LOC (split at 170). See `CLAUDE.md`.
