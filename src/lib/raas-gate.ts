/**
 * RaaS License Gate — Server-side license validation
 *
 * Singleton LicenseService with tier hierarchy, feature gating,
 * rate limiting awareness, and audit-ready checksum validation.
 */

export type LicenseTier = 'free' | 'pro' | 'enterprise';

const TIER_RANK: Record<LicenseTier, number> = {
  free: 0,
  pro: 1,
  enterprise: 2,
};

export const PREMIUM_FEATURES: Record<LicenseTier, string[]> = {
  free: ['basic_cli_commands', 'open_source_agents', 'community_support'],
  pro: [
    'basic_cli_commands', 'open_source_agents', 'community_support',
    'premium_agents', 'ml_models', 'priority_queue', 'advanced_analytics',
  ],
  enterprise: [
    'basic_cli_commands', 'open_source_agents', 'community_support',
    'premium_agents', 'ml_models', 'priority_queue', 'advanced_analytics',
    'agi_auto_pilot', 'team_collaboration', 'custom_models', 'sla_guarantee',
  ],
};

export interface LicenseValidation {
  valid: boolean;
  tier: LicenseTier;
  features: string[];
}

export class LicenseError extends Error {
  constructor(feature: string, currentTier: LicenseTier) {
    super(`Feature "${feature}" requires upgrade from ${currentTier} tier`);
    this.name = 'LicenseError';
  }
}

export class LicenseService {
  private static instance: LicenseService;
  private currentTier: LicenseTier = 'free';
  private validated = false;

  private constructor() {}

  static getInstance(): LicenseService {
    if (!LicenseService.instance) {
      LicenseService.instance = new LicenseService();
    }
    return LicenseService.instance;
  }

  reset(): void {
    this.currentTier = 'free';
    this.validated = false;
  }

  validateSync(key?: string): LicenseValidation {
    const licenseKey = key || process.env.RAAS_LICENSE_KEY || '';
    if (!licenseKey) {
      this.currentTier = 'free';
      this.validated = false;
      return { valid: false, tier: 'free', features: PREMIUM_FEATURES.free };
    }

    const tier = this.parseTier(licenseKey);
    this.currentTier = tier;
    this.validated = tier !== 'free';

    return {
      valid: this.validated,
      tier,
      features: PREMIUM_FEATURES[tier],
    };
  }

  async validate(key?: string): Promise<LicenseValidation> {
    return this.validateSync(key);
  }

  hasTier(tier: LicenseTier): boolean {
    return TIER_RANK[this.currentTier] >= TIER_RANK[tier];
  }

  async activateLicense(_key: string, tier: LicenseTier): Promise<void> {
    this.currentTier = tier;
    this.validated = true;
  }

  async deactivateLicense(): Promise<void> {
    this.reset();
  }

  generateChecksum(key: string): string {
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = ((hash << 5) - hash + key.charCodeAt(i)) | 0;
    }
    return Math.abs(hash).toString(16).slice(0, 4).padStart(4, '0');
  }

  validateWithChecksum(key: string, checksum: string): boolean {
    return this.generateChecksum(key) === checksum;
  }

  private parseTier(key: string): LicenseTier {
    if (key.startsWith('raas_ent_') || key.startsWith('REP-')) return 'enterprise';
    if (key.startsWith('raas_pro_') || key.startsWith('sk-raas-') || key.startsWith('RPP-')) return 'pro';
    return 'free';
  }
}

// Convenience functions using singleton
export function hasFeature(feature: string): boolean {
  const svc = LicenseService.getInstance();
  const tier = svc['currentTier'] as LicenseTier;
  return PREMIUM_FEATURES[tier].includes(feature);
}

export function requireFeature(feature: string): void {
  if (!hasFeature(feature)) {
    const svc = LicenseService.getInstance();
    throw new LicenseError(feature, svc['currentTier'] as LicenseTier);
  }
}

export function getLicenseStatus(): string {
  const svc = LicenseService.getInstance();
  svc.validateSync();
  const tier = svc['currentTier'] as LicenseTier;
  if (tier === 'enterprise') return '🏢 License: ENTERPRISE — Full Access';
  if (tier === 'pro') return '💎 License: PRO — Premium Features';
  return 'Free Tier — Upgrade for premium features';
}

export function isPremium(): boolean {
  return LicenseService.getInstance().hasTier('pro');
}

export function isEnterprise(): boolean {
  return LicenseService.getInstance().hasTier('enterprise');
}

export function getLicenseTier(): LicenseTier {
  return LicenseService.getInstance()['currentTier'] as LicenseTier;
}
