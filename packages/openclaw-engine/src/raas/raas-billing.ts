/**
 * raas-billing.ts — Credit billing engine with usage analytics
 * Tracks per-tenant credit consumption, auto-throttle, monthly reset.
 */
import { getTenant, validateAndMeter, recordUsage, getUsageLog } from './raas-gateway.js';
import type { MeteringResult } from './raas-gateway.js';
import type { ApiResponse } from './raas-api.js';
import type { RaasTier } from './raas-pricing.js';

// --- Types ---

export interface BillingEvent {
  tenantId: string;
  command: string;
  creditsCost: number;
  timestamp: number;
  latencyMs: number;
  success: boolean;
  throttled: boolean;
}

export interface UsageAnalytics {
  tenantId: string;
  totalCalls: number;
  successfulCalls: number;
  creditsUsed: number;
  avgLatencyMs: number;
  throttledCount: number;
  periodStart: number;
}

// --- In-memory billing store ---

const billingLog: BillingEvent[] = [];
const monthlyResetTimestamps = new Map<string, number>();

// --- Core Functions ---

/** Execute a billable command: validate → meter → record → return result */
export function executeBillableCommand(
  tenantId: string,
  command: string,
  creditsCost: number,
  latencyMs: number,
): ApiResponse<MeteringResult & { throttled: boolean }> {
  const startTs = Date.now();

  // Check if tenant exists
  const tenant = getTenant(tenantId);
  if (!tenant) {
    return { ok: false, status: 404, error: 'Tenant not found' };
  }

  // Validate and meter
  const meter = validateAndMeter(tenantId, creditsCost);
  const throttled = !meter.allowed;

  // Record billing event
  const event: BillingEvent = {
    tenantId,
    command,
    creditsCost: throttled ? 0 : creditsCost,
    timestamp: startTs,
    latencyMs,
    success: meter.allowed,
    throttled,
  };
  billingLog.push(event);

  if (throttled) {
    return {
      ok: false,
      status: 429,
      error: `Throttled: ${meter.reason}`,
      data: { ...meter, throttled: true },
    };
  }

  // Record usage for audit trail
  recordUsage({
    tenantId,
    command,
    creditsCost,
    timestamp: startTs,
    success: true,
  });

  return { ok: true, status: 200, data: { ...meter, throttled: false } };
}

/** Get usage analytics for a tenant in current billing period */
export function getUsageAnalytics(tenantId: string): ApiResponse<UsageAnalytics> {
  const resetTs = monthlyResetTimestamps.get(tenantId) ?? 0;
  const events = billingLog.filter(e => e.tenantId === tenantId && e.timestamp >= resetTs);

  if (events.length === 0) {
    return {
      ok: true,
      status: 200,
      data: {
        tenantId,
        totalCalls: 0,
        successfulCalls: 0,
        creditsUsed: 0,
        avgLatencyMs: 0,
        throttledCount: 0,
        periodStart: resetTs || Date.now(),
      },
    };
  }

  const successful = events.filter(e => e.success);
  const totalLatency = events.reduce((sum, e) => sum + e.latencyMs, 0);

  return {
    ok: true,
    status: 200,
    data: {
      tenantId,
      totalCalls: events.length,
      successfulCalls: successful.length,
      creditsUsed: successful.reduce((sum, e) => sum + e.creditsCost, 0),
      avgLatencyMs: Math.round(totalLatency / events.length),
      throttledCount: events.filter(e => e.throttled).length,
      periodStart: resetTs || events[0].timestamp,
    },
  };
}

/** Monthly reset: clear used credits for a tenant */
export function monthlyReset(tenantId: string): ApiResponse<{ reset: boolean }> {
  const tenant = getTenant(tenantId);
  if (!tenant) {
    return { ok: false, status: 404, error: 'Tenant not found' };
  }
  tenant.usedCredits = 0;
  monthlyResetTimestamps.set(tenantId, Date.now());
  return { ok: true, status: 200, data: { reset: true } };
}

/** Get billing log for a tenant */
export function getBillingLog(tenantId?: string): BillingEvent[] {
  if (!tenantId) return [...billingLog];
  return billingLog.filter(e => e.tenantId === tenantId);
}
