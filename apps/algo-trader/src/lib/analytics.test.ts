/**
 * Analytics Tests
 */

import {
  recordUsage,
  recordRateLimitHit,
  getTenantMetrics,
  getAnalyticsSummary,
  getRateLimitAnalytics,
  MetricsStore,
} from '../lib/analytics';

// Access store for testing
const store = new MetricsStore();

describe('Analytics', () => {
  beforeEach(() => {
    store.reset();
  });

  describe('recordUsage', () => {
    it('records usage for tenant', () => {
      recordUsage('tenant-1', '/api/test');
      recordUsage('tenant-1', '/api/test');
      recordUsage('tenant-1', '/api/other');

      const usage = store.getUsage('tenant-1');
      expect(usage.count).toBe(3);
      expect(usage.endpoints['/api/test']).toBe(2);
      expect(usage.endpoints['/api/other']).toBe(1);
    });
  });

  describe('recordRateLimitHit', () => {
    it('records rate limit hit', () => {
      recordRateLimitHit('tenant-1');
      recordRateLimitHit('tenant-1');

      const hits = store.getRateLimitHits('tenant-1');
      expect(hits).toBe(2);
    });
  });

  describe('getTenantMetrics', () => {
    it('returns tenant metrics', async () => {
      recordUsage('tenant-1', '/api/test');
      recordUsage('tenant-1', '/api/test');
      recordRateLimitHit('tenant-1');

      const metrics = await getTenantMetrics('tenant-1');

      expect(metrics.tenantId).toBe('tenant-1');
      expect(metrics.usage.total).toBeGreaterThanOrEqual(2);
      expect(metrics.rateLimits.hits).toBe(1);
    });
  });

  describe('getAnalyticsSummary', () => {
    it('returns aggregated summary', async () => {
      recordUsage('tenant-1', '/api/test');
      recordUsage('tenant-2', '/api/other');
      recordUsage('tenant-2', '/api/test');

      const summary = await getAnalyticsSummary();

      expect(summary.totalTenants).toBeGreaterThan(0);
      expect(summary.topEndpoints).toBeDefined();
    });
  });

  describe('getRateLimitAnalytics', () => {
    it('returns rate limit stats', async () => {
      recordRateLimitHit('tenant-1');
      recordRateLimitHit('tenant-2');
      recordRateLimitHit('tenant-2');

      const limits = await getRateLimitAnalytics();

      expect(limits.totalHits).toBe(3);
      expect(limits.byTenant['tenant-1']).toBe(1);
      expect(limits.byTenant['tenant-2']).toBe(2);
    });
  });
});
