import { createHmac } from 'node:crypto';
import type { Brand, LicenseTier } from './tiers.js';
import type { LicenseKey } from './key-generator.js';
import { buildPayload } from './key-generator.js';

export interface VerifyResult {
  valid: boolean;
  brand?: Brand;
  tier?: LicenseTier;
  owner?: string;
  reason?: string;
}

const DEV_SECRET = 'openclaw-dev-secret-do-not-use-in-production';

const KNOWN_BRANDS = new Set<Brand>([
  'MEKONG', 'SOPHIA', 'WELL', 'APEX', 'ALGO', 'OPENCLAW', 'AGENCYOS',
]);

function getSecret(): string {
  return process.env['OPENCLAW_LICENSE_SECRET'] ?? DEV_SECRET;
}

function hmac(payload: string): string {
  return createHmac('sha256', getSecret()).update(payload).digest('hex');
}

/**
 * Offline verification: decode brand from key prefix, verify HMAC, check expiry.
 * The `storedKey` object must be provided by the caller (loaded from LicenseStore).
 */
export function verifyKey(storedKey: LicenseKey): VerifyResult {
  const { key, brand, tier, owner, issuedAt, expiresAt, signature } = storedKey;

  // Validate brand prefix matches stored brand
  const prefix = key.split('-')[0] as Brand;
  if (!KNOWN_BRANDS.has(prefix)) {
    return { valid: false, reason: `unknown brand prefix: ${prefix}` };
  }
  if (prefix !== brand) {
    return { valid: false, reason: 'brand prefix mismatch' };
  }

  // Verify HMAC signature
  const payload = buildPayload(brand, tier, owner, issuedAt, expiresAt, key);
  const expected = hmac(payload);
  if (!timingSafeEqual(expected, signature)) {
    return { valid: false, reason: 'invalid signature' };
  }

  // Check expiry
  if (isExpiredByDate(expiresAt)) {
    return { valid: false, brand, tier, owner, reason: 'license expired' };
  }

  return { valid: true, brand, tier, owner };
}

/**
 * Returns true if the key is past its expiry date.
 */
export function isExpired(licenseKey: LicenseKey): boolean {
  return isExpiredByDate(licenseKey.expiresAt);
}

function isExpiredByDate(expiresAt: string | null): boolean {
  if (!expiresAt) return false;
  return Date.now() > new Date(expiresAt).getTime();
}

/** Constant-time string comparison to prevent timing attacks. */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}
