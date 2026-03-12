/**
 * TierManager — upgrade/downgrade license tier with prorated expiry.
 * Phase 4 of v0.5 License Admin.
 */
import type { LicenseTier, LicenseKey } from './types.js';
import { TIER_ORDER } from './types.js';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import { generateKey } from './key-generator.js';

export interface TierChangeResult {
  newKey: LicenseKey;
  oldKey: LicenseKey;
  direction: 'upgrade' | 'downgrade' | 'same';
  remainingDays: number;
}

/**
 * Change tier of an existing key.
 * Prorated expiry: remaining days from old key carried over to new key.
 */
export function changeTier(existing: LicenseKey, newTier: LicenseTier): Result<TierChangeResult, Error> {
  if (existing.status === 'revoked') {
    return err(new Error('Cannot change tier of a revoked key.'));
  }

  const remainingMs = Math.max(0, new Date(existing.expiresAt).getTime() - Date.now());
  const remainingDays = Math.max(1, Math.ceil(remainingMs / 86_400_000));

  const oldIdx = TIER_ORDER.indexOf(existing.tier);
  const newIdx = TIER_ORDER.indexOf(newTier);
  const direction: TierChangeResult['direction'] =
    newIdx > oldIdx ? 'upgrade' : newIdx < oldIdx ? 'downgrade' : 'same';

  const newKey = generateKey({ tier: newTier, owner: existing.owner, expiryDays: remainingDays });
  const revokedOld: LicenseKey = { ...existing, status: 'revoked' };

  return ok({ newKey, oldKey: revokedOld, direction, remainingDays });
}

/** Convenience: upgrade only — returns error if new tier is not higher */
export function upgradeTier(existing: LicenseKey, newTier: LicenseTier): Result<TierChangeResult, Error> {
  const oldIdx = TIER_ORDER.indexOf(existing.tier);
  const newIdx = TIER_ORDER.indexOf(newTier);
  if (newIdx <= oldIdx) {
    return err(new Error(`${newTier} is not higher than current tier ${existing.tier}`));
  }
  return changeTier(existing, newTier);
}

/** Convenience: downgrade only — returns error if new tier is not lower */
export function downgradeTier(existing: LicenseKey, newTier: LicenseTier): Result<TierChangeResult, Error> {
  const oldIdx = TIER_ORDER.indexOf(existing.tier);
  const newIdx = TIER_ORDER.indexOf(newTier);
  if (newIdx >= oldIdx) {
    return err(new Error(`${newTier} is not lower than current tier ${existing.tier}`));
  }
  return changeTier(existing, newTier);
}
