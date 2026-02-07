"use client";

import { GlassCard, GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
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
  const t = useTranslations('features');

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
            {t('title')}
          </Heading>
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            {t('subtitle')}
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
