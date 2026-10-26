/**
 * RaaS License Gate — Cryptographic HMAC-SHA256 license validation (Step 11b)
 *
 * Canonical tier hierarchy: FREE | BASIC | PREMIUM | ENTERPRISE | MASTER
 * Supports MEKONG-RAAS-v1 and SOPHIA-RAAS-v1 signed tokens.
 */
import * as crypto from 'crypto';

export type CanonicalTier = 'FREE' | 'BASIC' | 'PREMIUM' | 'ENTERPRISE' | 'MASTER';
export type LegacyTierAlias = 'free' | 'basic' | 'starter' | 'growth' | 'pro' | 'enterprise' | 'master';
export type LicenseTier = CanonicalTier | LegacyTierAlias;

const ALLOWED_PREFIXES = new Set(['MEKONG-RAAS-v1', 'SOPHIA-RAAS-v1']);
const DEFAULT_TEST_SECRET = 'mekong-raas-test-hmac-sha256-secret-baseline-2026';

const TIER_RANK: Record<CanonicalTier, number> = {
  FREE: 0,
  BASIC: 1,
  PREMIUM: 2,
  ENTERPRISE: 3,
  MASTER: 4,
};

export function normalizeTier(raw: string): CanonicalTier {
  const k = (raw || '').trim().toUpperCase();
  if (k === 'MASTER') return 'MASTER';
  if (k === 'ENTERPRISE' || k === 'ENTERPRISE_PLUS') return 'ENTERPRISE';
  if (k === 'PREMIUM' || k === 'PRO' || k === 'GROWTH' || k === 'TEAM') return 'PREMIUM';
  if (k === 'BASIC' || k === 'STARTER' || k === 'TRIAL') return 'BASIC';
  return 'FREE';
}

export const PREMIUM_FEATURES: Record<CanonicalTier, string[]> = {
  FREE: ['basic_cli_commands', 'open_source_agents', 'community_support'],
  BASIC: ['basic_cli_commands', 'open_source_agents', 'community_support', 'byok_standard'],
  PREMIUM: [
    'basic_cli_commands', 'open_source_agents', 'community_support', 'byok_standard',
    'premium_agents', 'ml_models', 'priority_queue', 'advanced_analytics',
  ],
  ENTERPRISE: [
    'basic_cli_commands', 'open_source_agents', 'community_support', 'byok_standard',
    'premium_agents', 'ml_models', 'priority_queue', 'advanced_analytics',
    'agi_auto_pilot', 'team_collaboration', 'custom_models', 'sla_guarantee',
  ],
  MASTER: [
    'basic_cli_commands', 'open_source_agents', 'community_support', 'byok_standard',
    'premium_agents', 'ml_models', 'priority_queue', 'advanced_analytics',
    'agi_auto_pilot', 'team_collaboration', 'custom_models', 'sla_guarantee',
    'whitelabel_portal', 'always_on_daemon', 'unlimited_mcu',
  ],
};

export interface LicenseValidation {
  valid: boolean;
  tier: CanonicalTier;
  features: string[];
  tenantId?: string;
  expiresAt?: number;
  error?: string;
}

export class LicenseError extends Error {
  constructor(feature: string, currentTier: LicenseTier) {
    super(`Feature "${feature}" requires upgrade from ${currentTier} tier`);
    this.name = 'LicenseError';
  }
}

function resolveSecret(explicit?: string): string {
  if (explicit) return explicit;
  const envSecret =
    process.env.RAAS_LICENSE_SECRET ||
    process.env.JWT_SECRET ||
    process.env.MEKONG_JWT_SECRET;
  if (envSecret) return envSecret;
  if (process.env.NODE_ENV === 'test' || process.env.CI || process.env.VITEST) {
    return DEFAULT_TEST_SECRET;
  }
  return '';
}

export class LicenseService {
  private static instance: LicenseService;
  private currentTier: CanonicalTier = 'FREE';
  private validated = false;

  private constructor() {}

  static getInstance(): LicenseService {
    if (!LicenseService.instance) {
      LicenseService.instance = new LicenseService();
    }
    return LicenseService.instance;
  }

  reset(): void {
    this.currentTier = 'FREE';
    this.validated = false;
  }

  generateHmacSignature(signingInput: string, secret?: string): string {
    const resolved = resolveSecret(secret);
    if (!resolved) return '';
    return crypto.createHmac('sha256', resolved).update(signingInput, 'utf8').digest('hex');
  }

  validateSync(key?: string, secret?: string): LicenseValidation {
    const licenseKey = (key || process.env.RAAS_LICENSE_KEY || '').trim();
    if (!licenseKey) {
      this.currentTier = 'FREE';
      this.validated = false;
      return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'empty_token' };
    }

    const parts = licenseKey.split('.');
    if (parts.length !== 3) {
      this.currentTier = 'FREE';
      this.validated = false;
      return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'invalid_token_format' };
    }

    const [prefix, payloadB64, sig] = parts;
    if (!ALLOWED_PREFIXES.has(prefix)) {
      this.currentTier = 'FREE';
      this.validated = false;
      return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'invalid_prefix' };
    }

    const expectedSig = this.generateHmacSignature(`${prefix}.${payloadB64}`, secret);
    const sigBuf = Buffer.from(sig, 'utf8');
    const expBuf = Buffer.from(expectedSig, 'utf8');
    if (!expectedSig || sigBuf.length !== expBuf.length || !crypto.timingSafeEqual(sigBuf, expBuf)) {
      this.currentTier = 'FREE';
      this.validated = false;
      return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'signature_mismatch' };
    }

    try {
      const rawJson = Buffer.from(payloadB64, 'base64url').toString('utf8');
      const data = JSON.parse(rawJson) as {
        tenant_id?: string;
        tier?: string;
        expires_at?: number;
        features?: string[];
      };
      const expiresAt = Number(data.expires_at || 0);
      if (Math.floor(Date.now() / 1000) >= expiresAt) {
        this.currentTier = 'FREE';
        this.validated = false;
        return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'license_expired' };
      }
      const tier = normalizeTier(data.tier || 'BASIC');
      this.currentTier = tier;
      this.validated = tier !== 'FREE';
      return {
        valid: this.validated,
        tier,
        features: Array.isArray(data.features) ? data.features : PREMIUM_FEATURES[tier],
        tenantId: data.tenant_id,
        expiresAt,
      };
    } catch {
      this.currentTier = 'FREE';
      this.validated = false;
      return { valid: false, tier: 'FREE', features: PREMIUM_FEATURES.FREE, error: 'malformed_payload' };
    }
  }

  async validate(key?: string, secret?: string): Promise<LicenseValidation> {
    return this.validateSync(key, secret);
  }

  hasTier(tier: LicenseTier): boolean {
    return TIER_RANK[this.currentTier] >= TIER_RANK[normalizeTier(tier)];
  }
}

export function hasFeature(feature: string): boolean {
  const tier = getLicenseTier();
  return PREMIUM_FEATURES[tier].includes(feature);
}

export function requireFeature(feature: string): void {
  if (!hasFeature(feature)) {
    throw new LicenseError(feature, getLicenseTier());
  }
}

export function getLicenseTier(): CanonicalTier {
  return LicenseService.getInstance()['currentTier'];
}
