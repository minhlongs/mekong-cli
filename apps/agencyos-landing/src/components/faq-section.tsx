"use client";

import { GlassContainer } from "@/components/glass";
import { Heading } from "@/components/typography/heading";
import { useTranslations } from "next-intl";
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
  const t = useTranslations('faq');

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
            {t('title')}
          </Heading>
          <p className="text-xl text-gray-300">
            {t('subtitle')}
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
