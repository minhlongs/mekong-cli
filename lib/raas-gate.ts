/**
 * RaaS Open Core License Gating
 *
 * Premium agents gated behind RAAS_LICENSE_KEY verification.
 * Core CLI, commands, skills remain open-source.
 *
 * @security License key is validated but NOT cryptographically verified.
 *           For production, implement signed JWT licenses with public key verification.
 */

import { createHash } from 'crypto';

// License verification via environment variable
const RAAS_LICENSE_KEY = process.env.RAAS_LICENSE_KEY;

/**
 * License metadata stored with validated licenses
 */
export interface LicenseMetadata {
  key: string;
  tier: LicenseTier;
  expiresAt?: Date;
  features: string[];
}

/**
 * License tier levels
 */
export enum LicenseTier {
  FREE = 'free',
  PRO = 'pro',
  ENTERPRISE = 'enterprise',
}

/**
 * License validation result
 */
export interface LicenseValidation {
  valid: boolean;
  tier: LicenseTier;
  expiresAt?: Date;
  features: string[];
  error?: string;
}

/**
 * Custom error for license violations
 */
export class LicenseError extends Error {
  constructor(message: string, public readonly code: string) {
    super(message);
    this.name = 'LicenseError';
  }
}

/**
 * Validate license key format
 * Accepts formats:
 * - mekong-XXXX-XXXX-XXXX-XXXX (standard)
 * - mk_XXXXXXXXXXXXXXXX (short)
 * - Any non-empty string >= 16 chars (legacy)
 */
export function validateLicenseKeyFormat(key: string): boolean {
  if (!key || typeof key !== 'string') return false;

  // Standard format: mekong-XXXX-XXXX-XXXX-XXXX
  const standardPattern = /^mekong-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/i;
  if (standardPattern.test(key)) return true;

  // Short format: mk_XXXXXXXXXXXXXXXX
  const shortPattern = /^mk_[A-Z0-9]{16}$/i;
  if (shortPattern.test(key)) return true;

  // Legacy: any string >= 16 chars
  return key.length >= 16;
}

/**
 * Hash license key for secure comparison
 */
function hashLicenseKey(key: string): string {
  return createHash('sha256').update(key).digest('hex');
}

/**
 * Parse license metadata from key
 * In production, this should decode JWT or verify signature
 */
function parseLicenseMetadata(key: string): LicenseMetadata {
  // Default metadata for unverified licenses
  // In production: decode JWT, verify signature, extract claims
  return {
    key: hashLicenseKey(key),
    tier: LicenseTier.PRO, // Default tier
    features: ['auto-cto-pilot', 'opus-strategy', 'opus-parallel', 'opus-review'],
  };
}

/**
 * Check if RaaS license is valid with format validation
 */
export function hasValidLicense(): boolean {
  if (!RAAS_LICENSE_KEY) return false;
  return validateLicenseKeyFormat(RAAS_LICENSE_KEY);
}

/**
 * Get full license validation with metadata
 */
export function getLicenseValidation(): LicenseValidation {
  if (!RAAS_LICENSE_KEY) {
    return {
      valid: false,
      tier: LicenseTier.FREE,
      features: [],
      error: 'RAAS_LICENSE_KEY not set',
    };
  }

  if (!validateLicenseKeyFormat(RAAS_LICENSE_KEY)) {
    return {
      valid: false,
      tier: LicenseTier.FREE,
      features: [],
      error: 'Invalid license key format',
    };
  }

  const metadata = parseLicenseMetadata(RAAS_LICENSE_KEY);

  // Check expiration (if implemented)
  if (metadata.expiresAt && metadata.expiresAt < new Date()) {
    return {
      valid: false,
      tier: LicenseTier.FREE,
      features: [],
      error: 'License expired',
    };
  }

  return {
    valid: true,
    tier: metadata.tier,
    expiresAt: metadata.expiresAt,
    features: metadata.features,
  };
}

/**
 * Require valid license for premium features
 * Throws LicenseError if license is missing or invalid
 */
