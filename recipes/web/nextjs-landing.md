---
name: Next.js Landing Page
description: Create a modern, responsive landing page with Next.js, React, and Tailwind CSS
author: Mekong CLI
tags: nextjs,react,landing,tailwind,frontend
difficulty: beginner
estimated_time: 20min
---

# Next.js Landing Page

Build a modern, high-converting landing page with Next.js 14+ (App Router) and Tailwind CSS.

## Prerequisites

- Node.js 18+
- npm/pnpm installed
- Basic React knowledge

## Step 1: Project Setup

```bash
# Create Next.js app
npx create-next-app@latest landing-page --typescript --tailwind --eslint --app
cd landing-page

# Or with pnpm
pnpm create next-app landing-page --typescript --tailwind --eslint --app
```

## Step 2: Project Structure

```
landing-page/
├── app/
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Landing page
│   ├── globals.css      # Global styles
│   └── favicon.ico
├── components/
│   ├── Header.tsx
│   ├── Hero.tsx
│   ├── Features.tsx
│   ├── Testimonials.tsx
│   ├── CTA.tsx
│   └── Footer.tsx
├── public/
│   └── images/
└── tailwind.config.ts
```

## Step 3: Create Components

### `components/Header.tsx`

```tsx
import React from 'react';

export default function Header() {
  return (
    <header className="fixed top-0 w-full bg-white/80 backdrop-blur-md z-50">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex-shrink-0">
            <span className="text-2xl font-bold text-indigo-600">Brand</span>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <a href="#features" className="hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">Features</a>
              <a href="#testimonials" className="hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">Testimonials</a>
              <a href="#pricing" className="hover:text-indigo-600 px-3 py-2 rounded-md text-sm font-medium">Pricing</a>
              <button className="bg-indigo-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-indigo-700">
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
}
```

### `components/Hero.tsx`

```tsx
import React from 'react';

export default function Hero() {
  return (
    <section className="pt-32 pb-20 bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6">
          Build Faster with{' '}
          <span className="text-indigo-600">AgencyOS</span>
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
          The all-in-one platform for building and scaling your digital agency.
          Automate workflows, manage clients, and deliver results.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-indigo-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition">
            Start Free Trial
          </button>
          <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold hover:border-indigo-600 hover:text-indigo-600 transition">
            Watch Demo
          </button>
        </div>
        <p className="mt-4 text-sm text-gray-500">No credit card required · 14-day free trial</p>
      </div>
    </section>
  );
}
```

### `components/Features.tsx`

```tsx
import React from 'react';

const features = [
  {
    name: 'AI-Powered Automation',
    description: 'Automate repetitive tasks with intelligent workflows powered by cutting-edge AI.',
    icon: '⚡',
  },
  {
    name: 'Client Management',
    description: 'Centralized dashboard for all client communications, projects, and deliverables.',
    icon: '👥',
  },
  {
    name: 'Analytics & Reporting',
    description: 'Real-time insights and automated reports to track performance and ROI.',
    icon: '📊',
  },
  {
    name: 'Team Collaboration',
    description: 'Built-in tools for seamless team communication and project coordination.',
    icon: '🤝',
  },
  {
    name: 'White-Label Ready',
    description: 'Customize branding across the entire platform to match your agency identity.',
    icon: '🎨',
  },
  {
    name: 'API First',
    description: 'Extensive API for custom integrations and extending functionality.',
    icon: '🔌',
  },
];

export default function Features() {
  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Everything You Need to Scale
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Powerful features to help you manage clients, automate workflows, and grow your agency.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div key={feature.name} className="p-6 border border-gray-200 rounded-xl hover:shadow-lg transition">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.name}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

### `components/CTA.tsx`

```tsx
import React from 'react';

export default function CTA() {
  return (
    <section className="py-20 bg-indigo-600">
      <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
        <h2 className="text-4xl font-bold text-white mb-6">
          Ready to Transform Your Agency?
        </h2>
        <p className="text-xl text-indigo-100 mb-10">
          Join 500+ agencies already using AgencyOS to scale their operations.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button className="bg-white text-indigo-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-indigo-50 transition">
            Start Free Trial
          </button>
          <button className="border-2 border-white text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white/10 transition">
            Schedule Demo
          </button>
        </div>
      </div>
    </section>
  );
}
```

### `components/Footer.tsx`

```tsx
import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <h4 className="text-white font-semibold mb-4">Product</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">Features</a></li>
              <li><a href="#" className="hover:text-white">Pricing</a></li>
              <li><a href="#" className="hover:text-white">API</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Company</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">About</a></li>
              <li><a href="#" className="hover:text-white">Blog</a></li>
              <li><a href="#" className="hover:text-white">Careers</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">Docs</a></li>
              <li><a href="#" className="hover:text-white">Support</a></li>
              <li><a href="#" className="hover:text-white">Community</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li><a href="#" className="hover:text-white">Privacy</a></li>
              <li><a href="#" className="hover:text-white">Terms</a></li>
              <li><a href="#" className="hover:text-white">Security</a></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 pt-8 border-t border-gray-800 text-center text-sm">
          <p>&copy; 2026 AgencyOS. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
```

## Step 4: Update Main Page

Update `app/page.tsx`:

```tsx
import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import CTA from '@/components/CTA';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <Hero />
      <Features />
      <CTA />
      <Footer />
    </main>
  );
}
```

## Step 5: Run Development Server

```bash
# Install dependencies
npm install  # or pnpm install

# Start dev server
npm run dev  # or pnpm dev

# Open http://localhost:3000
```

## Verification Criteria

- [ ] Page renders without errors
- [ ] Responsive on mobile, tablet, desktop
- [ ] All links and buttons work
- [ ] Lighthouse score > 90

## Next Steps

- Add testimonials section
- Add pricing table
- Add contact form
- Add blog section
- Deploy to Cloudflare Pages
