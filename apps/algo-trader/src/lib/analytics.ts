/**
 * Usage Analytics API - Phase 2C
 *
 * Collects and serves usage metrics for RaaS dashboard.
 */

import { UsageQuotaService, QUOTA_LIMITS } from '../lib/usage-quota';
import { LicenseService, LicenseTier } from '../lib/raas-gate';

/**
 * Usage metrics for a tenant
 */
export interface TenantUsageMetrics {
  tenantId: string;
  tier: string;
  period: {
    start: string;
    end: string;
  };
  usage: {
    total: number;
    limit: number;
    remaining: number;
    percentUsed: number;
  };
  rateLimits: {
    hits: number;
    byEndpoint: Record<string, number>;
  };
  revenue: {
    monthly: number;
    projected: number;
  };
}

/**
 * Aggregated analytics
 */
export interface AnalyticsSummary {
  totalTenants: number;
  activeTenants: number;
  totalRevenue: number;
  usageByTier: Record<string, number>;
  topEndpoints: Array<{ endpoint: string; hits: number }>;
}

/**
 * In-memory metrics store (production: use TimescaleDB/ClickHouse)
 */
export class MetricsStore {
  private usageData: Map<string, { count: number; endpoints: Record<string, number> }> = new Map();
  private rateLimitHits: Map<string, number> = new Map();

  incrementUsage(tenantId: string, endpoint: string): void {
    const data = this.usageData.get(tenantId) || { count: 0, endpoints: {} };
    data.count += 1;
    data.endpoints[endpoint] = (data.endpoints[endpoint] || 0) + 1;
    this.usageData.set(tenantId, data);
  }

  incrementRateLimit(tenantId: string): void {
    const count = this.rateLimitHits.get(tenantId) || 0;
    this.rateLimitHits.set(tenantId, count + 1);
  }

  getUsage(tenantId: string): { count: number; endpoints: Record<string, number> } {
    return this.usageData.get(tenantId) || { count: 0, endpoints: {} };
  }

  getRateLimitHits(tenantId: string): number {
    return this.rateLimitHits.get(tenantId) || 0;
  }

  getAllTenants(): string[] {
    return Array.from(this.usageData.keys());
  }

  reset(): void {
    this.usageData.clear();
    this.rateLimitHits.clear();
  }
}

const metricsStore = new MetricsStore();

/**
 * Record API usage for a tenant
 */
export function recordUsage(tenantId: string, endpoint: string): void {
  metricsStore.incrementUsage(tenantId, endpoint);
}

/**
 * Record rate limit hit
 */
export function recordRateLimitHit(tenantId: string): void {
  metricsStore.incrementRateLimit(tenantId);
}

/**
 * Get usage metrics for a tenant
 */
export async function getTenantMetrics(tenantId: string): Promise<TenantUsageMetrics> {
  const quotaService = UsageQuotaService.getInstance();
  const licenseService = LicenseService.getInstance();

  const tier = licenseService.getTier();
  const quota = await quotaService.getUsage(tenantId, tier);
  const usage = metricsStore.getUsage(tenantId);
  const rateLimitHits = metricsStore.getRateLimitHits(tenantId);

  const pricing = {
    free: 0,
    pro: 99,
    enterprise: 499,
  };

  return {
    tenantId,
    tier,
    period: {
      start: quota.periodStart.toISOString(),
      end: quota.periodEnd.toISOString(),
    },
    usage: {
      total: quota.used,
      limit: quota.limit,
      remaining: quota.remaining,
      percentUsed: quota.percentUsed,
    },
    rateLimits: {
      hits: rateLimitHits,
      byEndpoint: usage.endpoints,
    },
    revenue: {
      monthly: pricing[tier as keyof typeof pricing] || 0,
      projected: pricing[tier as keyof typeof pricing] || 0,
    },
  };
}

/**
 * Get analytics summary across all tenants
 */
export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const tenants = metricsStore.getAllTenants();
  const quotaService = UsageQuotaService.getInstance();

  let totalRevenue = 0;
  const usageByTier: Record<string, number> = { free: 0, pro: 0, enterprise: 0 };
  const endpointHits: Record<string, number> = {};

  for (const tenantId of tenants) {
    const tier = LicenseService.getInstance().getTier();
    usageByTier[tier] = (usageByTier[tier] || 0) + 1;

    const pricing = { free: 0, pro: 99, enterprise: 499 };
    totalRevenue += pricing[tier as keyof typeof pricing] || 0;

    const usage = metricsStore.getUsage(tenantId);
    for (const [endpoint, hits] of Object.entries(usage.endpoints)) {
      endpointHits[endpoint] = (endpointHits[endpoint] || 0) + hits;
    }
  }

  const topEndpoints = Object.entries(endpointHits)
    .map(([endpoint, hits]) => ({ endpoint, hits }))
    .sort((a, b) => b.hits - a.hits)
    .slice(0, 10);

  return {
    totalTenants: tenants.length,
    activeTenants: tenants.filter(t => metricsStore.getUsage(t).count > 0).length,
    totalRevenue,
    usageByTier,
    topEndpoints,
  };
}

/**
 * Get rate limit analytics
 */
export async function getRateLimitAnalytics(): Promise<{
  totalHits: number;
  byTenant: Record<string, number>;
}> {
  const tenants = metricsStore.getAllTenants();
  const byTenant: Record<string, number> = {};
  let totalHits = 0;

  for (const tenantId of tenants) {
    const hits = metricsStore.getRateLimitHits(tenantId);
    byTenant[tenantId] = hits;
    totalHits += hits;
  }

  return { totalHits, byTenant };
}
