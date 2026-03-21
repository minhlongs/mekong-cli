/**
 * E2E tests — Marketplace and Templates endpoints
 * All marketplace gallery routes are public (no auth).
 * Mission templates require auth (under /v1).
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

describe('Marketplace and Templates E2E', () => {
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
  // Public marketplace gallery
  // ---------------------------------------------------------------------------

  describe('GET /marketplace (public)', () => {
    it('returns 200 with missions array', async () => {
      const res = await app.request('/marketplace', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.missions)).toBe(true);
      expect(typeof data.total).toBe('number');
    });

    it('returns pagination metadata', async () => {
      const res = await app.request('/marketplace', { method: 'GET' }, env);
      const data = await res.json() as any;

      expect(data.pagination).toBeDefined();
      expect(typeof data.pagination.limit).toBe('number');
      expect(typeof data.pagination.offset).toBe('number');
    });

    it('accepts limit and offset query params', async () => {
      const res = await app.request('/marketplace?limit=5&offset=10', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.pagination.limit).toBe(5);
      expect(data.pagination.offset).toBe(10);
    });

    it('accepts search query param', async () => {
      const res = await app.request('/marketplace?q=blog+post', { method: 'GET' }, env);
      expect(res.status).toBe(200);
    });

    it('accepts complexity filter param', async () => {
      const res = await app.request('/marketplace?complexity=simple', { method: 'GET' }, env);
      expect(res.status).toBe(200);
    });

    it('enforces max limit of 50', async () => {
      const res = await app.request('/marketplace?limit=9999', { method: 'GET' }, env);
      const data = await res.json() as any;
      expect(data.pagination.limit).toBeLessThanOrEqual(50);
    });
  });

  describe('GET /marketplace/featured (public)', () => {
    it('returns 200 with featured array', async () => {
      const res = await app.request('/marketplace/featured', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.featured)).toBe(true);
    });
  });

  describe('GET /marketplace/stats (public)', () => {
    it('returns 200 with marketplace statistics', async () => {
      const res = await app.request('/marketplace/stats', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      // Returns stats object or empty object — both valid
      const data = await res.json() as any;
      expect(data).toBeDefined();
    });
  });

  describe('GET /marketplace/leaderboard (public)', () => {
    it('returns 200 with leaderboard array', async () => {
      const res = await app.request('/marketplace/leaderboard', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.leaderboard)).toBe(true);
    });
  });

  describe('GET /marketplace/:id/reviews (public)', () => {
    it('returns 200 with reviews and average rating', async () => {
      const res = await app.request('/marketplace/some-mission-id/reviews', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.reviews)).toBe(true);
      expect(typeof data.avgRating).toBe('number');
      expect(typeof data.totalReviews).toBe('number');
    });
  });

  describe('POST /marketplace/:id/reviews (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/marketplace/some-mission-id/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: 5, comment: 'Great mission!' }),
      }, env);

      expect(res.status).toBe(401);
    });
  });

  // ---------------------------------------------------------------------------
  // Mission templates (under /v1, require auth)
  // ---------------------------------------------------------------------------

  describe('GET /v1/missions/templates (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/missions/templates', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 401 with invalid token', async () => {
      const res = await app.request('/v1/missions/templates', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer fake-token' },
      }, env);
      expect(res.status).toBe(401);
    });
  });

  // ---------------------------------------------------------------------------
  // Public share and stats routes
  // ---------------------------------------------------------------------------

  describe('GET /stats (public)', () => {
    it('returns 200 with public platform stats', async () => {
      const res = await app.request('/stats', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(typeof data.tenants).toBe('number');
      expect(typeof data.missionsCompleted).toBe('number');
    });
  });
});
