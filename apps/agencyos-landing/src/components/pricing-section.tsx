"use client";

import { GlassCard, GlassButton, GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { CheckoutButton } from "./checkout-button";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
import { Check, Zap, Crown, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";

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
  const t = useTranslations('pricing');

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
            {t('title')}
          </Heading>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            {t('subtitle')}
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
                      {t('popular')}
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
                        {t('cta')}
                      </GlassButton>
                    </CheckoutButton>
                  ) : (
                    <GlassButton variant="outline" className="w-full">
                      {t('ctaEnterprise')}
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
