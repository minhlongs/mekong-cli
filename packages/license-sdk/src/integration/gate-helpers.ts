/**
 * Convenience helpers for embedding LicenseGate in applications.
 */

import { LicenseGate } from '../core/gate.js';
import { generateKey } from '../core/key-generator.js';
import { LicenseStore } from '../core/store.js';
import type { Brand, LicenseTier } from '../core/tiers.js';
import type { LicenseGateOptions, GateStatus } from '../core/gate.js';

export type { LicenseGateOptions, GateStatus };

/**
 * Create a LicenseGate pre-loaded from the default store.
 */
export function createGate(options: LicenseGateOptions): LicenseGate {
  return new LicenseGate(options);
}

/**
 * Activate a license from env var OPENCLAW_LICENSE_KEY_{BRAND}.
 * Returns gate status after activation attempt.
 */
export function activateFromEnv(
  brand: Brand,
  featureMap?: Record<string, LicenseTier>,
): GateStatus {
  const gate = new LicenseGate({ brand, featureMap });
  const keyStr = process.env[`OPENCLAW_LICENSE_KEY_${brand}`];
  if (keyStr) gate.activate(keyStr);
  return gate.getStatus();
}

/**
 * Throws if the command is not allowed for the current gate tier.
 */
export function requireAccess(gate: LicenseGate, command: string, required?: LicenseTier): void {
  const result = gate.canAccess(command, required);
  if (!result.allowed) {
    throw new Error(`[license-sdk] Access denied: ${result.reason}`);
  }
}

/**
 * Issue a trial key, save to store, and return the raw key string.
 */
export function issueTrialKey(
  brand: Brand,
  owner: string,
  tier: LicenseTier = 'starter',
  expiryDays = 14,
  store?: LicenseStore,
): string {
  const licenseKey = generateKey(brand, tier, owner, expiryDays);
  const s = store ?? new LicenseStore();
  s.save(brand, licenseKey);
  return licenseKey.key;
}
