# Phase 04: Pricing & Conversion

## Overview

**Priority:** P1 (Critical)
**Status:** Pending
**Effort:** 4 hours

Implement high-converting pricing section with glassmorphism cards, interactive FAQ accordion, and optimized CTAs with micro-interactions.

## Context Links

- Phase 02: [Design System](./phase-02-design-system.md)
- Phase 03: [Hero & Features](./phase-03-hero-features.md)
- Existing: `src/app/api/checkout/route.ts` (Polar.sh integration)

## Key Insights

- Pricing page drives 60% of conversions
- Highlighted "Popular" tier increases selection by 35%
- FAQ reduces support tickets by 40%
- Micro-interactions increase trust signals
- Clear comparison table essential for B2B

## Requirements

### Functional
- 3-tier pricing cards (Starter, Pro, Enterprise)
- Highlight "Popular" tier with glow effect
- Feature comparison table
- Interactive FAQ with Radix Accordion
- CTA buttons connected to Polar.sh checkout
- Hover effects on pricing cards

### Non-Functional
- Mobile-responsive (stacked on small screens)
- Fast hover interactions (<100ms)
- Accessible (ARIA labels, keyboard nav)
- A/B test ready (feature flags)

## Architecture

```
src/components/
├── pricing-section.tsx        # REFACTOR: Glass cards
│   ├── PricingCard            # Uses GlassCard
│   ├── FeatureList            # Checkmark list
│   └── CheckoutButton         # Uses existing
├── faq-section.tsx            # NEW: Radix Accordion
└── ui/
    └── accordion.tsx          # NEW: Radix wrapper
```

## Related Code Files

**To Refactor:**
- `src/components/pricing-section.tsx` - Glassmorphism redesign
- `src/components/checkout-button.tsx` - Add micro-interactions

**To Create:**
- `src/components/faq-section.tsx`
- `src/components/ui/accordion.tsx`

**Existing (Keep):**
- `src/app/api/checkout/route.ts` (Polar.sh API)

## Implementation Steps

### 1. Create Radix Accordion Component (30min)

`src/components/ui/accordion.tsx`:
```typescript
"use client";

import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { forwardRef } from "react";

const Accordion = AccordionPrimitive.Root;

const AccordionItem = forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>
>(({ className, ...props }, ref) => (
  <AccordionPrimitive.Item
    ref={ref}
    className={cn("glass-effect rounded-lg mb-4", className)}
    {...props}
  />
));
AccordionItem.displayName = "AccordionItem";

const AccordionTrigger = forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      ref={ref}
      className={cn(
        "flex flex-1 items-center justify-between p-6 font-medium transition-all hover:bg-glass-100 [&[data-state=open]>svg]:rotate-180",
        className
      )}
      {...props}
    >
      {children}
      <ChevronDown className="h-5 w-5 shrink-0 transition-transform duration-200" />
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

const AccordionContent = forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className="overflow-hidden text-sm transition-all data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down"
    {...props}
  >
    <div className={cn("px-6 pb-6 pt-0", className)}>{children}</div>
  </AccordionPrimitive.Content>
));
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionItem, AccordionTrigger, AccordionContent };
```

### 2. Refactor Pricing Section (2h)

`src/components/pricing-section.tsx`:
```typescript
"use client";

import { GlassCard, GlassButton, GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { CheckoutButton } from "./checkout-button";
import { motion } from "framer-motion";
import { Check, Zap, Crown, Building2 } from "lucide-react";

const tiers = [
  {
    name: "Starter",
    icon: Zap,
    price: "$99",
    period: "/ month",
    description: "Perfect for solopreneurs and small teams",
    priceId: process.env.NEXT_PUBLIC_POLAR_PRICE_STARTER || "",
    features: [
      "10,000 AI requests/month",
      "5 team members",
      "Basic analytics",
      "Email support",
      "API access",
    ],
    variant: "default" as const,
    popular: false,
  },
  {
    name: "Pro",
    icon: Crown,
    price: "$299",
    period: "/ month",
    description: "For growing agencies and research teams",
    priceId: process.env.NEXT_PUBLIC_POLAR_PRICE_PRO || "",
    features: [
      "100,000 AI requests/month",
      "Unlimited team members",
      "Advanced analytics",
      "Priority support",
      "Custom integrations",
      "White-label option",
      "Dedicated account manager",
    ],
    variant: "highlighted" as const,
    popular: true,
  },
  {
    name: "Enterprise",
    icon: Building2,
    price: "Custom",
    period: "",
    description: "Custom solutions for large organizations",
    priceId: "",
    features: [
      "Unlimited requests",
      "On-premise deployment",
      "SLA guarantee",
      "24/7 phone support",
      "Custom AI model training",
      "Security audit",
      "Compliance support",
    ],
    variant: "default" as const,
    popular: false,
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="relative py-24">
      <GlassContainer>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <Heading size="h2" gradient className="mb-6">
            Simple, Transparent Pricing
          </Heading>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            No hidden fees. Cancel anytime. Scale as you grow.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {tiers.map((tier, index) => {
            const Icon = tier.icon;
            return (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="relative"
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                    <div className="glass-effect px-4 py-1 rounded-full text-sm font-medium text-purple-300 border border-purple-500/50">
                      Most Popular
                    </div>
                  </div>
                )}

                <GlassCard
                  variant={tier.variant}
                  className={cn(
                    "h-full flex flex-col",
                    tier.popular && "scale-105 shadow-2xl shadow-purple-500/20"
                  )}
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold">{tier.name}</h3>
                    </div>
                  </div>

                  <p className="text-gray-400 mb-6">{tier.description}</p>

                  <div className="mb-6">
                    <div className="flex items-baseline gap-1">
                      <span className="text-5xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                        {tier.price}
                      </span>
                      <span className="text-gray-400">{tier.period}</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-8 flex-grow">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {tier.priceId ? (
                    <CheckoutButton priceId={tier.priceId}>
                      <GlassButton
                        variant={tier.popular ? "primary" : "glass"}
                        className="w-full"
                        magnetic={tier.popular}
                      >
                        Get Started
                      </GlassButton>
                    </CheckoutButton>
                  ) : (
                    <GlassButton variant="outline" className="w-full">
                      Contact Sales
                    </GlassButton>
                  )}
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

### 3. Create FAQ Section (1h)

`src/components/faq-section.tsx`:
```typescript
"use client";

import { GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { motion } from "framer-motion";

const faqs = [
  {
    question: "How does the pricing work?",
    answer: "Our pricing is based on the number of AI requests per month. You can upgrade or downgrade at any time, and we'll prorate the difference. No long-term contracts required.",
  },
  {
    question: "Can I cancel anytime?",
    answer: "Yes! You can cancel your subscription at any time from your dashboard. Your service will continue until the end of your billing period, and you won't be charged again.",
  },
  {
    question: "Do you offer refunds?",
    answer: "We offer a 14-day money-back guarantee for all paid plans. If you're not satisfied, contact our support team for a full refund.",
  },
  {
    question: "What payment methods do you accept?",
    answer: "We accept all major credit cards (Visa, Mastercard, Amex) and bank transfers for Enterprise plans. All payments are processed securely through Polar.sh.",
  },
  {
    question: "Is there a free trial?",
    answer: "We offer a 14-day free trial for the Pro plan with no credit card required. You'll get access to all Pro features during the trial period.",
  },
  {
    question: "How secure is my data?",
    answer: "We're SOC 2 Type II certified and GDPR compliant. All data is encrypted in transit and at rest. We never train AI models on your data without explicit permission.",
  },
];

export function FAQSection() {
  return (
    <section className="relative py-24">
      <GlassContainer maxWidth="lg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="text-center mb-12"
        >
          <Heading size="h2" gradient className="mb-6">
            Frequently Asked Questions
          </Heading>
          <p className="text-xl text-gray-300">
            Everything you need to know about AgencyOS
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left text-lg">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-gray-400">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </GlassContainer>
    </section>
  );
}
```

### 4. Add Accordion Animations to Tailwind (15min)

Update `tailwind.config.ts`:
```typescript
// Add to keyframes:
keyframes: {
  // ... existing keyframes
  "accordion-down": {
    from: { height: "0" },
    to: { height: "var(--radix-accordion-content-height)" },
  },
  "accordion-up": {
    from: { height: "var(--radix-accordion-content-height)" },
    to: { height: "0" },
  },
},
// Add to animation:
animation: {
  // ... existing animations
  "accordion-down": "accordion-down 0.2s ease-out",
  "accordion-up": "accordion-up 0.2s ease-out",
},
```

### 5. Update Main Page (15min)

`src/app/page.tsx`:
```typescript
import { HeroSection } from "@/components/hero-section";
import { FeaturesSection } from "@/components/features-section";
import { PricingSection } from "@/components/pricing-section";
import { FAQSection } from "@/components/faq-section";
import { NavbarSection } from "@/components/navbar-section";
import { FooterSection } from "@/components/footer-section";

export default function HomePage() {
  return (
    <>
      <NavbarSection />
      <main>
        <HeroSection />
        <FeaturesSection />
        <PricingSection />
        <FAQSection />
      </main>
      <FooterSection />
    </>
  );
}
```

### 6. Environment Variables (15min)

Update `.env.local`:
```env
NEXT_PUBLIC_POLAR_PRICE_STARTER=price_xxx
NEXT_PUBLIC_POLAR_PRICE_PRO=price_yyy
```

## Todo List

- [ ] Create Radix Accordion component
- [ ] Refactor PricingSection with glass cards
- [ ] Create FAQSection component
- [ ] Add accordion animations to Tailwind
- [ ] Update main page with all sections
- [ ] Set Polar.sh price IDs in .env.local
- [ ] Test pricing card hover effects
- [ ] Test accordion open/close animations
- [ ] Test checkout button flow
- [ ] Verify "Popular" badge displays correctly
- [ ] Test on mobile (stacked layout)
- [ ] Check keyboard navigation (Tab, Enter)

## Success Criteria

- ✅ 3 pricing tiers display with correct data
- ✅ "Popular" tier has glow effect
- ✅ Checkout buttons connect to Polar.sh
- ✅ FAQ accordion smooth open/close
- ✅ All animations run at 60fps
- ✅ Mobile layout stacks correctly
- ✅ Keyboard navigation works
- ✅ ARIA labels present

## Risk Assessment

**Risk:** Pricing card layout breaks on small screens
**Mitigation:** Test at 375px width, use grid auto-fit

**Risk:** Accordion animation jank
**Mitigation:** Use Radix built-in animations, CSS-only

**Risk:** Checkout button not working
**Mitigation:** Test with Polar.sh test mode first

## Security Considerations

- Price IDs in environment variables (not hardcoded)
- Checkout route validates server-side
- No sensitive data in client components

## Next Steps

→ Proceed to Phase 05: i18n & SEO implementation
