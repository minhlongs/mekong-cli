/**
 * E2E tests — Tenant management endpoints
 * Public: POST /v1/tenants/signup, POST /v1/tenants/login
 * Protected: profile, settings, api-keys (require auth)
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

// Minimal ExecutionContext mock — signup uses c.executionCtx.waitUntil()
const mockCtx = {
  waitUntil: (_promise: Promise<any>) => { /* fire-and-forget in tests */ },
  passThroughOnException: () => {},
  props: {},
} as unknown as ExecutionContext;

describe('Tenant Management E2E', () => {
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
  // Public signup / login
  // ---------------------------------------------------------------------------

  describe('POST /v1/tenants/signup (public)', () => {
    it('returns 400 when name is missing', async () => {
      const res = await app.request('/v1/tenants/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' }),
      }, env);

      expect(res.status).toBe(400);
      const data = await res.json() as any;
      expect(data.error).toBeDefined();
    });

    it('returns 400 when email is missing', async () => {
      const res = await app.request('/v1/tenants/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test User' }),
      }, env);

      expect(res.status).toBe(400);
      const data = await res.json() as any;
      expect(data.error).toBeDefined();
    });

    it('returns 400 for invalid email format', async () => {
      const res = await app.request('/v1/tenants/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test User', email: 'not-an-email' }),
      }, env);

      expect(res.status).toBe(400);
      const data = await res.json() as any;
      expect(data.code).toBe('INVALID_EMAIL');
    });

    it('creates tenant and returns JWT when valid', async () => {
      // Pass mockCtx as 4th arg — signup calls c.executionCtx.waitUntil()
      const res = await app.request('/v1/tenants/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test User', email: 'newuser@example.com' }),
      }, env, mockCtx);

      expect(res.status).toBe(201);
      const data = await res.json() as any;
      expect(data.tenantId).toBeDefined();
      expect(data.token).toBeDefined();
      expect(data.tier).toBe('free');
      expect(data.credits).toBeGreaterThan(0);
    });
  });

  describe('POST /v1/tenants/login (public)', () => {
    it('returns 400 when email is missing', async () => {
      const res = await app.request('/v1/tenants/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }, env);

      expect(res.status).toBe(400);
    });

    it('returns 404 for unknown email', async () => {
      const res = await app.request('/v1/tenants/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'nobody@example.com' }),
      }, env);

      // DB mock returns null → not found
      expect(res.status).toBe(404);
      const data = await res.json() as any;
      expect(data.code).toBe('NOT_FOUND');
    });
  });

  // ---------------------------------------------------------------------------
  // Protected tenant endpoints — auth guard enforcement
  // ---------------------------------------------------------------------------

  describe('GET /v1/tenants/profile (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/profile', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 401 with invalid token', async () => {
      const res = await app.request('/v1/tenants/profile', {
        method: 'GET',
        headers: { 'Authorization': 'Bearer bad-token' },
      }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('PUT /v1/tenants/settings (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notify_email: true }),
      }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('POST /v1/tenants/api-keys (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'My Key' }),
      }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('GET /v1/tenants/api-keys (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/api-keys', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });
  });

  describe('GET /v1/tenants/usage (auth required)', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/tenants/usage', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });
  });
});
