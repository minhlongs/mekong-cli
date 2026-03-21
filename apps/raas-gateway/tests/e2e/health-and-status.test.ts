/**
 * E2E tests — Health and Status endpoints (all public, no auth required)
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
  // prepare() must be synchronous — routes chain .bind().all() immediately
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

describe('Health and Status E2E', () => {
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

  describe('GET /health', () => {
    it('returns 200 with status healthy', async () => {
      const res = await app.request('/health', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
      expect(data.version).toBeDefined();
    });

    it('includes uptime field', async () => {
      const res = await app.request('/health', { method: 'GET' }, env);
      const data = await res.json() as any;
      expect(typeof data.uptime).toBe('number');
    });
  });

  describe('GET /health/live', () => {
    it('returns 200 alive status', async () => {
      const res = await app.request('/health/live', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.status).toBe('alive');
    });
  });

  describe('GET /health/ready', () => {
    it('returns readiness check result', async () => {
      const res = await app.request('/health/ready', { method: 'GET' }, env);

      // Either ready (200) or not_ready (503) — both are valid responses
      expect([200, 503]).toContain(res.status);
      const data = await res.json() as any;
      expect(data.status).toMatch(/ready|not_ready/);
    });
  });

  describe('GET /status', () => {
    it('returns system status with components', async () => {
      const res = await app.request('/status', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.status).toMatch(/operational|degraded|outage/);
      expect(Array.isArray(data.components)).toBe(true);
      expect(data.updatedAt).toBeDefined();
    });

    it('components include expected services', async () => {
      const res = await app.request('/status', { method: 'GET' }, env);
      const data = await res.json() as any;

      const names = data.components.map((c: any) => c.name);
      expect(names).toContain('API');
      expect(names).toContain('Database');
    });
  });

  describe('GET /status/incidents', () => {
    it('returns paginated incidents list', async () => {
      const res = await app.request('/status/incidents', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.incidents)).toBe(true);
      expect(typeof data.limit).toBe('number');
      expect(typeof data.offset).toBe('number');
    });

    it('accepts pagination query params', async () => {
      const res = await app.request('/status/incidents?limit=5&offset=0', { method: 'GET' }, env);
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.limit).toBe(5);
    });
  });

  describe('GET /status/history', () => {
    it('returns uptime history array', async () => {
      const res = await app.request('/status/history', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.history)).toBe(true);
    });
  });
});
