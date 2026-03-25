# Mekong Design System

The visual language of the Mekong CLI platform. Built for precision, depth, and flow.

## Design Principles

### 1. Flow
Like the Mekong River delta, information flows naturally from source to branches. Navigation follows predictable paths. Animations are fluid, never jarring.

### 2. Precision
Every pixel serves a purpose. Monospace numbers for data. Consistent spacing on an 8px grid. OKLCH colors for perceptual uniformity.

### 3. Depth
Layered surfaces communicate hierarchy. Semantic elevation through borders and shadows. Dark mode as a first-class citizen, not an afterthought.

### 4. Restraint
Minimal decoration. Content-first layouts. Color used sparingly for status and emphasis. Motion only where it aids comprehension.

### 5. Rootedness
Rooted in Vietnamese craft and the Mekong delta metaphor. The branching river pattern appears as a subtle motif throughout the system.

---

## Token Reference

### Colors

All colors use OKLCH for perceptual uniformity. The full scale is defined in `@mekong/tokens/tokens.css`.

- **Brand**: 11-stop blue scale (hue 240), primary at 500
- **Neutral**: 11-stop slate-tinted gray (hue 250)
- **Status**: success (green), warning (amber), danger (red), info (blue) at 500/600
- **Trading**: gain/loss/bid/ask for financial surfaces
- **Chart**: 8 categorical colors at equal L=0.60

### Typography

- **Sans**: Geist — clean, modern, geometric
- **Mono**: Geist Mono — code, numbers, data
- **Scale**: 12px to 60px + responsive hero size

### Spacing

8px base grid: 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px, 96px.

### Motion

| Speed | Duration | Use |
|-------|----------|-----|
| Fast | 100ms | Hover, focus |
| Normal | 200ms | Transitions |
| Slow | 300ms | Expand/collapse |
| Slower | 500ms | Page transitions |

Easings: `ease-out` for natural deceleration, `spring` for playful interactions.

---

## Component Catalog

### Core (11 components)
Button, Badge, Card, Input, Kbd, StatusDot, Skeleton, CodeBlock, CreditMeter, KpiCard, PipelineBadge.

### Trading (6 components)
PriceDisplay, PositionCard, OrderBook, ActivityFeed, BotStatus, ProbabilityChart.

### Dashboard (5 components)
MissionCard, PipelineViz, CreditGauge, AgentAvatar, CommandPalette.

### Marketing (6 components)
TerminalDemo, HeroSection, FeatureBento, PricingTable, TrustBar, MekongMotif.

### Brand (4 components)
MekongLogo, MekongWordmark, DeltaPattern, LoadingRiver.

**Total: 32 components**

---

## Surface Guidelines

### Dashboard Surface
Default light/dark theme. Use semantic variables (`--bg-primary`, `--text-primary`). Cards with borders, not shadows. Status colors for mission/agent states.

### Trading Surface
Always dark. Apply `data-surface="trading"` to the container. Monospace numbers everywhere. Gain/loss colors for P&L. Minimal borders — use subtle background differences.

### Marketing Surface
Light theme default. Large typography. Generous spacing. Hero sections with terminal demos. Bento grids for features. Delta pattern as subtle backgrounds.

---

## Dark Mode

The semantic layer (`semantic.css`) handles dark mode via `.dark` class or `[data-theme="dark"]` attribute. Rules:

1. Never hardcode light/dark colors — always use semantic vars
2. Borders get darker in dark mode (`neutral-800` vs `neutral-200`)
3. Accent colors stay consistent across modes
4. Text hierarchy inverts: primary becomes `neutral-50`, secondary becomes `neutral-400`
5. Trading surfaces ignore theme toggle — they are always dark

---

## Accessibility

1. All interactive elements have `focus-visible` ring styles
2. Color contrast meets WCAG 2.1 AA (4.5:1 text, 3:1 UI)
3. `prefers-reduced-motion` disables animations
4. All components support keyboard navigation
5. Status is never communicated by color alone — always paired with text or icons
