/**
 * VIBE UI Design Tokens - Aura Elite Design System
 *
 * Colors, gradients, animations, transitions, and utility classes.
 */

export const colors = {
  primary: {
    50: "#f0f9ff",
    100: "#e0f2fe",
    500: "#0ea5e9",
    600: "#0284c7",
    900: "#0c4a6e",
  },
  accent: {
    50: "#faf5ff",
    500: "#a855f7",
    600: "#9333ea",
  },
  success: {
    500: "#22c55e",
    600: "#16a34a",
  },
  dark: {
    bg: "#0f172a",
    card: "#1e293b",
    border: "#334155",
  },
} as const;

export const gradients = {
  aura: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
  vibe: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
  ocean: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
  sunset: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
} as const;

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
  },
  slideInLeft: {
    initial: { opacity: 0, x: -50 },
    animate: { opacity: 1, x: 0 },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
  },
  stagger: (delay = 0.1) => ({
    animate: { transition: { staggerChildren: delay } },
  }),
} as const;

export const transitions = {
  spring: { type: "spring", stiffness: 300, damping: 30 },
  smooth: { duration: 0.3, ease: "easeInOut" },
  bounce: { type: "spring", stiffness: 500, damping: 25 },
} as const;

export const vibeClasses = {
  glass: "backdrop-blur-xl bg-white/10 border border-white/20",
  gradientText:
    "bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent",
  hoverScale: "transition-transform hover:scale-105",
  hoverGlow: "hover:shadow-lg hover:shadow-purple-500/25",
  focusRing:
    "focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2",
} as const;
