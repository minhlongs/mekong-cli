---
phase: 1
title: "Scaffold + Design Tokens + Design System Components"
status: completed
effort: 6h
completed: 2026-04-10
---

# Phase 1: Scaffold + Design Tokens + Design System

## Context
- [pencil.dev design](/Users/macbook/mekong-ide-core/untitled.pen) — 586 components, 22 tokens
- [Dashboard app](../../apps/dashboard/) — reference for Next.js patterns in this monorepo
- [pnpm-workspace.yaml](../../pnpm-workspace.yaml) — `apps/*` already included

## Overview
Bootstrap Next.js 15 app with Tailwind v4, map all 22 design tokens, build atomic DS components matching .pen file.

## Files to Create

```
apps/mekong-ide/
├── package.json
├── next.config.ts                     # output: 'export', static
├── tsconfig.json
├── tailwind.config.ts                 # v4 with CSS variable tokens
├── postcss.config.mjs
├── eslint.config.mjs
├── app/
│   ├── layout.tsx                     # Root layout, font loading, token CSS vars
│   ├── page.tsx                       # Redirect to /ide
│   └── globals.css                    # @theme with 22 design tokens as CSS vars
├── components/
│   └── ds/
│       ├── design-tokens.css          # Token definitions (CSS custom properties)
│       ├── button.tsx                  # primary/secondary/danger/ghost variants
│       ├── badge.tsx                   # Status badges (success/warning/danger/info)
│       ├── input.tsx                   # Text input with label + error state
│       ├── card.tsx                    # Surface card with hover/active states
│       ├── code-block.tsx             # Syntax-highlighted code display
│       ├── progress-bar.tsx           # Horizontal progress with label
│       ├── data-table.tsx             # Simple table component
│       ├── toast.tsx                  # Toast notification overlay
│       ├── sidebar.tsx                # Collapsible sidebar shell
│       ├── icon-button.tsx            # Icon-only button (lucide icons)
│       └── index.ts                   # Barrel export
└── lib/
    └── types.ts                       # Shared TypeScript types
```

## Design Tokens (22 total)

Map to CSS custom properties in `globals.css`:

```css
:root {
  /* Backgrounds */
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-tertiary: #21262d;

  /* Surfaces */
  --surface-card: #1c2128;
  --surface-hover: #262c36;
  --surface-active: #2d333b;

  /* Text */
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-muted: #484f58;

  /* Borders */
  --border-subtle: #21262d;
  --border-strong: #30363d;

  /* Accent (Teal) */
  --accent-teal-400: #2dd4bf;
  --accent-teal-500: #14b8a6;
  --accent-teal-600: #0d9488;

  /* Status */
  --status-success: #3fb950;
  --status-warning: #d29922;
  --status-danger: #f85149;
  --status-info: #58a6ff;

  /* Model Colors */
  --model-architect: #bc8cff;
  --model-reasoning: #58a6ff;
  --model-audit: #f0883e;
  --model-trading: #3fb950;
}
```

Tailwind v4 maps these via `@theme` directive in `globals.css`.

## Implementation Steps

1. **Scaffold Next.js 15 app**
   ```bash
   cd apps && pnpm create next-app mekong-ide --typescript --tailwind --eslint --app --no-src-dir
   ```
   Then adjust `package.json`: name=`mekong-ide`, add `lucide-react`, `clsx`

2. **Configure Tailwind v4** — use `@theme` in globals.css to expose tokens as utilities (`bg-bg-primary`, `text-text-primary`, etc.)

3. **Configure Next.js for static export** — `next.config.ts`:
   ```ts
   const config: NextConfig = {
     output: 'export',
     images: { unoptimized: true },
   }
   ```

4. **Create design-tokens.css** — all 22 tokens as CSS custom properties

5. **Build DS components** (each < 200 lines):
   - `button.tsx` — 4 variants (primary/secondary/danger/ghost), sizes sm/md/lg
   - `badge.tsx` — status variants mapping to `--status-*` tokens
   - `input.tsx` — label, placeholder, error message, disabled state
   - `card.tsx` — uses `--surface-card`, hover/active states
   - `code-block.tsx` — monospace, line numbers, copy button
   - `progress-bar.tsx` — percentage, color by status
   - `data-table.tsx` — headers + rows, sortable prop
   - `toast.tsx` — success/error/info, auto-dismiss, stack
   - `sidebar.tsx` — 48px collapsed, expand on hover, icon slots
   - `icon-button.tsx` — wraps lucide icon in button with tooltip

6. **Create barrel export** `components/ds/index.ts`

7. **Verify build** — `cd apps/mekong-ide && pnpm build`

## Success Criteria
- [x] `npm build` produces static export in `out/` (used npm --no-workspaces due to bun workspace conflict)
- [x] All 22 tokens accessible as Tailwind utilities via @theme + CSS custom properties
- [x] All DS components render without errors (build passes)
- [x] Each file < 200 lines (max: code-block.tsx at 100 lines)
- [x] No `any` types (tsc --noEmit: 0 errors)

## Risk Assessment
- Tailwind v4 `@theme` syntax differs from v3 `extend` — verify docs
- Next.js 15 static export may have quirks with app router — test early
