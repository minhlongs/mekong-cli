/**
 * E2E tests — Billing and Credits endpoints
 * Billing pricing is public; credits routes require auth.
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

describe('Billing and Credits E2E', () => {
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
  // Public billing endpoints
  // ---------------------------------------------------------------------------

  describe('GET /billing/pricing (public)', () => {
    it('returns 200 with tier pricing', async () => {
      const res = await app.request('/billing/pricing', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.tiers)).toBe(true);
    });

    it('includes free tier in pricing', async () => {
      const res = await app.request('/billing/pricing', { method: 'GET' }, env);
      const data = await res.json() as any;

      const ids = data.tiers.map((t: any) => t.id);
      expect(ids).toContain('free');
    });

    it('each tier has required fields', async () => {
      const res = await app.request('/billing/pricing', { method: 'GET' }, env);
      const data = await res.json() as any;

      for (const tier of data.tiers) {
        expect(tier.id).toBeDefined();
        expect(tier.name).toBeDefined();
        expect(typeof tier.price).toBe('number');
        expect(typeof tier.credits).toBe('number');
      }
    });

    it('includes credit_costs mapping', async () => {
      const res = await app.request('/billing/pricing', { method: 'GET' }, env);
      const data = await res.json() as any;

      expect(data.credit_costs).toBeDefined();
      expect(data.credit_costs.simple).toBe(1);
      expect(data.credit_costs.standard).toBe(3);
      expect(data.credit_costs.complex).toBe(5);
    });

    it('includes credit_packs array', async () => {
      const res = await app.request('/billing/pricing', { method: 'GET' }, env);
      const data = await res.json() as any;

      expect(Array.isArray(data.credit_packs)).toBe(true);
      expect(data.credit_packs.length).toBeGreaterThan(0);
    });
  });

  describe('GET /billing/webhook/status (public)', () => {
    it('returns webhook service status', async () => {
      const res = await app.request('/billing/webhook/status', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
    });
  });

  // ---------------------------------------------------------------------------
  // Protected credits endpoints
  // ---------------------------------------------------------------------------

  describe('GET /credits (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/credits', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 401 with invalid token', async () => {
      const res = await app.request('/credits', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer not-a-real-jwt' },
      }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('GET /credits/history (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/credits/history', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('POST /credits/check (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/credits/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ complexity: 'simple' }),
      }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('POST /billing/webhook (public with signature)', () => {
    it('returns 401 for missing signature', async () => {
      const res = await app.request('/billing/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'order.paid', data: {} }),
      }, env);

      // Invalid/missing signature → 401
      expect(res.status).toBe(401);
    });
  });
});
