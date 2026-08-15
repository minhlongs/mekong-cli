# @mekong/tokens

Design token system for the Mekong CLI design system. Single source of truth for colors, typography, spacing, and motion — all in OKLCH color space with Tailwind v4 `@theme` directive.

## Usage

```css
@import "@mekong/tokens/tokens.css";
@import "@mekong/tokens/semantic.css";
```

## Color Scales

### Brand (Mekong Blue, hue 240)

| Token | OKLCH | Usage |
|-------|-------|-------|
| `--color-brand-50` | `oklch(0.97 0.01 240)` | Lightest tint |
| `--color-brand-100` | `oklch(0.93 0.03 240)` | Hover bg |
| `--color-brand-200` | `oklch(0.86 0.06 240)` | Selected bg |
| `--color-brand-300` | `oklch(0.76 0.10 240)` | Borders |
| `--color-brand-400` | `oklch(0.66 0.14 240)` | Dark mode accent |
| `--color-brand-500` | `oklch(0.56 0.17 240)` | **Primary** |
| `--color-brand-600` | `oklch(0.48 0.16 240)` | Hover |
| `--color-brand-700` | `oklch(0.40 0.14 240)` | Active |
| `--color-brand-800` | `oklch(0.33 0.11 240)` | Dark surfaces |
| `--color-brand-900` | `oklch(0.26 0.08 240)` | Darkest |
| `--color-brand-950` | `oklch(0.18 0.05 240)` | Near-black |

### Status Colors

| Token | Usage |
|-------|-------|
| `--color-success-500/600` | Green — success states |
| `--color-warning-500/600` | Amber — warnings |
| `--color-danger-500/600` | Red — errors, destructive |
| `--color-info-500/600` | Blue — informational |

### Trading Colors

| Token | Usage |
|-------|-------|
| `--color-gain` | Green — profit |
| `--color-loss` | Red — loss |
| `--color-bid` | Green — buy side |
| `--color-ask` | Red — sell side |

### Chart Categorical (equal perceptual brightness L=0.60)

`--color-chart-1` through `--color-chart-8`: Blue, Green, Red, Amber, Purple, Teal, Orange, Pink.

## Typography

| Token | Size | Px |
|-------|------|----|
| `--font-size-xs` | 0.75rem | 12 |
| `--font-size-sm` | 0.875rem | 14 |
| `--font-size-base` | 1rem | 16 |
| `--font-size-lg` | 1.125rem | 18 |
| `--font-size-xl` | 1.25rem | 20 |
| `--font-size-2xl` | 1.5rem | 24 |
| `--font-size-3xl` | 1.875rem | 30 |
| `--font-size-4xl` | 2.25rem | 36 |
| `--font-size-hero` | `clamp(2.5rem, 5vw + 1rem, 4.5rem)` | Responsive |

Fonts: `--font-sans` (Geist), `--font-mono` (Geist Mono).

## Spacing (8px grid)

`--spacing-1` (4px) through `--spacing-24` (96px).

## Motion

| Token | Duration |
|-------|----------|
| `--duration-fast` | 100ms |
| `--duration-normal` | 200ms |
| `--duration-slow` | 300ms |
| `--duration-slower` | 500ms |

Easings: `--ease-out` (decelerate), `--ease-spring` (overshoot).

## Semantic Layer (`semantic.css`)

Maps tokens to semantic roles. Auto-flips for `.dark` / `[data-theme="dark"]`.

| Semantic Var | Light | Dark |
|-------------|-------|------|
| `--bg-primary` | neutral-50 | neutral-950 |
| `--text-primary` | neutral-950 | neutral-50 |
| `--accent` | brand-500 | brand-500 |
| `--border-default` | neutral-200 | neutral-800 |

Trading surface `[data-surface="trading"]` uses fixed dark palette.
