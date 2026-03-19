/**
 * raas-dashboard.ts — Summary dashboard endpoint for RaaS
 * Aggregates: total tenants, revenue estimate, health score.
 */
import { TIER_CONFIGS } from './raas-pricing.js';
import type { RaasTier } from './raas-pricing.js';
import { getUsageLog } from './raas-gateway.js';
import { checkHealth } from './raas-health.js';
import { getBillingLog } from './raas-billing.js';
import type { ApiResponse } from './raas-api.js';

// --- Types ---

export interface DashboardSummary {
  totalTenants: number;
  activeTenants: number;
  revenueEstimateUsd: number;
  totalCreditsUsed: number;
  totalApiCalls: number;
  healthScore: number; // 0-100
  topTier: RaasTier;
  timestamp: number;
}

// --- Tenant tracking (in-memory) ---

const registeredTenants = new Map<string, RaasTier>();

/** Track a tenant registration for dashboard metrics */
export function trackTenantForDashboard(tenantId: string, tier: RaasTier): void {
  registeredTenants.set(tenantId, tier);
}

/** Remove tenant from dashboard tracking */
export function untrackTenant(tenantId: string): void {
  registeredTenants.delete(tenantId);
}

// --- Core Functions ---

/** Get full dashboard summary */
export function getDashboardSummary(): ApiResponse<DashboardSummary> {
  const tenantCount = registeredTenants.size;
  const tierCounts = new Map<RaasTier, number>();

  for (const tier of registeredTenants.values()) {
    tierCounts.set(tier, (tierCounts.get(tier) || 0) + 1);
  }

  // Revenue estimate: sum of tier prices for all tenants
  let revenueEstimate = 0;
  for (const [tier, count] of tierCounts) {
    revenueEstimate += TIER_CONFIGS[tier].priceUsd * count;
  }

  // Usage stats from billing log
  const billingEvents = getBillingLog();
  const totalCreditsUsed = billingEvents
    .filter(e => e.success)
    .reduce((sum, e) => sum + e.creditsCost, 0);

  // Health score: 25 per healthy component
  const health = checkHealth();
  const healthScore = health.data
    ? health.data.components.filter(c => c.status === 'healthy').length * 25
    : 0;

  // Top tier by count
  let topTier: RaasTier = 'starter';
  let maxCount = 0;
  for (const [tier, count] of tierCounts) {
    if (count > maxCount) { topTier = tier; maxCount = count; }
  }

  return {
    ok: true,
    status: 200,
    data: {
      totalTenants: tenantCount,
      activeTenants: tenantCount, // all registered = active for now
      revenueEstimateUsd: revenueEstimate,
      totalCreditsUsed,
      totalApiCalls: billingEvents.length,
      healthScore,
      topTier,
      timestamp: Date.now(),
    },
  };
}
