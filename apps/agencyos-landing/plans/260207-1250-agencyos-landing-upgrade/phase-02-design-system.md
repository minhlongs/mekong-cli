# Phase 02: Design System

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 5 hours

Build reusable glassmorphism design system with core UI components, typography scale, and animation utilities.

## Context Links

- Phase 01: [Audit & Setup](./phase-01-audit-setup.md)
- Research: Glassmorphism 2.0 best practices (dribbble.com/shots, awwwards.com)

## Key Insights

- Glassmorphism 2.0 = blur + transparency + borders + subtle glow
- Component composition > monolithic components
- CVA (class-variance-authority) for variant management
- Radix UI primitives for accessibility
- Framer Motion for micro-interactions

## Requirements

### Functional
- GlassCard component with variants (default, highlighted, interactive)
- Button component with magnetic effect
- Typography scale (H1, H2, H3, Body, Caption)
- Container/Grid layout primitives
- Reusable animation wrappers

### Non-Functional
- WCAG 2.1 AA accessibility compliance
- Smooth 60fps animations
- Tree-shakable component exports
- TypeScript strict mode

## Architecture

```
src/components/
├── ui/                          # Radix primitives
│   ├── button.tsx
│   ├── card.tsx
│   └── accordion.tsx
├── glass/                       # Glassmorphism components
│   ├── glass-card.tsx          # Core glass component
│   ├── glass-button.tsx        # Magnetic button
│   ├── glass-container.tsx     # Layout wrapper
│   └── animated-background.tsx # Gradient noise bg
└── typography/
    ├── heading.tsx
    └── text.tsx
```

## Related Code Files

**To Create:**
- `src/components/ui/button.tsx`
- `src/components/ui/card.tsx`
- `src/components/glass/glass-card.tsx`
- `src/components/glass/glass-button.tsx`
- `src/components/glass/glass-container.tsx`
- `src/components/glass/animated-background.tsx`
- `src/components/typography/heading.tsx`
- `src/components/typography/text.tsx`

**Dependencies (from Phase 01):**
- `src/lib/utils.ts` (cn function)
- `src/lib/animations.ts` (Framer presets)

## Implementation Steps

### 1. Create GlassCard Component (1h)

`src/components/glass/glass-card.tsx`:
```typescript
"use client";

import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { motion } from "framer-motion";
import { HTMLAttributes, forwardRef } from "react";

const glassCardVariants = cva(
  "relative overflow-hidden rounded-2xl backdrop-blur-xl border transition-all duration-300",
  {
    variants: {
      variant: {
        default: "bg-glass-100 border-glass-border",
        highlighted: "bg-glass-200 border-glow-purple glow-border",
        interactive: "bg-glass-100 border-glass-border hover:bg-glass-200 hover:scale-[1.02] cursor-pointer",
      },
      padding: {
        none: "p-0",
        sm: "p-4",
        md: "p-6",
        lg: "p-8",
      },
      noise: {
        true: "noise-texture",
        false: "",
      },
    },
    defaultVariants: {
      variant: "default",
      padding: "md",
      noise: true,
    },
  }
);

export interface GlassCardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof glassCardVariants> {
  animated?: boolean;
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  ({ className, variant, padding, noise, animated = false, children, ...props }, ref) => {
    const Comp = animated ? motion.div : "div";

    return (
      <Comp
        ref={ref}
        className={cn(glassCardVariants({ variant, padding, noise }), className)}
        {...(animated && {
          initial: { opacity: 0, y: 20 },
          whileInView: { opacity: 1, y: 0 },
          viewport: { once: true },
          transition: { duration: 0.6 },
        })}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);

GlassCard.displayName = "GlassCard";
```

### 2. Create Magnetic Button Component (1.5h)

`src/components/glass/glass-button.tsx`:
```typescript
"use client";

import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ButtonHTMLAttributes, forwardRef, useRef } from "react";

const buttonVariants = cva(
  "relative inline-flex items-center justify-center rounded-full font-medium transition-all duration-300 overflow-hidden",
  {
    variants: {
      variant: {
        primary: "bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:shadow-2xl hover:shadow-purple-500/50",
        glass: "glass-effect hover:bg-glass-200 text-white",
        outline: "border-2 border-white/20 hover:border-white/40 hover:bg-glass-100 text-white",
      },
      size: {
        sm: "px-4 py-2 text-sm",
        md: "px-6 py-3 text-base",
        lg: "px-8 py-4 text-lg",
      },
      magnetic: {
        true: "cursor-pointer",
        false: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      magnetic: false,
    },
  }
);

export interface GlassButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  ({ className, variant, size, magnetic, children, ...props }, ref) => {
    const buttonRef = useRef<HTMLButtonElement>(null);
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const springConfig = { damping: 20, stiffness: 300 };
    const springX = useSpring(x, springConfig);
    const springY = useSpring(y, springConfig);

    const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (!magnetic || !buttonRef.current) return;

      const rect = buttonRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const distanceX = e.clientX - centerX;
      const distanceY = e.clientY - centerY;

      x.set(distanceX * 0.3);
      y.set(distanceY * 0.3);
    };

    const handleMouseLeave = () => {
      x.set(0);
      y.set(0);
    };

    return (
      <motion.button
        ref={buttonRef}
        className={cn(buttonVariants({ variant, size, magnetic }), className)}
        style={magnetic ? { x: springX, y: springY } : {}}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        {...props}
      >
        {children}
      </motion.button>
    );
  }
);

GlassButton.displayName = "GlassButton";
```

### 3. Create Animated Background Component (1h)

