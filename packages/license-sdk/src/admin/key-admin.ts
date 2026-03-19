import type { LicenseTier } from '../core/tiers.js';
import { type LicenseKey, generateKey, generateBatchKeys } from '../core/key-generator.js';

export type { LicenseKey };

/**
 * In-memory admin tool for batch key generation, revocation, and export.
 * For production use, back with a persistent store.
 */
export class KeyAdmin {
  private readonly generated = new Map<string, LicenseKey>();
  private readonly revoked = new Set<string>();

  /**
   * Generate `count` signed license keys for a given brand/tier/owner.
   */
  generateBatch(
    brand: string,
    tier: string,
    owner: string,
    count: number
  ): LicenseKey[] {
    if (count < 1 || count > 1000) {
      throw new RangeError('count must be between 1 and 1000');
    }

    const keys = generateBatchKeys(brand as any, tier as LicenseTier, owner, count);

    for (const record of keys) {
      this.generated.set(record.key, record);
    }

    return keys;
  }

  /**
   * Generate a single key and track it.
   */
  generateOne(brand: string, tier: string, owner: string, expiryDays?: number): LicenseKey {
    const record = generateKey(brand as any, tier as LicenseTier, owner, expiryDays);
    this.generated.set(record.key, record);
    return record;
  }

  /**
   * Revoke a key. Returns false if already revoked.
   */
  revokeKey(key: string): boolean {
    if (this.revoked.has(key)) return false;
    this.revoked.add(key);
    return true;
  }

  isRevoked(key: string): boolean {
    return this.revoked.has(key);
  }

  /**
   * All generated keys that have not been revoked.
   */
  listActive(): LicenseKey[] {
    return Array.from(this.generated.values()).filter(
      (record) => !this.revoked.has(record.key)
    );
  }

  /**
   * Export all active keys as JSON or CSV string.
   */
  exportKeys(format: 'json' | 'csv'): string {
    const active = this.listActive();

    if (format === 'json') {
      return JSON.stringify(active, null, 2);
    }

    // CSV — use issuedAt from core's LicenseKey shape
    const header = 'key,brand,tier,owner,issuedAt,expiresAt';
    const rows = active.map((r) =>
      [r.key, r.brand, r.tier, r.owner, r.issuedAt, r.expiresAt ?? '']
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(',')
    );
    return [header, ...rows].join('\n');
  }
}
