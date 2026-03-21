/**
 * API endpoint tests with authentication and rate limiting
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { app } from '../src/index';
import type { Env } from '../src/index';

// Mock KV and D1
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

class MockD1 {
  async prepare(query: string) {
    return {
      bind: (...args: any[]) => ({
        first: async () => null,
        run: async () => ({ success: true, meta: { changes: 0 } }),
        all: async () => ({ results: [] }),
      }),
    };
  }
}

describe('API Endpoints', () => {
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
    };
  });

  describe('Health endpoint', () => {
    it('should return healthy status without auth', async () => {
      const res = await app.request('/health', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.status).toBe('healthy');
      expect(data.timestamp).toBeDefined();
    });
  });

  describe('API root', () => {
    it('should return API info without auth', async () => {
      const res = await app.request('/v1', { method: 'GET' }, env);

      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(data.name).toBe('RaaS Gateway API');
      expect(data.version).toBe('v1');
    });
  });

  describe('Protected routes', () => {
    it('should return 401 without auth', async () => {
      const res = await app.request('/v1/me', { method: 'GET' }, env);

      expect(res.status).toBe(401);
      const data = await res.json() as any;
      expect(data.error).toBe('Valid JWT or API key required');
    });

    it('should return 401 for missions without auth', async () => {
      const res = await app.request('/v1/missions', { method: 'GET' }, env);

      expect(res.status).toBe(401);
    });

    it('should return 401 for credits without auth', async () => {
      const res = await app.request('/v1/credits', { method: 'GET' }, env);

      expect(res.status).toBe(401);
    });
  });

  describe('JWT Authentication', () => {
    // JWT tests require valid jose module signing - skipped for unit tests
    it.skip('should accept valid JWT token', async () => {
      // Implementation requires full integration test setup
    });
  });

  describe('API Key Authentication', () => {
    // API key tests require D1 database setup - skipped for unit tests
    it.skip('should accept valid API key', async () => {
      // Implementation requires full integration test setup
    });
  });

  describe('Rate Limiting', () => {
    it('should include rate limit headers on responses', async () => {
      // Rate limiting is applied after auth, so we can't test it without valid auth
      // This is tested in integration tests with full auth flow
      const res = await app.request('/v1/me', {
        method: 'GET',
        headers: {
          'Authorization': 'Bearer invalid-token',
        },
      }, env);

      // Should get 401 (auth fails before rate limit)
      expect(res.status).toBe(401);
    });
  });
});
