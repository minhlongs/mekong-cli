# Phase 12 — Phase 01.12: Accessibility Audit

**Date:** 260811 · **Status:** pending

## Task
Run axe-core audit. Fix all violations: semantic HTML, ARIA labels, focus management, color contrast, keyboard navigation, skip links, reduced motion.

## Files

- src/components/ui/*.tsx
- src/components/sections/*.tsx
- src/hooks/useFocusTrap.ts

## Acceptance criteria

Zero axe-core violations. All interactive elements keyboard accessible. Focus visible. Skip-to-content link works. Respects prefers-reduced-motion.
