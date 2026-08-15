/**
 * raas-gateway.ts — License validation + credit metering gateway
 * Validates tenant license and meters credit usage before command execution.
 */
import { TIER_CONFIGS, hasCreditsRemaining } from './raas-pricing.js';
import type { RaasTier, UsageRecord } from './raas-pricing.js';

export interface TenantLicense {
  tenantId: string;
  tier: RaasTier;
  active: boolean;
  expiresAt: number; // epoch ms
  usedCredits: number;
}

export interface MeteringResult {
  allowed: boolean;
  reason?: string;
  remainingCredits: number;
  tenantId: string;
}

/** In-memory tenant store (production would use DB/KV) */
const tenants = new Map<string, TenantLicense>();

export function registerTenant(license: TenantLicense): void {
  tenants.set(license.tenantId, license);
}

export function getTenant(tenantId: string): TenantLicense | undefined {
  return tenants.get(tenantId);
}

/** Validate license and check credit budget before executing a command */
export function validateAndMeter(tenantId: string, creditsCost: number): MeteringResult {
  const license = tenants.get(tenantId);

  if (!license) {
    return { allowed: false, reason: 'Tenant not found', remainingCredits: 0, tenantId };
  }

  if (!license.active) {
    return { allowed: false, reason: 'License inactive', remainingCredits: 0, tenantId };
  }

  if (license.expiresAt > 0 && Date.now() > license.expiresAt) {
    return { allowed: false, reason: 'License expired', remainingCredits: 0, tenantId };
  }

  if (!hasCreditsRemaining(license.tier, license.usedCredits)) {
    return { allowed: false, reason: 'Credit limit reached (HTTP 402)', remainingCredits: 0, tenantId };
  }

  const config = TIER_CONFIGS[license.tier];
  const remaining = config.creditsPerMonth === -1
    ? Infinity
    : config.creditsPerMonth - license.usedCredits;

  if (remaining < creditsCost && remaining !== Infinity) {
    return { allowed: false, reason: `Insufficient credits: need ${creditsCost}, have ${remaining}`, remainingCredits: remaining, tenantId };
  }

  // Deduct credits
  license.usedCredits += creditsCost;

  const newRemaining = config.creditsPerMonth === -1
    ? Infinity
    : config.creditsPerMonth - license.usedCredits;

  return { allowed: true, remainingCredits: newRemaining, tenantId };
}

/** Record usage for audit trail */
const usageLog: UsageRecord[] = [];

export function recordUsage(record: UsageRecord): void {
  usageLog.push(record);
}

export function getUsageLog(tenantId?: string): UsageRecord[] {
  if (!tenantId) return [...usageLog];
  return usageLog.filter(r => r.tenantId === tenantId);
}

export function resetTenantUsage(tenantId: string): boolean {
  const license = tenants.get(tenantId);
  if (!license) return false;
  license.usedCredits = 0;
  return true;
}
