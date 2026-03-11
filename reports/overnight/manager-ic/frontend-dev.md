# Frontend Developer Report — Mekong CLI
*Role: Frontend Developer | Date: 2026-03-11*

---

## Frontend Architecture Overview

Mekong CLI has two frontend surfaces:

1. **Landing page** (`frontend/landing/`) — marketing site, static export
2. **Dashboard** (`agencyos.network`) — mission control UI, authenticated

Both deploy to Cloudflare Pages (zero cost, global CDN, git-push deploy).
Framework: Next.js with static export (`output: 'export'` in `next.config.js`).

---

## Next.js Static Export Pattern

CF Pages requires fully static output — no Node.js server at runtime.

```typescript
// next.config.js
const config = {
  output: 'export',          // Required for CF Pages
  trailingSlash: true,       // CF Pages prefers trailing slashes
  images: {
    unoptimized: true,       // No Next.js image optimization (static only)
  },
}
```

**Constraint:** No `getServerSideProps` — use `getStaticProps` or client-side
data fetching. API calls happen from browser → CF Worker edge API.

```typescript
// Pattern: client-side data fetch with SWR
import useSWR from 'swr'

export function MissionList() {
  const { data, error } = useSWR('/api/v1/missions', fetcher)
  if (error) return <ErrorState message={error.message} />
  if (!data) return <LoadingSkeleton rows={5} />
  return <MissionTable missions={data.missions} />
}
```

---

## MD3 Token System

All styling uses Material Design 3 design tokens. No hardcoded colors or spacing.

```typescript
// tokens/colors.ts — single source of truth
export const colors = {
  primary: 'var(--md-sys-color-primary)',           // #1565C0
  onPrimary: 'var(--md-sys-color-on-primary)',      // #FFFFFF
  primaryContainer: 'var(--md-sys-color-primary-container)', // #D3E4FF
  secondary: 'var(--md-sys-color-secondary)',       // #00897B
  tertiary: 'var(--md-sys-color-tertiary)',         // #F57F17
  surface: 'var(--md-sys-color-surface)',           // #FAFAFA
  background: 'var(--md-sys-color-background)',     // #FFFFFF
  error: 'var(--md-sys-color-error)',               // #B00020
} as const

// tokens/typography.ts
export const type = {
  displayLarge: { fontSize: '57px', lineHeight: '64px', fontWeight: 400 },
  headlineLarge: { fontSize: '32px', lineHeight: '40px', fontWeight: 400 },
  titleLarge: { fontSize: '22px', lineHeight: '28px', fontWeight: 500 },
  bodyLarge: { fontSize: '16px', lineHeight: '24px', fontWeight: 400 },
  labelLarge: { fontSize: '14px', lineHeight: '20px', fontWeight: 500 },
  code: { fontFamily: 'JetBrains Mono', fontSize: '14px', lineHeight: '20px' },
} as const
```

Rule: **Never** use raw hex values in component files. Always reference token variables.

---

## Component Patterns

### Loading State (required on all async)
```tsx
// components/mission-card-skeleton.tsx
export function MissionCardSkeleton() {
  return (
    <div className="animate-pulse rounded-lg bg-surface-variant p-4">
      <div className="h-4 bg-surface rounded w-3/4 mb-2" />
      <div className="h-3 bg-surface rounded w-1/2" />
    </div>
  )
}
```

### Error State (required on all fetches)
```tsx
// components/error-state.tsx
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-4 py-12 text-error">
      <AlertCircleIcon size={48} />
      <p className="text-body-large">{message}</p>
      {retry && <Button onClick={retry} variant="outlined">Try again</Button>}
    </div>
  )
}
```

### Empty State (required on all lists)
```tsx
// components/empty-missions.tsx
export function EmptyMissions() {
  return (
    <div className="flex flex-col items-center gap-4 py-16 text-on-surface-variant">
      <RocketIcon size={64} className="opacity-30" />
      <h3 className="text-headline-small">No missions yet</h3>
      <p className="text-body-large">Run your first: mekong cook "your goal"</p>
      <Button href="/docs/getting-started" variant="filled">Get started</Button>
    </div>
  )
}
```

---

## Landing Page Component Inventory

| Component | Status | Priority |
|-----------|--------|----------|
| `hero-section.tsx` | Needs GIF demo | P0 |
| `command-layer-diagram.tsx` | Missing | P0 |
| `pricing-cards.tsx` | Exists | P1 — link to Polar.sh |
| `llm-provider-strip.tsx` | Missing | P1 |
| `feature-grid.tsx` | Needs content | P1 |
| `github-stats-badge.tsx` | Missing | P2 |
| `testimonials.tsx` | Future | P3 |

---

## Dashboard Route Structure

```
/                     → Redirect to /dashboard
/dashboard            → Mission list (WAC north star)
/dashboard/mission/[id] → Mission detail + PEV timeline
/dashboard/credits    → Balance widget + usage history
/dashboard/settings   → LLM provider config + API key management
/docs                 → Embedded documentation
```

---

## Performance Standards

| Metric | Target | How to Achieve |
|--------|--------|----------------|
| LCP | < 2.5s | Static export + CF CDN edge |
| FCP | < 1.5s | Critical CSS inline |
| CLS | < 0.1 | Reserve space for async content |
| Bundle size | < 200KB gzipped | Dynamic imports for heavy components |
| Build time | < 30s | Next.js incremental compilation |

```typescript
// Dynamic import pattern for heavy components
const MermaidDiagram = dynamic(() => import('./mermaid-diagram'), {
  loading: () => <DiagramSkeleton />,
  ssr: false  // Client-only (Mermaid requires browser)
})
```

---

## Dark Theme Implementation

```css
/* globals.css — dark theme as primary */
:root {
  color-scheme: dark light;
}

@media (prefers-color-scheme: dark) {
  :root {
    --md-sys-color-background: #0A0A0A;
    --md-sys-color-surface: #121212;
    --md-sys-color-primary: #90CAF9;
    --md-sys-color-on-primary: #0D47A1;
  }
}
```

Rule: Design dark theme first — developer audience predominantly uses dark mode.

---

## Cloudflare Pages Deploy

```bash
# Automatic deploy on git push to main
git push origin main
# → GitHub Actions → npm run build → CF Pages picks up /out directory

# Local test
npm run build
npx wrangler pages dev out/
```

`wrangler.toml` for Pages:
```toml
name = "mekong-landing"
pages_build_output_dir = "out"
compatibility_date = "2026-03-01"
```

---

## Q2 Frontend Actions

- [ ] Add GIF/video demo of `mekong cook` to hero section above the fold
- [ ] Build `command-layer-diagram.tsx` — 5-layer visual (Founder→Ops)
- [ ] Build `llm-provider-strip.tsx` — logos: OpenRouter, DeepSeek, Ollama, Anthropic
- [ ] Implement loading skeletons for all async components
- [ ] Implement empty state for mission list
- [ ] Add GitHub stars badge to landing header
- [ ] Set up Lighthouse CI in GitHub Actions (enforce LCP < 2.5s)
