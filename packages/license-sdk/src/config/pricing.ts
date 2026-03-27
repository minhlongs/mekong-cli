import type { Brand, LicenseTier } from '../core/tiers.js';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TierPricing {
  tier: LicenseTier;
  name: string;
  priceUsd: number;
  nowpaymentsProductId: string;
  features: string[];
  quotas: {
    commands: number;   // -1 = unlimited
    projects: number;   // -1 = unlimited
    support: 'community' | 'email' | 'priority' | 'dedicated';
  };
}

export interface BrandPricing {
  brand: Brand;
  tiers: TierPricing[];
}

// ---------------------------------------------------------------------------
// Pricing config — 6 brands × 4 tiers
// ---------------------------------------------------------------------------

export const PRICING_CONFIG: Record<string, BrandPricing> = {
  MEKONG: {
    brand: 'MEKONG',
    tiers: [
      { tier: 'free',       name: 'Free',       priceUsd: 0,   nowpaymentsProductId: '',               features: ['5 commands/day', 'Community forum'],                                           quotas: { commands: 5,    projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Starter',    priceUsd: 49,  nowpaymentsProductId: 'mekong-starter',  features: ['200 MCU/mo', '3 projects', 'Email support'],                              quotas: { commands: 200,   projects: 3,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',        priceUsd: 149, nowpaymentsProductId: 'mekong-pro',      features: ['1000 MCU/mo', '10 projects', 'Priority support', 'Analytics'],            quotas: { commands: 1000,  projects: 10, support: 'priority' } },
      { tier: 'enterprise', name: 'Enterprise', priceUsd: 499, nowpaymentsProductId: 'mekong-enterprise', features: ['Unlimited MCU', 'Unlimited projects', 'Dedicated support', 'SSO', 'Audit logs'], quotas: { commands: -1, projects: -1, support: 'dedicated' } },
    ],
  },
  SOPHIA: {
    brand: 'SOPHIA',
    tiers: [
      { tier: 'free',       name: 'Free',    priceUsd: 0,   nowpaymentsProductId: '',              features: ['3 AI tasks/day', 'Community forum'],                                              quotas: { commands: 3,    projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Creator', priceUsd: 19,  nowpaymentsProductId: 'sophia-creator', features: ['30 AI tasks/day', '2 projects', 'Email support'],                                quotas: { commands: 30,   projects: 2,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',     priceUsd: 49,  nowpaymentsProductId: 'sophia-pro',     features: ['150 AI tasks/day', '5 projects', 'Priority support', 'Advanced models'],         quotas: { commands: 150,  projects: 5,  support: 'priority' } },
      { tier: 'enterprise', name: 'Agency',  priceUsd: 149, nowpaymentsProductId: 'sophia-agency',  features: ['Unlimited tasks', 'Unlimited projects', 'Dedicated support', 'White-label', 'SSO'], quotas: { commands: -1, projects: -1, support: 'dedicated' } },
    ],
  },
  WELL: {
    brand: 'WELL',
    tiers: [
      { tier: 'free',       name: 'Free',       priceUsd: 0,   nowpaymentsProductId: '',              features: ['Basic tracking', 'Community forum'],                                              quotas: { commands: 10,   projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Growth',     priceUsd: 29,  nowpaymentsProductId: 'well-growth',    features: ['Full tracking', '3 programs', 'Email support'],                                 quotas: { commands: 100,  projects: 3,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',        priceUsd: 79,  nowpaymentsProductId: 'well-pro',       features: ['Advanced analytics', '10 programs', 'Priority support', 'AI insights'],         quotas: { commands: 500,  projects: 10, support: 'priority' } },
      { tier: 'enterprise', name: 'Enterprise', priceUsd: 199, nowpaymentsProductId: 'well-enterprise', features: ['Unlimited programs', 'Custom integrations', 'Dedicated support', 'SSO'],        quotas: { commands: -1,   projects: -1, support: 'dedicated' } },
    ],
  },
  ALGO: {
    brand: 'ALGO',
    tiers: [
      { tier: 'free',       name: 'Free',    priceUsd: 0,   nowpaymentsProductId: '',           features: ['Paper trading only', 'Community forum'],                                            quotas: { commands: 5,   projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Trader',  priceUsd: 49,  nowpaymentsProductId: 'algo-trader', features: ['Live trading', '2 strategies', 'Email support'],                                   quotas: { commands: 50,  projects: 2,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',     priceUsd: 149, nowpaymentsProductId: 'algo-pro',    features: ['10 strategies', 'Backtesting', 'Priority support', 'Risk management'],              quotas: { commands: 200, projects: 10, support: 'priority' } },
      { tier: 'enterprise', name: 'Quant',   priceUsd: 499, nowpaymentsProductId: 'algo-quant',  features: ['Unlimited strategies', 'HFT support', 'Dedicated support', 'Custom connectors'],    quotas: { commands: -1,  projects: -1, support: 'dedicated' } },
    ],
  },
  APEX: {
    brand: 'APEX',
    tiers: [
      { tier: 'free',       name: 'Free',       priceUsd: 0,   nowpaymentsProductId: '',               features: ['Basic features', 'Community forum'],                                             quotas: { commands: 10,  projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Starter',    priceUsd: 39,  nowpaymentsProductId: 'apex-starter',    features: ['Core features', '3 projects', 'Email support'],                                 quotas: { commands: 100, projects: 3,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',        priceUsd: 99,  nowpaymentsProductId: 'apex-pro',        features: ['Advanced features', '10 projects', 'Priority support', 'Analytics'],             quotas: { commands: 500, projects: 10, support: 'priority' } },
      { tier: 'enterprise', name: 'Enterprise', priceUsd: 299, nowpaymentsProductId: 'apex-enterprise', features: ['All features', 'Unlimited projects', 'Dedicated support', 'SSO', 'Audit logs'], quotas: { commands: -1,  projects: -1, support: 'dedicated' } },
    ],
  },
  AGENCYOS: {
    brand: 'AGENCYOS',
    tiers: [
      { tier: 'free',       name: 'Free',    priceUsd: 0,  nowpaymentsProductId: '',           features: ['1 SDK', 'Community forum'],                                                          quotas: { commands: 5,   projects: 1,  support: 'community' } },
      { tier: 'starter',    name: 'Builder', priceUsd: 19, nowpaymentsProductId: 'sdk-builder', features: ['5 SDKs', '3 projects', 'Email support'],                                            quotas: { commands: 50,  projects: 3,  support: 'email' } },
      { tier: 'pro',        name: 'Pro',     priceUsd: 49, nowpaymentsProductId: 'sdk-pro',     features: ['Unlimited SDKs', '10 projects', 'Priority support', 'Custom branding'],              quotas: { commands: 200, projects: 10, support: 'priority' } },
      { tier: 'enterprise', name: 'Agency',  priceUsd: 99, nowpaymentsProductId: 'sdk-agency',  features: ['Unlimited everything', 'White-label', 'Dedicated support', 'SSO', 'Audit logs'],    quotas: { commands: -1,  projects: -1, support: 'dedicated' } },
    ],
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function quotaLabel(value: number): string {
  return value === -1 ? 'Unlimited' : String(value);
}

/**
 * Generate a markdown pricing comparison table for a given brand.
 */
export function getPricingPage(brand: string): string {
  const config = PRICING_CONFIG[brand];
  if (!config) return `# Unknown brand: ${brand}\n`;

  const { tiers } = config;
  const header = `# ${brand} Pricing\n\n`;
  const cols = tiers.map(t => t.name).join(' | ');
  const sep  = tiers.map(() => '---').join(' | ');
  const prices = tiers.map(t => (t.priceUsd === 0 ? 'Free' : `$${t.priceUsd}/mo`)).join(' | ');
  const commands  = tiers.map(t => quotaLabel(t.quotas.commands)).join(' | ');
  const projects  = tiers.map(t => quotaLabel(t.quotas.projects)).join(' | ');
  const support   = tiers.map(t => t.quotas.support).join(' | ');

  const allFeatures = Array.from(new Set(tiers.flatMap(t => t.features)));
  const featureRows = allFeatures.map(f => {
    const cells = tiers.map(t => (t.features.includes(f) ? 'Yes' : '-')).join(' | ');
    return `| ${f} | ${cells} |`;
  }).join('\n');

  return [
    header,
    `| Feature | ${cols} |`,
    `| --- | ${sep} |`,
    `| **Price** | ${prices} |`,
    `| Commands/day | ${commands} |`,
    `| Projects | ${projects} |`,
    `| Support | ${support} |`,
    featureRows,
  ].join('\n') + '\n';
}

/**
 * Return pricing data as a plain object suitable for JSON serialisation / API responses.
 */
export function getPricingJSON(brand: string): object {
  const config = PRICING_CONFIG[brand];
  if (!config) return { error: `Unknown brand: ${brand}` };
  return config;
}
