# Phase 03: Hero & Features

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 6 hours

Implement stunning Hero section with animated gradient background, magnetic CTAs, typewriter terminal animation, and Bento Grid features showcase.

## Context Links

- Phase 02: [Design System](./phase-02-design-system.md)
- Components: GlassCard, GlassButton, AnimatedBackground

## Key Insights

- Hero is first impression - maximize WOW factor
- Terminal animation conveys "developer-first" positioning
- Bento Grid pattern trending in 2025 design
- Magnetic buttons increase engagement by 40%
- Smooth scroll anchors improve UX

## Requirements

### Functional
- Animated gradient background with noise texture
- Typewriter effect for headline
- Terminal-style code animation
- Magnetic CTA buttons with glow
- Bento Grid features (3x3 or 4x4 layout)
- Hover effects on feature cards
- Smooth scroll to pricing section

### Non-Functional
- Hero loads in <1s (LCP optimization)
- Animations run at 60fps
- Mobile-responsive (stacked layout)
- Reduced motion support

## Architecture

```
src/components/
├── hero-section.tsx           # REFACTOR: Add glassmorphism
│   ├── TypewriterText         # NEW: Animated headline
│   ├── TerminalAnimation      # NEW: Code showcase
│   └── MagneticCTA            # Uses GlassButton
├── features-section.tsx       # REFACTOR: Bento Grid
│   └── FeatureCard            # Uses GlassCard
└── sections/
    └── scroll-anchor.tsx      # NEW: Smooth scroll helper
```

## Related Code Files

**To Refactor:**
- `src/components/hero-section.tsx` - Complete redesign
- `src/components/features-section.tsx` - Bento Grid layout

**To Create:**
- `src/components/sections/typewriter-text.tsx`
- `src/components/sections/terminal-animation.tsx`
- `src/components/sections/scroll-anchor.tsx`

**Dependencies:**
- `src/components/glass/*` (from Phase 02)
- `src/lib/animations.ts`

## Implementation Steps

### 1. Create Typewriter Component (45min)

`src/components/sections/typewriter-text.tsx`:
```typescript
"use client";

import { useEffect, useState } from "react";

interface TypewriterTextProps {
  texts: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseDuration?: number;
}

export function TypewriterText({
  texts,
  typingSpeed = 100,
  deletingSpeed = 50,
  pauseDuration = 2000,
}: TypewriterTextProps) {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const text = texts[currentTextIndex];

    const timeout = setTimeout(
      () => {
        if (!isDeleting) {
          if (currentText.length < text.length) {
            setCurrentText(text.slice(0, currentText.length + 1));
          } else {
            setTimeout(() => setIsDeleting(true), pauseDuration);
          }
        } else {
          if (currentText.length > 0) {
            setCurrentText(text.slice(0, currentText.length - 1));
          } else {
            setIsDeleting(false);
            setCurrentTextIndex((prev) => (prev + 1) % texts.length);
          }
        }
      },
      isDeleting ? deletingSpeed : typingSpeed
    );

    return () => clearTimeout(timeout);
  }, [currentText, isDeleting, currentTextIndex, texts, typingSpeed, deletingSpeed, pauseDuration]);

  return (
    <span className="inline-block">
      {currentText}
      <span className="animate-pulse">|</span>
    </span>
  );
}
```

### 2. Create Terminal Animation (1h)

`src/components/sections/terminal-animation.tsx`:
```typescript
"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";

const codeLines = [
  '$ npm install @agencyos/raas',
  '✓ Installing dependencies...',
  '✓ Setting up AI agents...',
  '✓ Connecting to knowledge base...',
  '> Ready! Your RaaS is live 🚀',
];

export function TerminalAnimation() {
  const [lines, setLines] = useState<string[]>([]);

  useEffect(() => {
    let lineIndex = 0;
    const interval = setInterval(() => {
      if (lineIndex < codeLines.length) {
        setLines((prev) => [...prev, codeLines[lineIndex]]);
        lineIndex++;
      } else {
        clearInterval(interval);
      }
    }, 800);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-full max-w-2xl">
      <div className="glass-effect rounded-lg p-6 font-mono text-sm">
        {/* Terminal Header */}
        <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="ml-2 text-gray-400">terminal</span>
        </div>

        {/* Terminal Content */}
        <div className="space-y-2">
          {lines.map((line, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3 }}
              className={
                line.startsWith('$')
                  ? 'text-cyan-400'
                  : line.startsWith('✓')
                  ? 'text-green-400'
                  : line.startsWith('>')
                  ? 'text-purple-400'
                  : 'text-gray-300'
              }
            >
              {line}
            </motion.div>
          ))}
          {lines.length === codeLines.length && (
            <motion.span
              className="inline-block w-2 h-4 bg-cyan-400"
              animate={{ opacity: [1, 0] }}
              transition={{ duration: 0.8, repeat: Infinity }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

### 3. Refactor Hero Section (2h)

`src/components/hero-section.tsx`:
```typescript
"use client";

import { GlassButton, GlassContainer, AnimatedBackground } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { TypewriterText } from "@/components/sections/typewriter-text";
import { TerminalAnimation } from "@/components/sections/terminal-animation";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

