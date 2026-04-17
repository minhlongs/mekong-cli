# Frontend Engineering Department as a Service

> Replace a frontend team with AI agents that ship pixel-perfect UIs from Figma designs.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| 2 Frontend Engineers ($150k each) | $300,000/yr | $49/mo floor |
| Design tooling + licenses | $6,000/yr | Included |
| **Total replaced** | **$306,000/yr** | **~$2,400/yr** |

## What This Department Does

1. **UI Component Development** — Build components from Figma specs with proper props/variants
2. **Responsive Fixes** — Cross-browser, cross-breakpoint layout fixes
3. **Design System Integration** — Token implementation, Storybook, component library
4. **Page Implementation** — Full page builds with routing, data fetching, loading states
5. **Performance Optimization** — Bundle splitting, image optimization, Core Web Vitals

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| UI component from Figma | $12 |
| Responsive fix (all breakpoints) | $8 |
| Full page implementation | $20 |
| Design system token integration | $15 |
| Performance audit + fixes | $25 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong frontend-ui-build         # UI component from spec/Figma
mekong frontend-responsive-fix   # Responsive layout fix
mekong cook                      # Full feature implementation
mekong code                      # Code generation
mekong review                    # Code review
```

## Install

```bash
mekong install dept-engineering-frontend
```

## Configuration

```bash
# .mekong/.env.dept-engineering-frontend
DEPT_FE_FRAMEWORK=nextjs   # nextjs|remix|astro|react
DEPT_FE_STYLING=tailwind   # tailwind|css-modules|styled-components
DEPT_FE_FIGMA_TOKEN=your_figma_token
DEPT_FE_DEPLOY_TARGET=vercel  # vercel|cloudflare-pages
DEPT_FE_STORYBOOK=true
```
