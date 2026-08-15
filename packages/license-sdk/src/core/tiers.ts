export type LicenseTier = 'free' | 'starter' | 'pro' | 'enterprise';

export type Brand =
  | 'MEKONG'
  | 'SOPHIA'
  | 'WELL'
  | 'APEX'
  | 'ALGO'
  | 'OPENCLAW'
  | 'AGENCYOS';

export const TIER_ORDER: LicenseTier[] = ['free', 'starter', 'pro', 'enterprise'];

export const TIER_PRICING: Record<LicenseTier, { priceUsd: number; name: string }> = {
  free:       { priceUsd: 0,   name: 'Free' },
  starter:    { priceUsd: 29,  name: 'Starter' },
  pro:        { priceUsd: 99,  name: 'Pro' },
  enterprise: { priceUsd: 299, name: 'Enterprise' },
};

export interface TierConfig {
  tier: LicenseTier;
  priceUsd: number;
  name: string;
  maxCommands?: number;
  maxApiCalls?: number;
  features?: string[];
}

/**
 * Returns true if `current` tier satisfies `required` tier minimum.
 */
export function tierMeetsMinimum(current: LicenseTier, required: LicenseTier): boolean {
  return TIER_ORDER.indexOf(current) >= TIER_ORDER.indexOf(required);
}

/**
 * Build a full tier config map, merging defaults with caller overrides.
 */
export function createCustomTiers(
  overrides: Partial<Record<LicenseTier, Partial<TierConfig>>>
): Record<LicenseTier, TierConfig> {
  const defaults: Record<LicenseTier, TierConfig> = {
    free: {
      tier: 'free',
      ...TIER_PRICING.free,
      maxCommands: 10,
      maxApiCalls: 100,
      features: [],
    },
    starter: {
      tier: 'starter',
      ...TIER_PRICING.starter,
      maxCommands: 50,
      maxApiCalls: 1000,
      features: ['basic_support'],
    },
    pro: {
      tier: 'pro',
      ...TIER_PRICING.pro,
      maxCommands: 200,
      maxApiCalls: 10000,
      features: ['basic_support', 'priority_support', 'advanced_analytics'],
    },
    enterprise: {
      tier: 'enterprise',
      ...TIER_PRICING.enterprise,
      maxCommands: -1,
      maxApiCalls: -1,
      features: ['basic_support', 'priority_support', 'advanced_analytics', 'sso', 'audit_logs'],
    },
  };

  const result = { ...defaults } as Record<LicenseTier, TierConfig>;
  for (const tier of TIER_ORDER) {
    if (overrides[tier]) {
      result[tier] = { ...defaults[tier], ...overrides[tier], tier };
    }
  }
  return result;
}
