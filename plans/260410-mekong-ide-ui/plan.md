---
title: "Mekong IDE Web App — VS Code-style Browser IDE"
description: "8-screen IDE UI with design system, agent chat, engine monitor, task tracker, trading view"
status: pending
priority: P1
effort: 32h
branch: feat/mekong-ide-ui
tags: [ide, ui, next15, react19, tailwind4, cloudflare]
created: 2026-04-10
---

# Mekong IDE Web App

VS Code-style IDE in the browser. 8 screens from pencil.dev design (586 components). Next.js 15 + React 19 + Tailwind v4. Static export to CF Pages.

## Architecture

- **App location:** `apps/mekong-ide/` (new Next.js 15 app in monorepo)
- **Design system:** `components/ds/` — tokens, primitives, composites
- **Screens:** `components/screens/` — 1 component per screen
- **Routes:** `app/(ide)/` — each screen = 1 route
- **API:** gateway at `localhost:8000` or `api.mekongmind.com`
- **Deploy:** CF Pages static export via `next.config.ts` `output: 'export'`

## Phases

| # | Phase | Effort | Status | File |
|---|-------|--------|--------|------|
| 1 | Scaffold + Design Tokens + DS Components | 6h | pending | [phase-01](phase-01-scaffold-design-system.md) |
| 2 | Main IDE Layout (Screen 1 — core shell) | 5h | pending | [phase-02](phase-02-main-ide-layout.md) |
| 3 | Agent Chat + Tool Execution Panels | 4h | pending | [phase-03](phase-03-agent-chat-tools.md) |
| 4 | Engine Farm Monitor + Context Visualizer | 4h | pending | [phase-04](phase-04-engine-farm-context.md) |
| 5 | Task Tracker + CashClaw Trading | 4h | pending | [phase-05](phase-05-task-tracker-trading.md) |
| 6 | Navigation (Top Bar + Cmd+K Palette) | 3h | pending | [phase-06](phase-06-navigation.md) |
| 7 | Wire to Gateway API | 4h | pending | [phase-07](phase-07-gateway-api.md) |
| 8 | Build + Deploy to CF Pages | 2h | pending | [phase-08](phase-08-build-deploy.md) |

## Key Constraints

- Each file < 200 lines, kebab-case naming
- No external UI library — custom DS from .pen file
- 22 design tokens mapped to CSS variables + Tailwind v4
- Desktop only (1440px min), no mobile responsive
- MIT license, original code
- Gateway API connection via env var `NEXT_PUBLIC_API_URL`

## Dependencies

- pnpm workspace already configured for `apps/*`
- Turbo build pipeline in place
- lucide-react for icons (already used in dashboard)
- Tailwind v4 (new — dashboard uses older version)
