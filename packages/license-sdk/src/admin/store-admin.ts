/**
 * Admin helpers: key issuance, revocation, store audit using the new core API.
 */

import { generateKey, generateBatchKeys } from '../core/key-generator.js';
import { verifyKey } from '../core/verifier.js';
import { LicenseStore, defaultStore } from '../core/store.js';
import type { Brand, LicenseTier } from '../core/tiers.js';
import type { LicenseKey } from '../core/key-generator.js';
import type { VerifyResult } from '../core/verifier.js';

export interface AuditEntry {
  brand: Brand;
  key: string;
  tier: LicenseTier;
  owner: string;
  issuedAt: string;
  expiresAt: string | null;
  status: 'valid' | 'expired' | 'invalid';
}

/**
 * Issue a single key and optionally persist to a store.
 */
export function issueKey(
  brand: Brand,
  tier: LicenseTier,
  owner: string,
  expiryDays?: number,
  store?: LicenseStore,
): LicenseKey {
  const licenseKey = generateKey(brand, tier, owner, expiryDays);
  store?.save(brand, licenseKey);
  return licenseKey;
}

/**
 * Batch-issue keys. Does NOT auto-save — caller persists as needed.
 */
export function batchIssue(
  brand: Brand,
  tier: LicenseTier,
  owner: string,
  count: number,
  expiryDays?: number,
): LicenseKey[] {
  return generateBatchKeys(brand, tier, owner, count, expiryDays);
}

/**
 * Delete a stored license for a brand. Returns true if removed.
 */
export function revokeKey(brand: Brand, store?: LicenseStore): boolean {
  return (store ?? defaultStore).remove(brand);
}

/**
 * Inspect a LicenseKey object and return a structured verify result.
 */
export function inspectKey(licenseKey: LicenseKey): VerifyResult {
  return verifyKey(licenseKey);
}

/**
 * Audit all stored licenses — returns status for each entry.
 */
export function auditStore(store?: LicenseStore): AuditEntry[] {
  const s = store ?? defaultStore;
  return s.listAll().map(({ brand, key }) => {
    const result = verifyKey(key);
    let status: AuditEntry['status'] = 'invalid';
    if (result.valid) status = 'valid';
    else if (result.reason === 'license expired') status = 'expired';
    return {
      brand,
      key: key.key,
      tier: key.tier,
      owner: key.owner,
      issuedAt: key.issuedAt,
      expiresAt: key.expiresAt,
      status,
    };
  });
}
