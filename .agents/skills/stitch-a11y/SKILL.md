---
name: stitch-a11y
description: >-
  WCAG 2.1 AA accessibility auditing and remediation for Google Stitch web applications. Implements high-visibility focus-visible rings, ARIA labels, landmarks, and skip-to-content links.
---

# /stitch-a11y — WCAG 2.1 AA Accessibility Engine

Ensures all generated Stitch pages meet strict WCAG 2.1 AA accessibility standards.

## Principles
1. **Focus Visibility**: High-contrast 2px emerald focus-visible outline with 2px offset (`outline: 2px solid #10B981; outline-offset: 2px`).
2. **Keyboard Navigation**: Skip-to-content links (`#skip-to-content`), full `Tab` order predictability, and `Escape` handlers for modals.
3. **Semantic Roles & ARIA**: `role="banner"`, `role="main"`, `role="dialog"`, `aria-modal="true"`, `aria-label`, and `aria-expanded` attributes.
4. **Contrast Ratio**: 4.5:1 minimum contrast on obsidian dark backgrounds (`#090A0F`, `#11131A`).

## Execution
```bash
python3 scripts/verify_site_public.py --a11y
```
