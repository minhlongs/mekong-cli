# Phase 01: Audit & Setup

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 4 hours

Foundation phase for glassmorphism upgrade: dependency installation, Tailwind 4 configuration, and project structure audit.

## Key Insights

- Current stack: Next.js 16, Tailwind 4, React 19
- Minimal dependencies (clean slate for upgrade)
- Existing components: Hero, Features, Pricing, Navbar, Footer
- Polar.sh checkout already integrated (route.ts exists)

## Requirements

### Functional
- Install framer-motion, lenis, radix-ui packages
- Configure Tailwind 4 for glassmorphism tokens
- Setup utility functions (cn, clsx)
- Audit existing components for refactor needs

### Non-Functional
- Zero breaking changes to existing functionality
- Maintain TypeScript strict mode
- Keep bundle size optimized (<500KB gzipped)

## Architecture

```
apps/agencyos-landing/
├── src/
│   ├── components/
│   │   ├── ui/               # NEW: Radix primitives
│   │   ├── glass/            # NEW: Glassmorphism components
│   │   └── [existing]        # Refactor targets
│   ├── lib/
│   │   ├── utils.ts          # NEW: cn() utility
│   │   ├── animations.ts     # NEW: Framer presets
│   │   └── lenis-provider.tsx # NEW: Smooth scroll
│   └── styles/
│       └── globals.css       # MODIFY: Add glass tokens
├── tailwind.config.ts        # MODIFY: Glassmorphism theme
└── package.json              # MODIFY: Add dependencies
```

## Related Code Files

**To Modify:**
- `tailwind.config.ts` - Add glassmorphism colors, animations
- `src/app/globals.css` - Add custom CSS properties
- `package.json` - Install new dependencies

**To Create:**
- `src/lib/utils.ts` - Utility functions
- `src/lib/animations.ts` - Animation presets
- `src/lib/lenis-provider.tsx` - Smooth scroll wrapper

**To Audit:**
- `src/components/hero-section.tsx`
- `src/components/features-section.tsx`
- `src/components/pricing-section.tsx`

## Implementation Steps

### 1. Dependency Installation (30min)

```bash
cd apps/agencyos-landing

# Animation & Scroll
npm install framer-motion @studio-freight/lenis

# UI Primitives
npm install @radix-ui/react-accordion @radix-ui/react-dialog @radix-ui/react-dropdown-menu

# Utilities
npm install clsx tailwind-merge class-variance-authority

# Types
npm install -D @types/node
```

### 2. Create Utility Functions (20min)

Create `src/lib/utils.ts`:
```typescript
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

### 3. Configure Tailwind Glassmorphism Theme (1h)

Update `tailwind.config.ts`:
```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        glass: {
          50: "rgba(255, 255, 255, 0.05)",
          100: "rgba(255, 255, 255, 0.1)",
          200: "rgba(255, 255, 255, 0.15)",
          300: "rgba(255, 255, 255, 0.2)",
        },
        glow: {
          purple: "rgba(168, 85, 247, 0.4)",
          blue: "rgba(59, 130, 246, 0.4)",
          cyan: "rgba(6, 182, 212, 0.4)",
        }
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'magnetic': 'magnetic 0.3s ease-out',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '0.5', boxShadow: '0 0 20px var(--glow-color)' },
          '50%': { opacity: '1', boxShadow: '0 0 40px var(--glow-color)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'magnetic': {
          '0%': { transform: 'translate(0, 0)' },
          '100%': { transform: 'translate(var(--x), var(--y))' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

### 4. Setup Global CSS (30min)

Update `src/app/globals.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --noise-opacity: 0.03;
    --glass-border: rgba(255, 255, 255, 0.1);
    --glow-color: rgba(168, 85, 247, 0.4);
  }

  html {
    scroll-behavior: auto;
  }

  body {
    @apply bg-black text-white antialiased;
  }
}

@layer utilities {
  .glass-effect {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .noise-texture {
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  }

  .glow-border {
    position: relative;
  }

  .glow-border::before {
    content: "";
    position: absolute;
    inset: -2px;
    border-radius: inherit;
    padding: 2px;
    background: linear-gradient(135deg, var(--glow-color), transparent);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
  }
}
```

### 5. Create Lenis Smooth Scroll Provider (40min)

Create `src/lib/lenis-provider.tsx`:
```typescript
"use client";

import { ReactNode, useEffect } from "react";
import Lenis from "@studio-freight/lenis";

export function LenisProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    const lenis = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  return <>{children}</>;
}
```

### 6. Create Animation Presets (30min)

Create `src/lib/animations.ts`:
```typescript
import { Variants } from "framer-motion";

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } },
};

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5 } },
};

export const magneticButton = {
  hover: { scale: 1.05 },
  tap: { scale: 0.95 },
};
```

### 7. Audit Existing Components (1h)

Review each component for refactor needs:
- Extract reusable patterns
- Identify glassmorphism candidates
- Document animation opportunities
- Note accessibility improvements

## Todo List

- [ ] Install all dependencies via npm
- [ ] Create `src/lib/utils.ts` with cn() function
- [ ] Update `tailwind.config.ts` with glassmorphism theme
- [ ] Update `src/app/globals.css` with glass utilities
- [ ] Create `src/lib/lenis-provider.tsx`
- [ ] Create `src/lib/animations.ts` with Framer presets
- [ ] Audit hero-section.tsx for refactor
- [ ] Audit features-section.tsx for refactor
- [ ] Audit pricing-section.tsx for refactor
- [ ] Verify build passes (npm run build)
- [ ] Document refactor findings

## Success Criteria

- ✅ All dependencies installed without conflicts
- ✅ Tailwind config includes glassmorphism tokens
- ✅ Utility functions (cn) working
- ✅ Lenis provider created
- ✅ Animation presets defined
- ✅ Build passes with 0 TypeScript errors
- ✅ Component audit complete with findings documented

## Risk Assessment

**Risk:** Dependency conflicts with Next.js 16 / React 19
**Mitigation:** Use compatible versions, test immediately after install

**Risk:** Tailwind 4 breaking changes
**Mitigation:** Review migration docs, test existing components

**Risk:** Performance impact from blur effects
**Mitigation:** Use CSS backdrop-filter, enable GPU acceleration

## Security Considerations

- All dependencies from trusted npm sources
- No runtime secrets exposed in client code
- Lenis scroll provider client-side only ("use client")

## Next Steps

→ Proceed to Phase 02: Design System (glass components)
