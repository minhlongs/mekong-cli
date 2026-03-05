/**
 * RAAS License Gate — ROIaaS Phase 1
 *
 * Gate premium features behind RAAS_LICENSE_KEY environment variable.
 * Core features remain open-source. Premium features require valid license.
 *
 * @see docs/HIEN_PHAP_ROIAAS.md - Dual-Stream Revenue Strategy
 */

import { existsSync, readFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

/**
 * License validation result
 */
export interface LicenseValidation {
  isValid: boolean;
  licenseKey?: string;
  tier: 'free' | 'pro' | 'enterprise';
  features: string[];
  error?: string;
}

/**
 * Premium features gated by license
 */
export const PREMIUM_FEATURES = {
  free: [
    'basic-cli-commands',
    'open-source-agents',
    'community-patterns',
  ] as string[],
  pro: [
    'premium-agents',
    'advanced-patterns',
    'priority-support',
    'custom-workflows',
  ] as string[],
  enterprise: [
    'agi-auto-pilot',
    'team-collaboration',
    'audit-logs',
    'sso-integration',
    'dedicated-support',
  ] as string[],
} as const;

/**
 * Check if RAAS_LICENSE_KEY is set and valid
 *
 * Validation strategy:
 * - Empty/missing = free tier (core open-source features)
 * - Valid key = pro/enterprise tier (premium features unlocked)
 *
 * @returns License validation result
 */
export function validateLicense(): LicenseValidation {
  const licenseKey = process.env.RAAS_LICENSE_KEY;

  // No license = free tier (open-source core)
  if (!licenseKey || licenseKey.trim() === '') {
    return {
      isValid: false,
      tier: 'free',
      features: [...PREMIUM_FEATURES.free],
      error: 'No license key provided. Core features available. Set RAAS_LICENSE_KEY for premium features.',
    };
  }

  // Validate license key format
  const validation = validateLicenseKeyFormat(licenseKey);
  if (!validation.isValid) {
    return {
      isValid: false,
      tier: 'free',
      features: [...PREMIUM_FEATURES.free],
      error: validation.error,
    };
  }

  // Determine tier from license key
  const tier = determineTier(licenseKey);
  const features = PREMIUM_FEATURES[tier];

  return {
    isValid: true,
    licenseKey: maskLicenseKey(licenseKey),
    tier,
    features: [...features],
  };
}

/**
 * Validate license key format
 *
 * Expected formats:
 * - raas_pro_XXXXXXXXXXXXXXXX
 * - raas_ent_XXXXXXXXXXXXXXXX
 * - sk-raas-XXXXXXXXXXXXXXXX (Stripe-like)
 */
function validateLicenseKeyFormat(key: string): { isValid: boolean; error?: string } {
  const trimmedKey = key.trim();

  // Minimum length check
  if (trimmedKey.length < 16) {
    return {
      isValid: false,
      error: 'License key too short. Must be at least 16 characters.',
    };
  }

  // Check for valid prefix patterns
  const validPatterns = [
    /^raas_(pro|ent|enterprise)_/i,
    /^sk-raas-/i,
    /^rk-raas-/i,
  ];

  const hasValidPrefix = validPatterns.some(pattern => pattern.test(trimmedKey));

  if (!hasValidPrefix) {
    // Allow custom keys without prefix (for backward compatibility)
    // But log warning in production
    if (process.env.NODE_ENV === 'production') {
      console.warn('[RAAS-GATE] License key without standard prefix detected');
    }
  }

  return { isValid: true };
}

/**
 * Determine license tier from key
 */
function determineTier(key: string): 'pro' | 'enterprise' {
  const lowerKey = key.toLowerCase();

  if (lowerKey.includes('ent') || lowerKey.includes('enterprise')) {
    return 'enterprise';
  }

  if (lowerKey.includes('pro')) {
    return 'pro';
  }

  // Default to pro for valid keys without tier indicator
  return 'pro';
}

/**
 * Mask license key for logging (show first 8 and last 4 chars)
 */
function maskLicenseKey(key: string): string {
  if (key.length <= 12) {
    return '***';
  }
  return `${key.slice(0, 8)}...${key.slice(-4)}`;
}

/**
 * Check if a specific feature is available
 *
 * @param feature - Feature name to check
 * @returns True if feature is available
 */
export function hasFeature(feature: string): boolean {
  const validation = validateLicense();
  return validation.features.includes(feature);
}

/**
 * Require a premium feature - throws if not available
 *
 * @param feature - Feature name required
 * @throws Error if feature not available
 */
export function requireFeature(feature: string): void {
  const validation = validateLicense();

  if (!validation.features.includes(feature)) {
    throw new Error(
      `Premium feature '${feature}' requires ${validation.tier === 'free' ? 'a valid' : validation.tier + '+'} license. ` +
      `Set RAAS_LICENSE_KEY environment variable. ${validation.error || ''}`
    );
  }
}

/**
 * Get current license status as human-readable string
 */
export function getLicenseStatus(): string {
  const validation = validateLicense();

  if (!validation.isValid) {
    return `🔓 Free Tier (Open Source)\n   ${validation.error}`;
  }

  const tierEmoji = validation.tier === 'enterprise' ? '🏢' : '💎';
  return `${tierEmoji} ${validation.tier.toUpperCase()} License: ${validation.licenseKey}\n   Features: ${validation.features.join(', ')}`;
}

/**
 * Load license from file (alternative to env var)
 *
 * @param filePath - Path to license file
 * @returns License validation result
 */
export function loadLicenseFromFile(filePath?: string): LicenseValidation {
  const homeDirPath = typeof homedir === 'function' ? homedir() : process.env.HOME || '~';
  const defaultPaths = [
    join(process.cwd(), '.raas-license'),
    join(homeDirPath, '.raas-license'),
  ];

  const fileToRead = filePath || defaultPaths.find(p => existsSync(p));

  if (!fileToRead || !existsSync(fileToRead)) {
    return {
      isValid: false,
      tier: 'free',
      features: [...PREMIUM_FEATURES.free],
      error: 'No license file found',
    };
  }

  try {
    const licenseKey = readFileSync(fileToRead, 'utf-8').trim();
    process.env.RAAS_LICENSE_KEY = licenseKey;
    return validateLicense();
  } catch (error) {
    return {
      isValid: false,
      tier: 'free',
      features: [...PREMIUM_FEATURES.free],
      error: `Failed to read license file: ${(error as Error).message}`,
    };
  }
}

/**
 * CLI command: Check license status
 */
export function cliLicenseCheck(): void {
  console.log('=== RAAS License Status ===\n');
  console.log(getLicenseStatus());
  console.log('\n=== Premium Features ===\n');
  console.log('Pro:      ', PREMIUM_FEATURES.pro.join(', '));
  console.log('Enterprise:', PREMIUM_FEATURES.enterprise.join(', '));
}
