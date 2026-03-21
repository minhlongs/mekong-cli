/**
 * Rate Limit Service tests
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { RateLimitService } from '../src/services/rate-limit-service';

// Mock KV storage
class MockKV {
  private store: Map<string, any> = new Map();

  async get(key: string, type?: 'json'): Promise<any> {
    const value = this.store.get(key);
    if (type === 'json' && value) {
      return JSON.parse(JSON.stringify(value));
    }
    return value;
  }

  async put(key: string, value: string, options?: { expirationTtl?: number }): Promise<void> {
    this.store.set(key, JSON.parse(value));
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}

describe('RateLimitService', () => {
  let mockKV: MockKV;
  let rateLimitService: RateLimitService;

  beforeEach(() => {
    mockKV = new MockKV();
    rateLimitService = new RateLimitService({
      RATE_LIMIT_KV: mockKV as any,
      SESSION_KV: mockKV as any,
      DB: {} as any,
      JWT_SECRET=REDACTED: 'test-secret',
      POLAR_WEBHOOK_SECRET: 'test-webhook-secret',
      ENVIRONMENT: 'test',
      LOG_LEVEL: 'debug',
      AI: {} as any,
      TELEGRAM_BOT_TOKEN: 'test-bot-token',
    });
  });

  describe('checkLimit', () => {
    it('should allow requests when under limit (starter tier)', async () => {
      const result = await rateLimitService.checkLimit('tenant-1', 'starter');

      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(29); // starter: 30 - 1
      expect(result.resetAt).toBeDefined();
    });

    it('should allow requests for pro tier with higher limit', async () => {
      const result = await rateLimitService.checkLimit('tenant-2', 'pro');

      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(59); // pro: 60 - 1
    });

    it('should allow requests for enterprise tier with highest limit', async () => {
      const result = await rateLimitService.checkLimit('tenant-3', 'enterprise');

      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(999); // enterprise: 1000 - 1
    });

    it('should deny requests when limit exceeded', async () => {
      const tenantId = 'rate-limited-tenant';

      // Exhaust all tokens
      for (let i = 0; i < 30; i++) {
        await rateLimitService.checkLimit(tenantId, 'starter');
      }

      // Next request should be denied
      const result = await rateLimitService.checkLimit(tenantId, 'starter');

      expect(result.allowed).toBe(false);
      expect(result.remaining).toBe(0);
      expect(result.retryAfter).toBeDefined();
      expect(result.retryAfter!).toBeGreaterThan(0);
    });

    it.skip('should refill tokens over time — minute-window based', async () => {
      const tenantId = 'refill-tenant';

      // Use some tokens
      for (let i = 0; i < 20; i++) {
        await rateLimitService.checkLimit(tenantId, 'starter');
      }

      const firstResult = await rateLimitService.checkLimit(tenantId, 'starter');
      expect(firstResult.remaining).toBeLessThan(50);

      // Simulate time passing by manually updating KV
      const key = `rl:${tenantId}`;
      const bucketData = await mockKV.get(key, 'json');
      if (bucketData) {
        // Move lastRefill back by 10 seconds (should add ~16 tokens at 1.67/sec)
        bucketData.lastRefill = Date.now() - (10 * 1000);
        await mockKV.put(key, JSON.stringify(bucketData));
      }

      const result = await rateLimitService.checkLimit(tenantId, 'starter');
      expect(result.remaining).toBeGreaterThan(firstResult.remaining);
    });

    it('should default to starter tier for unknown tiers', async () => {
      const result = await rateLimitService.checkLimit('unknown-tier-tenant', 'unknown');

      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(9); // Defaults to free: 10 - 1
    });

    it('should handle concurrent requests correctly', async () => {
      const tenantId = 'concurrent-tenant';

      // Make 10 concurrent requests
      const promises = Array.from({ length: 10 }, () =>
        rateLimitService.checkLimit(tenantId, 'starter')
      );

      const results = await Promise.all(promises);
      const allowed = results.filter(r => r.allowed);

      // All should be allowed (10 << 100 limit)
      expect(allowed.length).toBe(10);
    });
  });

  describe('getStatus', () => {
    it('should return full capacity for new tenant', async () => {
      const result = await rateLimitService.getStatus('new-tenant', 'starter');

      expect(result.allowed).toBe(true);
      expect(result.remaining).toBe(30);
    });

    it('should return current status without consuming tokens', async () => {
      const tenantId = 'status-check-tenant';

      // Make a request
      await rateLimitService.checkLimit(tenantId, 'starter');

      // Check status twice - should return same remaining
      const status1 = await rateLimitService.getStatus(tenantId, 'starter');
      const status2 = await rateLimitService.getStatus(tenantId, 'starter');

      expect(status1.remaining).toBe(status2.remaining);
    });
  });

  describe('reset', () => {
    it('should reset rate limit for tenant', async () => {
      const tenantId = 'reset-tenant';

      // Use some tokens
      for (let i = 0; i < 20; i++) {
        await rateLimitService.checkLimit(tenantId, 'starter');
      }

      const beforeReset = await rateLimitService.getStatus(tenantId, 'starter');
      expect(beforeReset.remaining).toBeLessThan(30);

      // Reset
      await rateLimitService.reset(tenantId);

      const afterReset = await rateLimitService.getStatus(tenantId, 'starter');
      expect(afterReset.remaining).toBe(30);
    });
  });
});