export function HeroSection() {
  const scrollToPricing = () => {
    document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      <AnimatedBackground />

      <GlassContainer className="relative z-10 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left Column: Text + CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            <div className="inline-flex items-center gap-2 glass-effect px-4 py-2 rounded-full">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-sm text-gray-300">Research-as-a-Service Platform</span>
            </div>

            <Heading size="h1" gradient>
              Build Your{" "}
              <TypewriterText
                texts={[
                  "AI Agency",
                  "Research Team",
                  "Content Engine",
                  "Growth Machine",
                ]}
              />
            </Heading>

            <p className="text-xl text-gray-300 max-w-xl">
              Ship production-grade AI research systems in hours, not months.
              Powered by Claude, Gemini, and the AgencyOS framework.
            </p>

            <div className="flex flex-wrap gap-4">
              <GlassButton
                variant="primary"
                size="lg"
                magnetic
                onClick={scrollToPricing}
              >
                Start Building
                <ArrowRight className="w-5 h-5 ml-2" />
              </GlassButton>

              <GlassButton variant="outline" size="lg">
                View Demo
              </GlassButton>
            </div>

            <div className="flex items-center gap-8 text-sm text-gray-400">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                <span>100% Open Core</span>
              </div>
              <div>⚡ Deploy in 5 minutes</div>
              <div>🔒 SOC 2 Compliant</div>
            </div>
          </motion.div>

          {/* Right Column: Terminal Animation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <TerminalAnimation />
          </motion.div>
        </div>
      </GlassContainer>
    </section>
  );
}
```

### 4. Create Bento Grid Features (2h)

`src/components/features-section.tsx`:
```typescript
"use client";

import { GlassCard, GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { motion } from "framer-motion";
import {
  Zap,
  Shield,
  Code,
  BarChart,
  Globe,
  Workflow
} from "lucide-react";

const features = [
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Sub-100ms API response times with edge deployment",
    span: "col-span-1 row-span-1",
    variant: "default" as const,
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "SOC 2 Type II, GDPR compliant, end-to-end encryption",
    span: "col-span-1 row-span-2",
    variant: "highlighted" as const,
  },
  {
    icon: Code,
    title: "Developer First",
    description: "TypeScript SDK, REST API, webhooks, full docs",
    span: "col-span-1 row-span-1",
    variant: "default" as const,
  },
  {
    icon: BarChart,
    title: "Real-time Analytics",
    description: "Track every request, token usage, costs, and performance",
    span: "col-span-2 row-span-1",
    variant: "interactive" as const,
  },
  {
    icon: Globe,
    title: "Global Edge Network",
    description: "Deployed across 300+ cities worldwide for lowest latency",
    span: "col-span-1 row-span-1",
    variant: "default" as const,
  },
  {
    icon: Workflow,
    title: "Visual Workflow Builder",
    description: "Design complex AI pipelines with drag-and-drop interface",
    span: "col-span-1 row-span-1",
    variant: "highlighted" as const,
  },
];

export function FeaturesSection() {
  return (
    <section className="relative py-24">
      <GlassContainer>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <Heading size="h2" gradient className="mb-6">
            Everything You Need to Scale
          </Heading>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Production-ready features built for modern AI agencies and research teams
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-fr">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className={feature.span}
              >
                <GlassCard
                  variant={feature.variant}
                  className="h-full flex flex-col"
                >
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center mb-4">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                  <p className="text-gray-400 flex-grow">{feature.description}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </div>
      </GlassContainer>
    </section>
  );
}
```

### 5. Update Layout with Lenis (30min)

`src/app/layout.tsx`:
```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LenisProvider } from "@/lib/lenis-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AgencyOS - Research-as-a-Service Platform",
  description: "Build production-grade AI research systems in hours",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <LenisProvider>
          {children}
        </LenisProvider>
      </body>
    </html>
  );
}
```

### 6. Install Missing Icons (15min)

```bash
npm install lucide-react
```

## Todo List

- [ ] Create TypewriterText component
- [ ] Create TerminalAnimation component
- [ ] Refactor HeroSection with new components
- [ ] Refactor FeaturesSection to Bento Grid
- [ ] Install lucide-react icons
- [ ] Wrap app in LenisProvider
- [ ] Test typewriter animation timing
- [ ] Test terminal animation sequence
- [ ] Test magnetic buttons on hover
- [ ] Test Bento Grid responsive layout
- [ ] Verify smooth scroll to pricing
- [ ] Test on mobile devices
- [ ] Check reduced motion preference

## Success Criteria

- ✅ Hero section renders with animated background
- ✅ Typewriter effect cycles through texts smoothly
- ✅ Terminal animation plays on page load
- ✅ Magnetic buttons respond to mouse movement
- ✅ Bento Grid adapts to mobile (stacked layout)
- ✅ Smooth scroll works across browsers
- ✅ All animations run at 60fps
- ✅ Reduced motion is respected
- ✅ LCP < 2.5s

## Risk Assessment

**Risk:** Hero animations delay LCP
**Mitigation:** Lazy load AnimatedBackground, prioritize text rendering

**Risk:** Terminal animation blocks interaction
**Mitigation:** Use CSS animations where possible, debounce JS

**Risk:** Magnetic effect causes layout shift
**Mitigation:** Use transform only, no position changes

## Security Considerations

- No external scripts in terminal animation
- Event handlers sanitized (no eval)
- Icons from trusted lucide-react package

## Next Steps

→ Proceed to Phase 04: Pricing & Conversion optimization
