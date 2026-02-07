---
title: "MAX WOW Upgrade - Premium Visual Overhaul"
description: "Complete visual transformation with glassmorphism, dark mode, micro-animations, and premium typography"
status: pending
priority: P1
effort: 24h
branch: master
tags: [ui, design, glassmorphism, dark-mode, premium]
created: 2026-02-07
---

# MAX WOW Upgrade Plan

> **Mission**: Transform all UI components and documentation into premium, eye-catching experiences that command attention and respect.

## Strategic Overview

This plan implements aggressive visual upgrades across:
- **Core Library** (`packages/ui/vibe-ui`) - Foundation for all apps
- **Landing Pages** (agencyos-landing, sophia-ai-factory, 84tea, sophia-proposal)
- **Documentation** (All README.md files across the monorepo)

## Success Metrics

- [ ] Dark mode as default across all properties
- [ ] Glassmorphism effects on 80%+ of interactive components
- [ ] Micro-animations on all state transitions
- [ ] Premium typography (Inter Display + JetBrains Mono)
- [ ] Mobile-first responsive design verified on 3+ devices
- [ ] README files with emoji structure + badges + visual hierarchy

---

## Phase Breakdown

### Phase 1: Core UI Library (`vibe-ui`) - 8h
**Priority**: P1 - CRITICAL PATH
**Status**: Pending

Foundation upgrade enabling all downstream apps.

[Details → phase-01-core-ui-library.md](./phase-01-core-ui-library.md)

### Phase 2: AgencyOS Landing - 4h
**Priority**: P1
**Status**: Pending

Primary landing page - flagship visual experience.

[Details → phase-02-agencyos-landing.md](./phase-02-agencyos-landing.md)

### Phase 3: Sophia AI Factory - 4h
**Priority**: P2
**Status**: Pending

AI product showcase with premium vibes.

[Details → phase-03-sophia-ai-factory.md](./phase-03-sophia-ai-factory.md)

### Phase 4: Sophia Proposal + 84tea - 4h
**Priority**: P3
**Status**: Pending

Secondary apps with consistent premium treatment.

[Details → phase-04-secondary-apps.md](./phase-04-secondary-apps.md)

### Phase 5: README Overhaul (Parallel) - 4h
**Priority**: P1 - CAN RUN PARALLEL
**Status**: Pending

Documentation transformation across all packages.

[Details → phase-05-readme-overhaul.md](./phase-05-readme-overhaul.md)

---

## Technical Standards

### Visual Design System

**Glassmorphism Classes** (Tailwind v4):
```css
.glass-card {
  @apply bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl;
}

.glass-panel {
  @apply bg-black/30 backdrop-blur-2xl border border-white/10;
}

.glass-button {
  @apply bg-gradient-to-r from-purple-500/20 to-pink-500/20
         backdrop-blur-md border border-white/30
         hover:border-white/50 transition-all duration-300;
}
```

**Dark Mode Palette**:
```js
colors: {
  dark: {
    bg: '#0a0a0f',
    surface: '#13131a',
    card: '#1a1a24',
    border: '#2a2a3a',
    text: '#e5e5f0',
    muted: '#9090a0'
  },
  accent: {
    primary: '#8b5cf6',   // Purple
    secondary: '#ec4899', // Pink
    tertiary: '#06b6d4'   // Cyan
  }
}
```

**Typography Stack**:
- **Headings**: `font-family: 'Inter Display', -apple-system, sans-serif`
- **Body**: `font-family: 'Inter', -apple-system, sans-serif`
- **Code**: `font-family: 'JetBrains Mono', 'Fira Code', monospace`

**Animation Library** (framer-motion):
```tsx
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
};

const scaleOnHover = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 }
};

const glowPulse = {
  animate: {
    boxShadow: [
      '0 0 20px rgba(139, 92, 246, 0.3)',
      '0 0 40px rgba(139, 92, 246, 0.5)',
      '0 0 20px rgba(139, 92, 246, 0.3)'
    ]
  },
  transition: { duration: 2, repeat: Infinity }
};
```

### Responsive Breakpoints
```js
screens: {
  xs: '375px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px'
}
```

---

## Dependencies

```json
{
  "framer-motion": "^12.33.0",
  "tailwindcss": "^4.0.0",
  "@tailwindcss/typography": "^0.5.15",
  "lucide-react": "^0.563.0",
  "class-variance-authority": "^0.7.1",
  "tailwind-merge": "^2.6.0"
}
```

**Font CDN**:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
```

---

## Execution Strategy

### Sequential Path
1. **Phase 1** (vibe-ui) → Foundation MUST complete first
2. **Phase 2-4** (Apps) → Depends on Phase 1 completion
3. **Phase 5** (READMEs) → Can run in parallel anytime

### Quality Gates
- [ ] Build passes with 0 TypeScript errors
- [ ] All animations tested on 60fps devices
- [ ] Dark mode contrast meets WCAG AA standards
- [ ] Mobile viewport tested on iPhone SE (375px) and iPad (768px)
- [ ] No console warnings/errors in production build

### Rollback Plan
- Git branch: `feat/max-wow-upgrade`
- Checkpoint commits after each phase
- Feature flags for gradual rollout if needed

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing components | High | Incremental rollout with feature detection |
| Performance degradation | Medium | Lazy-load animations, optimize backdrop-blur usage |
| Dark mode accessibility issues | Medium | WCAG contrast checker, user preference detection |
| Font loading delays | Low | Font subsetting, preload critical fonts |

---

## Next Steps

1. Review plan with stakeholders
2. Create feature branch `feat/max-wow-upgrade`
3. Execute Phase 1 (vibe-ui core)
4. Parallel: Start Phase 5 (README overhaul)
5. Sequential: Phases 2-4 (Apps integration)
6. Final QA and production deployment

---

**Estimated Total Effort**: 24 hours
**Parallel Optimization**: Can reduce to ~16 hours with 2 agents
**Target Completion**: 2-3 days for solo execution
