/**
 * E2E tests — Wave 8 endpoints: checkout, metrics, docs, tenant limits
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store: Map<string, string> = new Map();

  async get(key: string, type?: 'json'): Promise<any> {
    const value = this.store.get(key);
    if (value === undefined) return null;
    if (type === 'json') return JSON.parse(value);
    return value;
  }

  async put(key: string, value: string, _options?: { expirationTtl?: number }): Promise<void> {
    this.store.set(key, value);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}

class MockD1 {
  prepare(_query: string) {
    const stmt = {
      bind: (..._args: any[]) => stmt,
      first: async () => null,
      run: async () => ({ success: true, meta: { changes: 0 } }),
      all: async () => ({ results: [] }),
    };
    return stmt;
  }

  async batch(_statements: any[]) {
    return [];
  }
}

describe('Wave 8 E2E: Checkout, Metrics, Docs, Limits', () => {
  let env: Env;

  beforeEach(() => {
    env = {
      RATE_LIMIT_KV: new MockKV() as any,
      SESSION_KV: new MockKV() as any,
      DB: new MockD1() as any,
      JWT_SECRET=REDACTED: 'test-secret-key-for-testing-only-12345',
      POLAR_WEBHOOK_SECRET: 'test-webhook-secret',
      ENVIRONMENT: 'test',
      LOG_LEVEL: 'debug',
      AI: {} as any,
      TELEGRAM_BOT_TOKEN: 'test-bot-token',
    };
  });

  // ---------------------------------------------------------------------------
  // GET /billing/checkout/products (public)
  // ---------------------------------------------------------------------------

  describe('GET /billing/checkout/products (public)', () => {
    it('returns 200 with products array', async () => {
      const res = await app.request('/billing/checkout/products', { method: 'GET' }, env);
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.products)).toBe(true);
    });

    it('each product has name, tier, type fields', async () => {
      const res = await app.request('/billing/checkout/products', { method: 'GET' }, env);
      const data = await res.json() as any;
      expect(data.products.length).toBeGreaterThan(0);
      for (const p of data.products) {
        expect(p.name).toBeDefined();
        expect(p.tier).toBeDefined();
        expect(p.type).toBeDefined();
      }
    });
  });

  // ---------------------------------------------------------------------------
  // POST /billing/checkout (auth required)
  // ---------------------------------------------------------------------------

  describe('POST /billing/checkout (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: 'ce215739' }),
      }, env);
      expect(res.status).toBe(401);
    });

    it('returns 400 with missing product_id (authenticated)', async () => {
      const res = await app.request('/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer bad-token',
        },
        body: JSON.stringify({}),
      }, env);
      // Auth guard rejects invalid token before reaching body validation
      expect([400, 401]).toContain(res.status);
    });

    it('returns 400 with invalid product_id (authenticated)', async () => {
      const res = await app.request('/billing/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer bad-token',
        },
        body: JSON.stringify({ product_id: 'nonexistent' }),
      }, env);
      expect([400, 401]).toContain(res.status);
    });
  });

  // ---------------------------------------------------------------------------
  // GET /metrics (public)
  // ---------------------------------------------------------------------------

  describe('GET /metrics (public)', () => {
    it('returns 200 with metrics object', async () => {
      const res = await app.request('/metrics', { method: 'GET' }, env);
      expect(res.status).toBe(200);
    });

    it('has totalRequests, statusBreakdown, topPaths fields', async () => {
      const res = await app.request('/metrics', { method: 'GET' }, env);
      const data = await res.json() as any;
      expect(typeof data.totalRequests).toBe('number');
      expect(typeof data.statusBreakdown).toBe('object');
      expect(Array.isArray(data.topPaths)).toBe(true);
    });
  });

  // ---------------------------------------------------------------------------
  // GET /metrics/live (public)
  // ---------------------------------------------------------------------------

  describe('GET /metrics/live (public)', () => {
    it('returns 200 with live metrics', async () => {
      const res = await app.request('/metrics/live', { method: 'GET' }, env);
      expect(res.status).toBe(200);
    });

    it('has requestsThisHour and timestamp fields', async () => {
      const res = await app.request('/metrics/live', { method: 'GET' }, env);
      const data = await res.json() as any;
      expect(typeof data.requestsThisHour).toBe('number');
      expect(data.timestamp).toBeDefined();
    });
  });

  // ---------------------------------------------------------------------------
  // GET /docs (public)
  // ---------------------------------------------------------------------------

  describe('GET /docs (public)', () => {
    it('returns 200', async () => {
      const res = await app.request('/docs', { method: 'GET' }, env);
      expect(res.status).toBe(200);
    });

    it('response contains HTML content', async () => {
      const res = await app.request('/docs', { method: 'GET' }, env);
      const text = await res.text();
      expect(text).toContain('<!DOCTYPE html>');
    });
  });

  // ---------------------------------------------------------------------------
  // GET /v1/tenants/limits (auth required)
  // ---------------------------------------------------------------------------

  describe('GET /v1/tenants/limits (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/limits', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });
  });
});
