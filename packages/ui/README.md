# @mekong/ui

Shared React component library for the Mekong design system. Built with CVA, Tailwind v4, and semantic CSS variables.

## Usage

```tsx
import { Button } from "@mekong/ui/button";
import { Badge } from "@mekong/ui/badge";
import "@mekong/ui/globals.css";
```

## Core Components

### Button
```tsx
import { Button } from "@mekong/ui/button";
```
| Prop | Type | Default |
|------|------|---------|
| `variant` | `"default" \| "secondary" \| "ghost" \| "danger"` | `"default"` |
| `size` | `"sm" \| "md" \| "lg"` | `"md"` |

### Badge
```tsx
import { Badge } from "@mekong/ui/badge";
```
| Prop | Type | Default |
|------|------|---------|
| `variant` | `"idle" \| "running" \| "success" \| "failed" \| "warning" \| "gain" \| "loss"` | `"idle"` |

### Card
```tsx
import { Card, CardHeader, CardContent, CardFooter } from "@mekong/ui/card";
```
| Prop | Type | Default |
|------|------|---------|
| `variant` | `"default" \| "elevated" \| "bordered"` | `"default"` |

### Input
```tsx
import { Input } from "@mekong/ui/input";
```
| Prop | Type | Default |
|------|------|---------|
| `label` | `string` | — |
| `error` | `string` | — |
| `icon` | `ReactNode` | — |

### Kbd
```tsx
import { Kbd } from "@mekong/ui/kbd";
// <Kbd>⌘K</Kbd>
```

### StatusDot
```tsx
import { StatusDot } from "@mekong/ui/status-dot";
```
| Prop | Type | Default |
|------|------|---------|
| `status` | `"online" \| "degraded" \| "error" \| "offline"` | `"offline"` |
| `pulse` | `boolean` | `false` |

### Skeleton
```tsx
import { Skeleton } from "@mekong/ui/skeleton";
// <Skeleton className="h-4 w-32" />
```

### CodeBlock
```tsx
import { CodeBlock } from "@mekong/ui/code-block";
```
| Prop | Type | Default |
|------|------|---------|
| `code` | `string` | — |
| `language` | `string` | `"bash"` |
| `showCopy` | `boolean` | `true` |

### CreditMeter
```tsx
import { CreditMeter } from "@mekong/ui/credit-meter";
```
| Prop | Type |
|------|------|
| `used` | `number` |
| `total` | `number` |
| `label` | `string` |

### KpiCard
```tsx
import { KpiCard } from "@mekong/ui/kpi-card";
```
| Prop | Type |
|------|------|
| `label` | `string` |
| `value` | `string \| number` |
| `trend` | `"up" \| "down" \| "flat"` |
| `trendValue` | `string` |
| `sparkline` | `ReactNode` |

### PipelineBadge
```tsx
import { PipelineBadge } from "@mekong/ui/pipeline-badge";
```
| Prop | Type | Default |
|------|------|---------|
| `phase` | `"plan" \| "execute" \| "verify"` | `"plan"` |
| `active` | `boolean` | `false` |

## Surface Components

### Trading (`@mekong/ui/trading/*`)
- **PriceDisplay** — Mono number with gain/loss coloring + flash animation
- **PositionCard** — Market question, probability, P&L
- **OrderBook** — Bid/ask rows with depth bars
- **ActivityFeed** — Bot action log
- **BotStatus** — Status dot + uptime + strategy
- **ProbabilityChart** — SVG line chart

### Dashboard (`@mekong/ui/dashboard/*`)
- **MissionCard** — Task status, credits, agent avatars
- **PipelineViz** — Plan/Execute/Verify step visualization
- **CreditGauge** — Radial gauge with tier label
- **AgentAvatar** — Colored circle with agent initial
- **CommandPalette** — Cmd+K modal with search

### Marketing (`@mekong/ui/marketing/*`)
- **TerminalDemo** — Animated typing terminal
- **HeroSection** — Centered hero with CTA buttons
- **FeatureBento** — Bento grid layout
- **PricingTable** — 4-tier pricing display
- **TrustBar** — GitHub stars, downloads, license
- **MekongMotif** — SVG delta branching pattern

### Brand (`@mekong/ui/brand/*`)
- **MekongLogo** — Abstract delta SVG logo
- **MekongWordmark** — "MEKONG" + subtitle text
- **DeltaPattern** — Repeating background pattern
- **LoadingRiver** — Animated loading indicator
