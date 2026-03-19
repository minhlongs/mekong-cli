/**
 * raas-pricing.ts — Tier-based pricing for RaaS (ROIaaS-as-a-Service)
 * Defines tiers, credit costs, and usage calculation.
 */

export type RaasTier = 'starter' | 'pro' | 'enterprise';

export interface TierConfig {
  name: string;
  creditsPerMonth: number;
  priceUsd: number;
  maxProjects: number;
  features: string[];
}

export const TIER_CONFIGS: Record<RaasTier, TierConfig> = {
  starter: {
    name: 'Starter',
    creditsPerMonth: 200,
    priceUsd: 49,
    maxProjects: 3,
    features: ['basic-commands', 'email-support'],
  },
  pro: {
    name: 'Pro',
    creditsPerMonth: 1000,
    priceUsd: 149,
    maxProjects: 10,
    features: ['basic-commands', 'advanced-commands', 'priority-support', 'api-access'],
  },
  enterprise: {
    name: 'Enterprise',
    creditsPerMonth: -1, // unlimited
    priceUsd: 499,
    maxProjects: -1, // unlimited
    features: ['basic-commands', 'advanced-commands', 'priority-support', 'api-access', 'sla', 'custom-agents'],
  },
};

export interface UsageRecord {
  tenantId: string;
  command: string;
  creditsCost: number;
  timestamp: number;
  success: boolean;
}

export function calculateMonthlyCost(records: UsageRecord[]): number {
  return records.reduce((sum, r) => sum + (r.success ? r.creditsCost : 0), 0);
}

export function hasCreditsRemaining(tier: RaasTier, usedCredits: number): boolean {
  const config = TIER_CONFIGS[tier];
  if (config.creditsPerMonth === -1) return true; // unlimited
  return usedCredits < config.creditsPerMonth;
}

export function getOverageCredits(tier: RaasTier, usedCredits: number): number {
  const config = TIER_CONFIGS[tier];
  if (config.creditsPerMonth === -1) return 0;
  return Math.max(0, usedCredits - config.creditsPerMonth);
}
