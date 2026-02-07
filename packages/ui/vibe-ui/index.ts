/**
 * 🎨 VIBE UI - MAX WOW Design System
 *
 * Premium glassmorphism components with dark mode excellence
 * Pattern 106: Composite Layout Animation Orchestration
 * Pattern 95: Reusable Component Topologies
 */

import type { ReactNode } from "react";

// ============================================
// MAX WOW DESIGN TOKENS
// ============================================

export const colors = {
  // Primary - Aura Gradient
  primary: {
    50: "#f0f9ff",
    100: "#e0f2fe",
    500: "#0ea5e9",
    600: "#0284c7",
    900: "#0c4a6e",
  },
  // Accent - MAX WOW Purple/Pink/Cyan
  accent: {
    primary: "#8b5cf6",   // Purple
    secondary: "#ec4899", // Pink
    tertiary: "#06b6d4",  // Cyan
    50: "#faf5ff",
    500: "#a855f7",
    600: "#9333ea",
  },
  // Success - Win Green
  success: {
    500: "#22c55e",
    600: "#16a34a",
  },
  // Dark Mode - Deep Premium Blacks
  dark: {
    bg: "#0a0a0f",      // Deep black background
    surface: "#13131a",  // Surface layer
    card: "#1a1a24",     // Card background
    border: "#2a2a3a",   // Border color
    text: "#e5e5f0",     // Primary text
    muted: "#9090a0",    // Muted text
  },
} as const;

export const gradients = {
  aura: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  vibe: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  ocean: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  sunset: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
  maxWow: "linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #06b6d4 100%)",
  purplePink: "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)",
} as const;

// ============================================
// MAX WOW ANIMATION PRESETS (Pattern 106)
// ============================================

export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  fadeInUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  },
  slideInLeft: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
    transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
    transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] },
  },
  scaleOnHover: {
    whileHover: { scale: 1.02 },
    whileTap: { scale: 0.98 },
  },
  glowPulse: {
    animate: {
      boxShadow: [
        "0 0 20px rgba(139, 92, 246, 0.3)",
        "0 0 40px rgba(139, 92, 246, 0.5)",
        "0 0 20px rgba(139, 92, 246, 0.3)",
      ],
    },
    transition: { duration: 2, repeat: Infinity },
  },
  stagger: (delay = 0.1) => ({
    animate: { transition: { staggerChildren: delay } },
  }),
} as const;

export const transitions = {
  spring: { type: "spring" as const, stiffness: 300, damping: 30 },
  smooth: { duration: 0.3, ease: "easeInOut" as const },
  bounce: { type: "spring" as const, stiffness: 500, damping: 25 },
  premium: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as any },
} as const;

// ============================================
// COMPONENT PATTERNS (Pattern 95)
// ============================================

export interface ButtonProps {
  variant: "primary" | "secondary" | "ghost" | "vibe";
  size: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
}

export interface CardProps {
  variant: "default" | "glass" | "gradient";
  hover?: boolean;
  children: ReactNode;
}

export interface BadgeProps {
  variant: "success" | "warning" | "error" | "info" | "vibe";
  size: "sm" | "md";
  children: ReactNode;
}

// ============================================
// MAX WOW UTILITY CLASSES
// ============================================

export const vibeClasses = {
  // Glassmorphism variants
  glass: "backdrop-blur-xl bg-white/10 border border-white/20 shadow-2xl",
  glassCard: "backdrop-blur-xl bg-white/10 border border-white/20 shadow-2xl rounded-2xl",
  glassPanel: "backdrop-blur-2xl bg-black/30 border border-white/10 rounded-xl",
  glassButton: "backdrop-blur-md bg-gradient-to-r from-purple-500/20 to-pink-500/20 border border-white/30 hover:border-white/50 transition-all duration-300",
  glassDark: "backdrop-blur-xl bg-black/40 border border-white/10 shadow-2xl",

  // Gradient text
  gradientText: "bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent",
  gradientTextMaxWow: "bg-gradient-to-r from-purple-400 via-pink-500 to-cyan-400 bg-clip-text text-transparent",

  // Hover effects
  hoverScale: "transition-transform hover:scale-105 duration-300",
  hoverGlow: "hover:shadow-lg hover:shadow-purple-500/25 transition-shadow duration-300",
  hoverGlowPink: "hover:shadow-lg hover:shadow-pink-500/25 transition-shadow duration-300",
  hoverLift: "transition-transform hover:-translate-y-1 duration-300",

  // Focus ring
  focusRing: "focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-dark-bg",

  // Premium backgrounds
  bgDarkPremium: "bg-gradient-to-br from-dark-bg to-dark-surface",
  bgGlassGradient: "bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-xl border border-white/10",
} as const;

// ============================================
// EXPORTS
// ============================================

export default {
  colors,
  gradients,
  animations,
  transitions,
  vibeClasses,
};
