# Design Lead Report — Mekong CLI
*Role: Design Lead | Date: 2026-03-11*

---

## Design System Overview

Mekong CLI spans two distinct design surfaces:

1. **Terminal UI (TUI)** — Rich-powered CLI output, developer-facing
2. **Web UI** — Next.js + Material Design 3 (MD3) token system, dashboard + landing

Both surfaces share a common brand language rooted in the Binh Pháp philosophy:
precise, purposeful, no decoration for its own sake.

---

## Terminal UI Design Principles

Built with Rich (Python). Current patterns:

```python
# Status output pattern
console.print("[green]✓[/green] Step completed: {step_name}")
console.print("[red]✗[/red] Step failed: {error}")
console.print("[yellow]⟳[/yellow] Executing: {step_name}")

# Progress pattern (PEV loop)
with Progress() as progress:
    task = progress.add_task("Planning...", total=3)
    # Plan → Execute → Verify
```

**Design rules for TUI:**
- Use semantic color only (green=success, red=error, yellow=in-progress, blue=info)
- Never use color for decoration — only for state communication
- `--verbose` flag unlocks detailed step output; default is summary only
- `--json` flag strips all Rich formatting for machine consumption
- Progress indicators required for any operation >2 seconds

### Rich Component Inventory
| Component | Usage | Status |
|-----------|-------|--------|
| `Progress` | PEV loop steps | Active |
| `Table` | Command listings, results | Active |
| `Panel` | Section headers | Active |
| `Syntax` | Code output highlighting | Active |
| `Spinner` | LLM inference wait | Needs implementation |

---

## Web UI Design System (MD3 Tokens)

The landing page (`frontend/landing/`) and dashboard use Material Design 3 token system.

### Color Tokens
```css
/* Primary palette — Mekong brand */
--md-sys-color-primary: #1565C0;          /* Deep blue — trust, tech */
--md-sys-color-on-primary: #FFFFFF;
--md-sys-color-primary-container: #D3E4FF;
--md-sys-color-secondary: #00897B;        /* Teal — growth */
--md-sys-color-tertiary: #F57F17;         /* Amber — energy, action */

/* Surface tokens */
--md-sys-color-surface: #FAFAFA;
--md-sys-color-surface-variant: #E8F0FE;
--md-sys-color-background: #FFFFFF;

/* Dark theme overrides */
--md-sys-color-primary-dark: #90CAF9;
--md-sys-color-surface-dark: #121212;
--md-sys-color-background-dark: #0A0A0A;
```

### Typography Scale
```css
--md-sys-typescale-display-large: 57px / 64px — Hero headings
--md-sys-typescale-headline-large: 32px / 40px — Section titles
--md-sys-typescale-title-large: 22px / 28px — Card titles
--md-sys-typescale-body-large: 16px / 24px — Body copy
--md-sys-typescale-label-large: 14px / 20px — Buttons, chips
--md-sys-typescale-code: JetBrains Mono 14px — All code blocks
```

---

## Component Library Status

| Component | Status | Notes |
|-----------|--------|-------|
| Navigation rail | Needs audit | Dashboard sidebar |
| Command cards | Needs design | 289 commands browser |
| Mission timeline | Needs design | PEV step visualization |
| Credit balance widget | Needs design | MCU usage meter |
| Pricing cards | Exists (landing) | 3 tiers, Polar.sh CTAs |
| Code block | Active | Syntax highlighted |
| Toast notifications | Needs implementation | Mission complete/fail |
| Empty states | Missing | Zero missions, zero credits |

---

## Dark Theme Implementation

Mekong CLI targets developer users who predominantly use dark terminals and dark IDEs.
Dark theme is **the primary theme**, not secondary.

```css
/* System preference detection */
@media (prefers-color-scheme: dark) {
  :root {
    --bg: var(--md-sys-color-background-dark);
    --surface: var(--md-sys-color-surface-dark);
    --primary: var(--md-sys-color-primary-dark);
  }
}
```

Rule: Design dark theme first, light theme as secondary. Never force theme — always
respect `prefers-color-scheme`.

---

## Landing Page Design Audit

Current landing (`frontend/landing/`) needs:
- [ ] GIF/video demo of `mekong cook` in terminal (above the fold)
- [ ] Command layer diagram (5-layer architecture visual)
- [ ] Pricing section with 3-tier cards (Starter/Pro/Enterprise)
- [ ] "Works with any LLM" provider logo strip
- [ ] GitHub star count badge (social proof)
- [ ] "Open source" trust badge (MIT license)

---

## Dashboard Design Priorities

Mission control dashboard (`agencyos.network → /v1/missions`):
1. **Mission list** — status (planning/executing/verifying/done/failed), duration, MCU used
2. **Mission detail** — PEV step-by-step timeline with expand/collapse
3. **Credit balance** — donut chart: used/remaining MCU
4. **Quick actions** — "New mission" button → triggers `mekong cook` equivalent via API

---

## Accessibility Standards

- WCAG 2.1 AA minimum for all web UI
- Color contrast ratio ≥ 4.5:1 for body text
- All interactive elements keyboard-navigable
- `aria-label` on all icon-only buttons
- Terminal output: no color-only differentiation (use symbols + color together)

---

## Design Debt

| Item | Impact | Effort |
|------|--------|--------|
| Missing empty states | Medium | Low |
| No toast/notification system | High | Medium |
| Inconsistent spacing (8px grid not enforced) | Medium | Medium |
| No loading skeleton screens | Medium | Medium |
| Mobile responsiveness untested | High | High |

---

## Q2 Design Actions

- [ ] Create Figma component library with MD3 tokens
- [ ] Design mission timeline component (PEV visualization)
- [ ] Design credit balance widget with usage alerts
- [ ] Record `mekong cook` demo GIF for README and landing
- [ ] Audit landing page against conversion best practices
- [ ] Implement toast notification system in dashboard