`src/components/glass/animated-background.tsx`:
```typescript
"use client";

import { motion } from "framer-motion";

export function AnimatedBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden bg-black">
      {/* Gradient Orbs */}
      <motion.div
        className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl"
        animate={{
          x: [0, 100, 0],
          y: [0, -50, 0],
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 20,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-3xl"
        animate={{
          x: [0, -100, 0],
          y: [0, 50, 0],
          scale: [1, 1.3, 1],
        }}
        transition={{
          duration: 25,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Noise Texture */}
      <div className="absolute inset-0 noise-texture opacity-50" />

      {/* Grid Overlay */}
      <div
        className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)
          `,
          backgroundSize: "50px 50px",
        }}
      />
    </div>
  );
}
```

### 4. Create Typography Components (45min)

`src/components/typography/heading.tsx`:
```typescript
import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { HTMLAttributes, forwardRef } from "react";

const headingVariants = cva("font-bold tracking-tight", {
  variants: {
    size: {
      h1: "text-5xl md:text-7xl lg:text-8xl",
      h2: "text-4xl md:text-5xl lg:text-6xl",
      h3: "text-3xl md:text-4xl lg:text-5xl",
      h4: "text-2xl md:text-3xl",
    },
    gradient: {
      true: "bg-gradient-to-r from-white via-purple-200 to-blue-200 bg-clip-text text-transparent",
      false: "text-white",
    },
  },
  defaultVariants: {
    size: "h1",
    gradient: false,
  },
});

export interface HeadingProps
  extends HTMLAttributes<HTMLHeadingElement>,
    VariantProps<typeof headingVariants> {
  as?: "h1" | "h2" | "h3" | "h4";
}

export const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ className, size, gradient, as = "h1", children, ...props }, ref) => {
    const Comp = as;
    return (
      <Comp
        ref={ref}
        className={cn(headingVariants({ size, gradient }), className)}
        {...props}
      >
        {children}
      </Comp>
    );
  }
);

Heading.displayName = "Heading";
```

### 5. Create Glass Container (30min)

`src/components/glass/glass-container.tsx`:
```typescript
import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

export interface GlassContainerProps extends HTMLAttributes<HTMLDivElement> {
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full";
}

export const GlassContainer = forwardRef<HTMLDivElement, GlassContainerProps>(
  ({ className, maxWidth = "2xl", children, ...props }, ref) => {
    const maxWidthClasses = {
      sm: "max-w-screen-sm",
      md: "max-w-screen-md",
      lg: "max-w-screen-lg",
      xl: "max-w-screen-xl",
      "2xl": "max-w-screen-2xl",
      full: "max-w-full",
    };

    return (
      <div
        ref={ref}
        className={cn("mx-auto px-4 sm:px-6 lg:px-8", maxWidthClasses[maxWidth], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

GlassContainer.displayName = "GlassContainer";
```

### 6. Create Index Exports (15min)

`src/components/glass/index.ts`:
```typescript
export { GlassCard } from "./glass-card";
export { GlassButton } from "./glass-button";
export { GlassContainer } from "./glass-container";
export { AnimatedBackground } from "./animated-background";
```

### 7. Test Components (45min)

Create test page `src/app/design-test/page.tsx`:
```typescript
import { GlassCard, GlassButton, GlassContainer, AnimatedBackground } from "@/components/glass";
import { Heading } from "@/components/typography/heading";

export default function DesignTestPage() {
  return (
    <>
      <AnimatedBackground />
      <GlassContainer className="py-20">
        <div className="space-y-8">
          <Heading size="h1" gradient>
            Design System Test
          </Heading>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <GlassCard variant="default">
              <h3 className="text-xl font-bold mb-2">Default Card</h3>
              <p className="text-gray-300">Basic glassmorphism card</p>
            </GlassCard>

            <GlassCard variant="highlighted">
              <h3 className="text-xl font-bold mb-2">Highlighted Card</h3>
              <p className="text-gray-300">With glow border effect</p>
            </GlassCard>

            <GlassCard variant="interactive">
              <h3 className="text-xl font-bold mb-2">Interactive Card</h3>
              <p className="text-gray-300">Hover to see scale effect</p>
            </GlassCard>
          </div>

          <div className="flex gap-4">
            <GlassButton variant="primary" magnetic>
              Primary Button
            </GlassButton>
            <GlassButton variant="glass">Glass Button</GlassButton>
            <GlassButton variant="outline">Outline Button</GlassButton>
          </div>
        </div>
      </GlassContainer>
    </>
  );
}
```

## Todo List

- [ ] Create GlassCard component with variants
- [ ] Create GlassButton with magnetic effect
- [ ] Create AnimatedBackground component
- [ ] Create Heading typography component
- [ ] Create GlassContainer layout component
- [ ] Create index exports for glass components
- [ ] Create design test page
- [ ] Test all variants in browser
- [ ] Verify animations run at 60fps
- [ ] Check accessibility (keyboard nav, ARIA)
- [ ] Verify TypeScript compilation

## Success Criteria

- ✅ All glass components render correctly
- ✅ Magnetic button effect smooth and responsive
- ✅ Animated background runs without jank
- ✅ Typography scales properly across breakpoints
- ✅ Components are tree-shakable
- ✅ TypeScript strict mode passes
- ✅ Accessibility: keyboard navigation works
- ✅ Build size impact <50KB gzipped

## Risk Assessment

**Risk:** Animation performance on low-end devices
**Mitigation:** Use CSS transforms, detect reduced motion preference

**Risk:** Blur effects crash on older browsers
**Mitigation:** Provide fallback styles without backdrop-filter

**Risk:** Component API too complex
**Mitigation:** Use CVA for clean variant API, provide sensible defaults

## Security Considerations

- All components client-safe (no sensitive data exposure)
- Motion values sanitized (no XSS via style injection)
- Event handlers properly typed

## Next Steps

→ Proceed to Phase 03: Hero & Features implementation
