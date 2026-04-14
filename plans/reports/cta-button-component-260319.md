# CTA Button Component - Created

**Date:** 2026-03-19
**Component:** `cta-button.component.jsx`
**Location:** `design-assets/raas-ux-kit/robot-interface-components.v2.1.79/buttons/`

---

## Overview

High-converting Call-to-Action button optimized for marketing and landing pages. Built on top of RaaS UX Kit v2.1.79 design tokens.

## Features

- **4 Variants:** primary, secondary, gradient, outline
- **4 Sizes:** sm, md, lg, xl
- **Loading State:** Spinner animation
- **Hover Effects:** Scale transform (1.02x), brightness adjustments
- **Accessibility:** ARIA labels, focus rings, keyboard navigation
- **Full Width Option:** For responsive layouts

## Token Usage

Uses CSS custom properties from `tokens.css`:
- `--color-primary*` - Primary brand colors
- `--color-secondary*` - Secondary colors
- `--color-accent*` - Accent gradient colors
- `--color-border-strong` - Outline variant border
- `--color-focus-ring` - Focus state
- `--radius-button` - Border radius (8px)
- `--shadow-{2,3,4}` - Elevation shadows

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | primary\|secondary\|gradient\|outline | primary | Visual style |
| `size` | sm\|md\|lg\|xl | lg | Button size |
| `isLoading` | boolean | false | Loading state |
| `fullWidth` | boolean | false | Full width layout |
| `icon` | ReactNode | - | Leading icon |
| `className` | string | '' | Additional classes |
| `onClick` | function | - | Click handler |

## Example Usage

```jsx
import { CTAButton } from '@raas/robot-interface';

// Primary CTA
<CTAButton variant="primary" size="lg" onClick={handleSignup}>
  Get Started Free
</CTAButton>

// Gradient (Premium)
<CTAButton variant="gradient" size="xl" onClick={handlePro}>
  Upgrade to Pro
</CTAButton>

// Outline (Low-friction)
<CTAButton variant="outline" size="md" icon={<PlayIcon />}>
  Watch Demo
</CTAButton>

// Loading State
<CTAButton variant="primary" isLoading>
  Processing...
</CTAButton>
```

## Accessibility

- WCAG 2.1 AA compliant color contrast
- Focus ring: 2px solid `--color-focus-ring`
- `aria-busy` for loading state
- `aria-disabled` for disabled state
- Keyboard: Tab focus, Enter/Space activation

## File

- **Path:** `design-assets/raas-ux-kit/robot-interface-components.v2.1.79/buttons/cta-button.component.jsx`
- **Lines:** 174
- **Dependencies:** React (useState, useCallback)
