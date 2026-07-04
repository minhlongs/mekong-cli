/**
 * Pricing tier data layer.
 * Mirrors the 3-tier MCU billing model defined in CLAUDE.md.
 * Polar checkout URLs must be updated after each product approval cycle.
 */

import type { PricingTier } from "./types.js";

const PRICING_TIERS: PricingTier[] = [
  {
    id: "starter",
    name: "Starter",
    priceUsdCents: 4900,
    creditsPerMonth: 200,
    checkoutUrl:
      "https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA",
    highlighted: false,
    features: [
      "200 MCU credits / month",
      "All 342+ commands",
      "CF Pages auto-deploy",
      "Email support",
    ],
  },
  {
    id: "growth",
    name: "Growth",
    priceUsdCents: 14900,
    creditsPerMonth: 1000,
    checkoutUrl:
      "https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA",
    highlighted: true,
    features: [
      "1,000 MCU credits / month",
      "All 342+ commands",
      "Priority execution queue",
      "Slack support",
      "Custom LLM provider (BYOK)",
    ],
  },
  {
    id: "pro",
    name: "Pro",
    priceUsdCents: 49900,
    creditsPerMonth: 5000,
    checkoutUrl:
      "https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA",
    highlighted: false,
    features: [
      "5,000 MCU credits / month",
      "All 342+ commands",
      "Dedicated agent pool",
      "SLA 99.9%",
      "Custom LLM provider (BYOK)",
      "Audit log export",
    ],
  },
];

/** Returns all pricing tiers. Synchronous — data is static. */
export function getPricingTiers(): PricingTier[] {
  return PRICING_TIERS;
}
