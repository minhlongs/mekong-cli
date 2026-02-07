# 🚀 AgencyOS Landing - Premium Marketing Site

<div align="center">

![MAX WOW](https://img.shields.io/badge/MAX-WOW-8b5cf6?style=for-the-badge&logo=sparkles&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=for-the-badge&logo=next.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-4.0-06B6D4?style=for-the-badge&logo=tailwind-css&logoColor=white)

**Flagship marketing experience with glassmorphism design and dark mode**

[🎨 Features](#-features) • [🚀 Quick Start](#-quick-start) • [🎯 Tech Stack](#-tech-stack)

</div>

---

## ✨ Features

### 🎨 **Premium Visual Design**
- **Glassmorphism effects** on interactive components
- **Dark mode** as default with WCAG AA contrast
- **Micro-animations** on all state transitions
- **Gradient accents** (Purple → Pink → Cyan)

### ⚡ **Performance Optimized**
- Next.js App Router with server components
- Optimized fonts (Inter Display + JetBrains Mono)
- Code splitting with React.lazy
- WebP image optimization

### 📱 **Mobile-First Responsive**
- Breakpoints: 375px → 1536px
- Touch-optimized interactions
- Progressive enhancement

---

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Development server
pnpm dev
# → http://localhost:3000

# Production build
pnpm build
pnpm start
```

---

## 🎯 Tech Stack

### Framework
- **Next.js 16** - App Router, Server Components
- **React 19** - React Compiler enabled
- **TypeScript 5.0+** - Strict mode

### Styling
- **Tailwind CSS 4.0** - Utility-first
- **Framer Motion 12** - Animations
- **Lucide React** - Icon system
- **CVA** - Component variants

### Deployment
- **Vercel** - Edge deployment
- **GitHub Actions** - CI/CD pipeline
- **Analytics** - Vercel Analytics

---

## 🎨 Design System

### Color Palette
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

### Typography
- **Headings**: Inter Display (900 weight)
- **Body**: Inter (400-600)
- **Code**: JetBrains Mono (400-600)

### Animations
```tsx
const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
};
```

---

## 📁 Project Structure

```
apps/agencyos-landing/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Home page
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── ui/                 # Base UI components
│   ├── sections/           # Page sections
│   └── layout/             # Layout components
├── lib/                    # Utilities
├── public/                 # Static assets
└── tailwind.config.ts      # Tailwind configuration
```

---

## 🧪 Development

```bash
# Type checking
pnpm type-check

# Linting
pnpm lint

# Format
pnpm format
```

---

## 🚢 Deployment

Automatic deployment via Vercel:
```bash
git push origin main
# → Triggers GitHub Actions → Vercel deployment
```

Manual deployment:
```bash
pnpm build
vercel --prod
```

---

## 🎯 Quality Gates

- ✅ Build passes with 0 TypeScript errors
- ✅ Dark mode contrast meets WCAG AA
- ✅ Mobile viewport tested (375px - 1536px)
- ✅ Lighthouse score: 90+ on all metrics

---

<div align="center">

**Part of Mekong CLI Hub Architecture**

[← Back to Root](../../README.md) • [Documentation](../../docs/)

</div>
