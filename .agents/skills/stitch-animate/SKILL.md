---
name: stitch-animate
description: >-
  Micro-interactions and animation engine for Cyber-Bento Horizon interfaces. Provides GPU-accelerated bento card hover transforms, glowing borders, and prefers-reduced-motion accessibility support.
---

# /stitch-animate — Motion & Micro-Interactions

Implements performance-optimized micro-interactions and transitions for Cyber-Bento components.

## Guidelines
1. **Transforms**: Use GPU-accelerated `transform` and `opacity` properties (`will-change: transform`).
2. **Elevated Hover**: Subtle translateY(-2px) elevation with emerald glow on interactive bento panels.
3. **Reduced Motion**: Full support for `@media (prefers-reduced-motion: reduce)` to disable transitions and animations for motion-sensitive users.
4. **Duration**: Fast, snappy interaction curves (150ms-250ms ease-out).

## Execution
```bash
python3 scripts/verify_site_public.py --motion
```
