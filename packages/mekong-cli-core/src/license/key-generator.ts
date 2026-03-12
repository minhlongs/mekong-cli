/**
 * KeyGenerator — generates RAAS-{TIER}-{16-char-hex} keys with HMAC-SHA256 signatures.
 * Phase 1 of v0.5 License Admin.
 */
import { randomBytes } from 'node:crypto';
import type { LicenseTier, LicenseKey } from './types.js';
import { computeSignature } from './verifier.js';

/** Options for generating a new license key. */
export interface KeyGenOptions {
  tier: LicenseTier;
  owner: string;
  /** Days until expiry; defaults to 365. */
  expiryDays?: number;
}

/**
 * Generate a new signed LicenseKey.
 * Format: RAAS-{TIER}-{16-char-hex}
 */
export function generateKey(opts: KeyGenOptions): LicenseKey {
  const { tier, owner, expiryDays = 365 } = opts;
  const randomPart = randomBytes(8).toString('hex'); // 16 hex chars
  const key = `RAAS-${tier.toUpperCase()}-${randomPart}`;
  const issuedAt = new Date().toISOString();
  const expiresAt = new Date(Date.now() + expiryDays * 86_400_000).toISOString();

  const partial = { key, tier, status: 'active' as const, issuedAt, expiresAt, owner };
  const signature = computeSignature(partial);
  return { ...partial, signature };
}
