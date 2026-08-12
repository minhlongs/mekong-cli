# Phase 14 — Phase 01.14: Accessibility Audit & Fixes

**Date:** 260811 · **Status:** pending

## Task
Run axe-core audit. Fix: color contrast, focus visible outlines, heading hierarchy, landmark regions, ARIA labels, skip link, reduced motion. Test with NVDA/VoiceOver.

## Files

- src/components/**/*.tsx
- src/app/page.tsx
- src/styles/globals.css

## Acceptance criteria

Zero axe violations (WCAG 2.1 AA). Focus order logical. Skip link works. All interactive elements have focus-visible. Color contrast >= 4.5:1. prefers-reduced-motion respected.
