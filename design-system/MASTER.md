# Design System Master File — Mekong Platform: Cyber-Bento Horizon

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Mekong Cyber-Bento Horizon
**Theme:** Cyber-Bento Horizon (Obsidian Void `#090A0F`, Slate `#11131A`, Emerald `#10B981`, Cyan `#06B6D4`)
**Architecture:** Multi-Page Static Edge Delivery (Cloudflare Pages) + React 18 SPA (`/app/`) + Cloudflare Pages Edge Worker API (`_worker.js`)
**Standards:** WCAG 2.1 AA Accessible, Tabular Numerals, 44×44px Touch Targets, Zero Structural Emojis (Vector SVG Only).

---

## 1. Global Color Palette

| Token | Hex | CSS Variable | Semantic Usage |
|---|---|---|---|
| Obsidian Void | `#090A0F` | `--bg-app` / `--color-background` | Global app canvas, deep space void |
| Elevated Slate | `#11131A` | `--bg-panel` / `--color-surface` | Bento cards, navigation shells, modals |
| Hover Slate | `#181B26` | `--bg-hover` | Table row hover, button ghost states |
| Border Subtle | `#1E2230` | `--border-subtle` | 1px structural bento grid lines |
| Border Active | `#2D3748` | `--border-active` | Focused, active, and highlighted borders |
| Neon Emerald | `#10B981` | `--color-primary` | Active agent signals, verified stamps, CTAs |
| Electric Cyan | `#06B6D4` | `--color-secondary` | Interactive triggers, telemetry, code snippets |
| Amber Warning | `#F59E0B` | `--color-warning` | Quota thresholds, pending states, MCU burn |
| Crimson Interlock | `#EF4444` | `--color-error` | Destructive actions, interlocks, alerts |
| Text Primary | `#F9FAFB` | `--text-primary` | Headings, active values, high-contrast labels |
| Text Secondary | `#9CA3AF` | `--text-secondary` | Body copy, secondary metrics, subtitles |
| Text Muted | `#64748B` | `--text-muted` | Metadata, timestamps, structural hints |

---

## 2. Typography & Numerical Precision

- **Headings Font:** `Space Grotesk`, `-apple-system`, sans-serif (Font weights: 600, 700; Tracking: -0.02em)
- **Body & UI Font:** `Plus Jakarta Sans`, `Inter`, sans-serif (13px–15px; Line-height: 1.5)
- **Telemetry, Hashes & Code:** `JetBrains Mono`, monospace (SHA-256 hashes, terminal commands, VND/MCU pricing)
- **Tabular Numerals (MANDATORY):**
  ```css
  font-variant-numeric: tabular-nums;
  font-feature-settings: 'tnum' on, 'zero' on;
  ```
  All financial amounts (VND, USD, MCU), counters, timestamps, latency metrics, and cryptographic hashes MUST use tabular numerals to prevent layout shift during updates.

---

## 3. Radii, Hit Areas & Surface Elevation

- **Bento Cards & Panels:** `12px` (`--radius-card`)
- **Buttons, Inputs & Selectors:** `8px` (`--radius-btn`)
- **Pills & Status Badges:** `9999px` (`--radius-pill`)
- **Touch Targets (MANDATORY):**
  ```css
  min-height: 44px;
  min-width: 44px;
  ```
  All interactive controls, buttons, links, search triggers, and modal dismissals must provide a minimum 44×44px hit area per WCAG 2.1 AA standards.

---

## 4. Vector-Only Iconography (Zero Structural Emojis)

- **Strict Ban:** No structural emoji icons (`🌐`, `💳`, `🖥️`, `⚡`, `🛡️`, `🔍`, `📊`, `🤖`, `🧪`, `🏛️`, `🏦`, `🚀`, etc.) in production navigation, cards, or palettes.
- **Icon Standard:** Inline crisp SVG vector icons:
  ```html
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <!-- Lucide/Heroicon Path -->
  </svg>
  ```
- **Icon Sizing:**
  - Navigation / Inline: `16×16px` (stroke: 1.75px)
  - Bento Header Badge: `20×20px` (stroke: 1.75px)
  - Hero / Feature Featurette: `24×24px` (stroke: 2px)

---

## 5. Micro-Interactions & Reduced Motion (stitch-animate)

```css
/* Bento Hover Lift */
.bento-card, [class*="rounded-xl"] {
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1),
              border-color 0.2s ease;
}
.bento-card:hover, [class*="rounded-xl"]:hover {
  transform: translateY(-2px);
  border-color: var(--border-active);
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.7), 0 0 16px -2px rgba(16, 185, 129, 0.2);
}

/* Reduced Motion Override */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 6. Pre-Delivery Checklist (ak-ui-ux-pro-max)

- [x] Zero structural emojis used as iconography (all replaced with vector SVGs).
- [x] All interactive targets meet or exceed 44×44px hit areas.
- [x] Tabular numerals applied to all metrics, telemetry, timestamps, and currency (`font-variant-numeric: tabular-nums`).
- [x] High-contrast 2px emerald focus-visible outline with 2px offset (`:focus-visible`).
- [x] Skip-to-content bypass link (`#skip-to-content`) present in DOM for keyboard navigation.
- [x] Responsive layout tested for 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide) with zero horizontal overflow.
- [x] Strict Cloudflare Pages edge delivery — zero Vercel dependencies or artifacts.
