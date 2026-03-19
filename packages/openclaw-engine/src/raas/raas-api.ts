/**
 * raas-api.ts — REST-style API handlers for RaaS
 * Designed as pure functions — can be wired to any HTTP framework.
 */
import { validateAndMeter, getTenant, registerTenant, getUsageLog, recordUsage } from './raas-gateway.js';
import type { TenantLicense, MeteringResult } from './raas-gateway.js';
import { TIER_CONFIGS, calculateMonthlyCost } from './raas-pricing.js';
import type { RaasTier } from './raas-pricing.js';

export interface ApiResponse<T = unknown> {
  ok: boolean;
  status: number;
  data?: T;
  error?: string;
}

/** POST /raas/validate — validate a command execution request */
export function handleValidate(tenantId: string, command: string, creditsCost: number): ApiResponse<MeteringResult> {
  const result = validateAndMeter(tenantId, creditsCost);
  if (!result.allowed) {
    const status = result.reason?.includes('402') ? 402 : 403;
    return { ok: false, status, error: result.reason, data: result };
  }
  recordUsage({ tenantId, command, creditsCost, timestamp: Date.now(), success: true });
  return { ok: true, status: 200, data: result };
}

/** GET /raas/balance/:tenantId — check remaining credits */
export function handleGetBalance(tenantId: string): ApiResponse<{ tier: RaasTier; used: number; remaining: number; limit: number }> {
  const tenant = getTenant(tenantId);
  if (!tenant) {
    return { ok: false, status: 404, error: 'Tenant not found' };
  }
  const config = TIER_CONFIGS[tenant.tier];
  const limit = config.creditsPerMonth;
  const remaining = limit === -1 ? Infinity : limit - tenant.usedCredits;
  return { ok: true, status: 200, data: { tier: tenant.tier, used: tenant.usedCredits, remaining, limit } };
}

/** POST /raas/tenant — register or update a tenant license */
export function handleRegisterTenant(license: TenantLicense): ApiResponse<{ tenantId: string }> {
  if (!license.tenantId || !license.tier) {
    return { ok: false, status: 400, error: 'Missing tenantId or tier' };
  }
  if (!(license.tier in TIER_CONFIGS)) {
    return { ok: false, status: 400, error: `Invalid tier: ${license.tier}` };
  }
  registerTenant(license);
  return { ok: true, status: 201, data: { tenantId: license.tenantId } };
}

/** GET /raas/usage/:tenantId — usage history and monthly cost */
export function handleGetUsage(tenantId: string): ApiResponse<{ records: number; monthlyCost: number }> {
  const records = getUsageLog(tenantId);
  return { ok: true, status: 200, data: { records: records.length, monthlyCost: calculateMonthlyCost(records) } };
}

/** GET /raas/tiers — list all available tiers */
export function handleListTiers(): ApiResponse<typeof TIER_CONFIGS> {
  return { ok: true, status: 200, data: TIER_CONFIGS };
}
