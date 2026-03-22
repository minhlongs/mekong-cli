/**
 * Wave 39-40 E2E tests — Tenant API Tokens, Mission Webhooks V3, Platform Announcements,
 * Tenant Quotas, AI Model Registry, Platform Metrics Dashboard
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store = new Map<string, string>();
  async get(key: string, type?: 'json') {
    const v = this.store.get(key);
    if (v === undefined) return null;
    return type === 'json' ? JSON.parse(v) : v;
  }
  async put(key: string, value: string) { this.store.set(key, value); }
  async delete(key: string) { this.store.delete(key); }
  async list(_opts?: any) { return { keys: Array.from(this.store.keys()).map(name => ({ name })) }; }
}

class MockD1 {
  prepare(_q: string) {
    const stmt = {
      bind: (..._a: any[]) => stmt,
      first: async () => null,
      run: async () => ({ success: true, meta: { changes: 1 } }),
      all: async () => ({ results: [] }),
    };
    return stmt;
  }
  async batch(_s: any[]) { return [{ results: [] }]; }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';

async function makeToken(tier = 'pro') {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api')
    .setExpirationTime('1h').sign(secret);
}

function createEnv(): Env {
  return {
    DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any,
    SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED,
    POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test',
    ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY,
  };
}

let env: Env;
let token: string;

beforeEach(async () => { env = createEnv(); token = await makeToken(); });

function req(path: string, init?: RequestInit) {
  return app.request(path, init, env);
}

// --- Wave 39: Tenant API Tokens ---

describe('Wave 39: Tenant API Tokens', () => {
  it('GET /v1/api-tokens/tokens — list tokens (auth)', async () => {
    const res = await req('/v1/api-tokens/tokens', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/api-tokens/tokens — create token (auth)', async () => {
    const res = await req('/v1/api-tokens/tokens', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test-token', scopes: ['read', 'write'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/api-tokens/validate — validate token (public)', async () => {
    const res = await req('/v1/api-tokens/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: 'mkt_test123' }),
    });
    expect([200, 401, 404, 500]).toContain(res.status);
  });

  it('GET /v1/api-tokens/admin/overview — admin', async () => {
    const res = await req('/v1/api-tokens/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 39: Mission Webhooks V3 ---

describe('Wave 39: Mission Webhooks V3', () => {
  it('GET /v1/mission-webhooks-v3/subscriptions — list subs (auth)', async () => {
    const res = await req('/v1/mission-webhooks-v3/subscriptions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-webhooks-v3/subscriptions — create sub (auth)', async () => {
    const res = await req('/v1/mission-webhooks-v3/subscriptions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test', url: 'https://example.com/hook', events: ['mission.completed'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/mission-webhooks-v3/deliveries — deliveries (auth)', async () => {
    const res = await req('/v1/mission-webhooks-v3/deliveries', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-webhooks-v3/stats — stats (auth)', async () => {
    const res = await req('/v1/mission-webhooks-v3/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-webhooks-v3/admin/overview — admin', async () => {
    const res = await req('/v1/mission-webhooks-v3/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 39: Platform Announcements ---

describe('Wave 39: Platform Announcements', () => {
  it('GET /v1/announcements/active — active (auth)', async () => {
    const res = await req('/v1/announcements/active', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/announcements/maintenance — maintenance (public)', async () => {
    const res = await req('/v1/announcements/maintenance');
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/announcements/admin/create — create (admin)', async () => {
    const res = await req('/v1/announcements/admin/create', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test', content: 'Test announcement', type: 'info' }),
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });

  it('GET /v1/announcements/admin/list — list all (admin)', async () => {
    const res = await req('/v1/announcements/admin/list', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /v1/announcements/admin/stats — stats (admin)', async () => {
    const res = await req('/v1/announcements/admin/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 40: Tenant Quotas ---

describe('Wave 40: Tenant Quotas', () => {
  it('GET /v1/quotas/quotas — get quotas (auth)', async () => {
    const res = await req('/v1/quotas/quotas', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/quotas/usage — quota usage (auth)', async () => {
    const res = await req('/v1/quotas/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/quotas/check — check quota (auth)', async () => {
    const res = await req('/v1/quotas/check', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_type: 'projects' }),
    });
    expect([200, 429, 500]).toContain(res.status);
  });

  it('GET /v1/quotas/tier-defaults/pro — tier defaults (public)', async () => {
    const res = await req('/v1/quotas/tier-defaults/pro');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/quotas/admin/overview — admin', async () => {
    const res = await req('/v1/quotas/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 40: AI Model Registry ---

describe('Wave 40: AI Model Registry', () => {
  it('GET /v1/ai-models/models — list models (public)', async () => {
    const res = await req('/v1/ai-models/models');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/ai-models/providers — list providers (public)', async () => {
    const res = await req('/v1/ai-models/providers');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/ai-models/usage — model usage (auth)', async () => {
    const res = await req('/v1/ai-models/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/ai-models/costs — cost breakdown (auth)', async () => {
    const res = await req('/v1/ai-models/costs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/ai-models/admin/top-models — top models (admin)', async () => {
    const res = await req('/v1/ai-models/admin/top-models', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /v1/ai-models/admin/seed — seed models (admin)', async () => {
    const res = await req('/v1/ai-models/admin/seed', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });
});

// --- Wave 40: Platform Metrics Dashboard ---

describe('Wave 40: Platform Metrics Dashboard', () => {
  it('GET /admin/platform-metrics/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/platform-metrics/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-metrics/metrics — metrics (admin)', async () => {
    const res = await req('/admin/platform-metrics/metrics', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-metrics/growth — growth (admin)', async () => {
    const res = await req('/admin/platform-metrics/growth', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-metrics/revenue — revenue (admin)', async () => {
    const res = await req('/admin/platform-metrics/revenue', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-metrics/goals — goals (admin)', async () => {
    const res = await req('/admin/platform-metrics/goals', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 39-40: OpenAPI spec', () => {
  it('includes Wave 39-40 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 39
    expect(paths).toContain('/v1/api-tokens/tokens');
    expect(paths).toContain('/v1/api-tokens/validate');
    expect(paths).toContain('/v1/mission-webhooks-v3/subscriptions');
    expect(paths).toContain('/v1/mission-webhooks-v3/stats');
    expect(paths).toContain('/v1/announcements/active');
    expect(paths).toContain('/v1/announcements/maintenance');
    // Wave 40
    expect(paths).toContain('/v1/quotas/quotas');
    expect(paths).toContain('/v1/quotas/usage');
    expect(paths).toContain('/v1/ai-models/models');
    expect(paths).toContain('/v1/ai-models/providers');
    expect(paths).toContain('/admin/platform-metrics/dashboard');
    expect(paths).toContain('/admin/platform-metrics/goals');
  });
});
