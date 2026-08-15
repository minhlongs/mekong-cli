import { createHmac, randomBytes } from 'node:crypto';
import type { Brand, LicenseTier } from './tiers.js';

export interface LicenseKey {
  key: string;
  brand: Brand;
  tier: LicenseTier;
  owner: string;
  issuedAt: string;   // ISO 8601
  expiresAt: string | null;
  signature: string;
}

const DEV_SECRET = 'openclaw-dev-secret-do-not-use-in-production';

function getSecret(): string {
  return process.env['OPENCLAW_LICENSE_SECRET'] ?? DEV_SECRET;
}

function randomHexGroup(bytes: number): string {
  return randomBytes(bytes).toString('hex').toUpperCase();
}

function buildPayload(
  brand: Brand,
  tier: LicenseTier,
  owner: string,
  issuedAt: string,
  expiresAt: string | null,
  keyRaw: string,
): string {
  return [brand, tier, owner, issuedAt, expiresAt ?? 'never', keyRaw].join('|');
}

function sign(payload: string): string {
  return createHmac('sha256', getSecret()).update(payload).digest('hex');
}

function formatKey(brand: Brand): string {
  // {BRAND}-XXXX-XXXX-XXXX-XXXX  (16 hex chars in 4 groups of 4)
  const groups = [
    randomHexGroup(2), // 4 hex chars
    randomHexGroup(2),
    randomHexGroup(2),
    randomHexGroup(2),
  ];
  return `${brand}-${groups.join('-')}`;
}

/**
 * Generate a single signed license key.
 * @param expiryDays - if omitted or 0, key never expires.
 */
export function generateKey(
  brand: Brand,
  tier: LicenseTier,
  owner: string,
  expiryDays?: number,
): LicenseKey {
  const issuedAt = new Date().toISOString();
  const expiresAt =
    expiryDays && expiryDays > 0
      ? new Date(Date.now() + expiryDays * 86_400_000).toISOString()
      : null;

  const keyRaw = formatKey(brand);
  const payload = buildPayload(brand, tier, owner, issuedAt, expiresAt, keyRaw);
  const signature = sign(payload);

  return { key: keyRaw, brand, tier, owner, issuedAt, expiresAt, signature };
}

/**
 * Generate `count` keys with identical parameters.
 */
export function generateBatchKeys(
  brand: Brand,
  tier: LicenseTier,
  owner: string,
  count: number,
  expiryDays?: number,
): LicenseKey[] {
  if (count < 1) throw new RangeError('count must be >= 1');
  return Array.from({ length: count }, () => generateKey(brand, tier, owner, expiryDays));
}

/** Re-export for verifier to reuse signing logic without circular deps. */
export { buildPayload, sign };