export function requireLicense(featureName: string): void {
  const validation = getLicenseValidation();

  if (!validation.valid) {
    throw new LicenseError(
      `RaaS License Required: "${featureName}" is a premium feature.`,
      'LICENSE_REQUIRED'
    );
  }

  // Check if feature is in licensed features
  if (validation.features.length > 0 && !validation.features.includes(featureName)) {
    throw new LicenseError(
      `Feature "${featureName}" not included in current license tier (${validation.tier}).`,
      'FEATURE_NOT_LICENSED'
    );
  }
}

/**
 * Premium agents that require license
 */
export const PREMIUM_AGENTS = {
  // CTO Auto-Pilot - Phase 1
  'auto-cto-pilot': {
    name: 'CTO Auto-Pilot',
    description: 'Tự động tạo tasks chất lượng cao theo Binh Pháp',
    phase: 'discovery',
    requiredTier: LicenseTier.PRO,
  },
  // Opus-gated features
  'opus-strategy': {
    name: 'Opus Strategy',
    description: 'Strategic planning với Claude Opus 4.6',
    phase: 'planning',
    requiredTier: LicenseTier.PRO,
  },
  'opus-parallel': {
    name: 'Opus Parallel',
    description: 'Parallel agent orchestration với Opus',
    phase: 'building',
    requiredTier: LicenseTier.PRO,
  },
  'opus-review': {
    name: 'Opus Code Review',
    description: 'Security & quality review với Opus',
    phase: 'polish',
    requiredTier: LicenseTier.PRO,
  },
} as const;

export type PremiumAgentKey = keyof typeof PREMIUM_AGENTS;

/**
 * Check if specific agent is premium
 */
export function isPremiumAgent(agentName: string): boolean {
  return agentName in PREMIUM_AGENTS;
}

/**
 * Gate access to premium agent with tier verification
 */
export function requirePremiumAgent(agentName: string): void {
  if (!isPremiumAgent(agentName)) {
    return; // Not a premium agent, no gate needed
  }

  const agent = PREMIUM_AGENTS[agentName as PremiumAgentKey];
  const validation = getLicenseValidation();

  if (!validation.valid) {
    throw new LicenseError(
      `RaaS License Required: "${agent.name}" is a premium feature.`,
      'LICENSE_REQUIRED'
    );
  }

  // Check tier requirement
  if (validation.tier === LicenseTier.FREE) {
    throw new LicenseError(
      `License upgrade required: "${agent.name}" requires ${agent.requiredTier} tier.`,
      'TIER_UPGRADE_REQUIRED'
    );
  }
}

/**
 * Get list of available agents based on license status
 */
export function getAvailableAgents(): {
  available: string[];
  premium: string[];
  locked: string[];
} {
  const validation = getLicenseValidation();
  const hasLicense = validation.valid && validation.tier !== LicenseTier.FREE;

  // Core agents (always available)
  const coreAgents = [
    'planner',
    'fullstack-developer',
    'code-reviewer',
    'tester',
    'debugger',
    'researcher',
    'ui-ux-designer',
    'docs-manager',
    'project-manager',
    'git-manager',
  ];

  // Premium agents
  const premiumAgents = Object.keys(PREMIUM_AGENTS);

  return {
    available: hasLicense ? [...coreAgents, ...premiumAgents] : coreAgents,
    premium: premiumAgents,
    locked: hasLicense ? [] : premiumAgents,
  };
}

/**
 * Get current license status (safe for logging)
 */
export function getLicenseStatus(): {
  hasLicense: boolean;
  tier: LicenseTier;
  featureCount: number;
  maskedKey?: string;
} {
  const validation = getLicenseValidation();

  return {
    hasLicense: validation.valid,
    tier: validation.tier,
    featureCount: validation.features.length,
    maskedKey: RAAS_LICENSE_KEY
      ? `${RAAS_LICENSE_KEY.substring(0, 4)}...${RAAS_LICENSE_KEY.substring(RAAS_LICENSE_KEY.length - 4)}`
      : undefined,
  };
}
