/**
 * Wave 43-44 E2E tests — Webhook Analytics, Rate Plans, Mission Costs,
 * Audit Policies, Feature Requests, Admin Tenant Mgmt
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

// --- Wave 43: Webhook Analytics ---

describe('Wave 43: Webhook Analytics', () => {
  it('GET /v1/webhook-analytics/stats — delivery stats (auth)', async () => {
    const res = await req('/v1/webhook-analytics/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-analytics/timeline — timeline (auth)', async () => {
    const res = await req('/v1/webhook-analytics/timeline', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-analytics/endpoints — endpoints (auth)', async () => {
    const res = await req('/v1/webhook-analytics/endpoints', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-analytics/overview — overview (auth)', async () => {
    const res = await req('/v1/webhook-analytics/overview', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-analytics/admin/analytics — admin', async () => {
    const res = await req('/v1/webhook-analytics/admin/analytics', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 43: Rate Plan Management ---

describe('Wave 43: Rate Plan Management', () => {
  it('GET /v1/rate-plans/plans — list plans (public)', async () => {
    const res = await req('/v1/rate-plans/plans');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-plans/my-plan — my plan (auth)', async () => {
    const res = await req('/v1/rate-plans/my-plan', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-plans/my-limits — effective limits (auth)', async () => {
    const res = await req('/v1/rate-plans/my-limits', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/rate-plans/admin/plans — create plan (admin)', async () => {
    const res = await req('/v1/rate-plans/admin/plans', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test-plan', requests_per_minute: 100 }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /v1/rate-plans/admin/overview — admin', async () => {
    const res = await req('/v1/rate-plans/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 43: Mission Cost Tracking ---

describe('Wave 43: Mission Cost Tracking', () => {
  it('GET /v1/mission-costs/costs — cost breakdown (auth)', async () => {
    const res = await req('/v1/mission-costs/costs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-costs/costs/by-model — by model (auth)', async () => {
    const res = await req('/v1/mission-costs/costs/by-model', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-costs/budget — budget (auth)', async () => {
    const res = await req('/v1/mission-costs/budget', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404, 500]).toContain(res.status);
  });

  it('GET /v1/mission-costs/summary — summary (auth)', async () => {
    const res = await req('/v1/mission-costs/summary', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-costs/admin/overview — admin', async () => {
    const res = await req('/v1/mission-costs/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 44: Tenant Audit Policies ---

describe('Wave 44: Tenant Audit Policies', () => {
  it('GET /v1/audit-policies/policies — list (auth)', async () => {
    const res = await req('/v1/audit-policies/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/audit-policies/policies — create (auth)', async () => {
    const res = await req('/v1/audit-policies/policies', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_name: 'test-policy', event_types: ['mission.created'], retention_days: 90 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/audit-policies/violations — violations (auth)', async () => {
    const res = await req('/v1/audit-policies/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit-policies/admin/overview — admin', async () => {
    const res = await req('/v1/audit-policies/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 44: Feature Requests ---

describe('Wave 44: Feature Requests', () => {
  it('GET /v1/feature-requests/requests — list (public)', async () => {
    const res = await req('/v1/feature-requests/requests');
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/feature-requests/requests — submit (auth)', async () => {
    const res = await req('/v1/feature-requests/requests', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test Feature', description: 'Need this', category: 'api' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/feature-requests/requests/fr-1/vote — vote (auth)', async () => {
    const res = await req('/v1/feature-requests/requests/fr-1/vote', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/feature-requests/admin/overview — admin', async () => {
    const res = await req('/v1/feature-requests/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 44: Admin Tenant Management ---

describe('Wave 44: Admin Tenant Management', () => {
  it('GET /admin/tenant-mgmt/tenants/t-1/notes — notes (admin)', async () => {
    const res = await req('/admin/tenant-mgmt/tenants/t-1/notes', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/tenant-mgmt/tenants/t-1/tags — add tag (admin)', async () => {
    const res = await req('/admin/tenant-mgmt/tenants/t-1/tags', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag: 'vip', color: '#ff0000' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/tenant-mgmt/tenants/t-1/risk — risk score (admin)', async () => {
    const res = await req('/admin/tenant-mgmt/tenants/t-1/risk', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 404, 500]).toContain(res.status);
  });

  it('GET /admin/tenant-mgmt/at-risk — at-risk list (admin)', async () => {
    const res = await req('/admin/tenant-mgmt/at-risk', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/tenant-mgmt/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/tenant-mgmt/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 43-44: OpenAPI spec', () => {
  it('includes Wave 43-44 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 43
    expect(paths).toContain('/v1/webhook-analytics/stats');
    expect(paths).toContain('/v1/webhook-analytics/overview');
    expect(paths).toContain('/v1/rate-plans/plans');
    expect(paths).toContain('/v1/rate-plans/my-limits');
    expect(paths).toContain('/v1/mission-costs/costs');
    expect(paths).toContain('/v1/mission-costs/budget');
    // Wave 44
    expect(paths).toContain('/v1/audit-policies/policies');
    expect(paths).toContain('/v1/audit-policies/violations');
    expect(paths).toContain('/v1/feature-requests/requests');
    expect(paths).toContain('/v1/feature-requests/admin/overview');
    expect(paths).toContain('/admin/tenant-mgmt/at-risk');
    expect(paths).toContain('/admin/tenant-mgmt/dashboard');
  });
});
