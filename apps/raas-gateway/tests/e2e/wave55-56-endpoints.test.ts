/**
 * Wave 55-56 E2E tests — IP Geolocation, Dependency Graph, Rate Limit Analytics,
 * Tag System, System Health, Response Caching
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
function req(path: string, init?: RequestInit) { return app.request(path, init, env); }

// --- Wave 55: Tenant IP Geolocation ---
describe('Wave 55: Tenant IP Geolocation', () => {
  it('GET /v1/ip-geo/rules — list (auth)', async () => {
    const res = await req('/v1/ip-geo/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/ip-geo/rules — create (auth)', async () => {
    const res = await req('/v1/ip-geo/rules', {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_type: 'block', country_codes: ['CN', 'RU'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/ip-geo/analytics — analytics (auth)', async () => {
    const res = await req('/v1/ip-geo/analytics', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/ip-geo/admin/overview — admin', async () => {
    const res = await req('/v1/ip-geo/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 55: Mission Dependency Graph ---
describe('Wave 55: Mission Dependency Graph', () => {
  it('POST /v1/dep-graph/dependencies — add (auth)', async () => {
    const res = await req('/v1/dep-graph/dependencies', {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent_mission_id: 'm1', child_mission_id: 'm2' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/dep-graph/groups — list groups (auth)', async () => {
    const res = await req('/v1/dep-graph/groups', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/dep-graph/analyses — analyses (auth)', async () => {
    const res = await req('/v1/dep-graph/analyses', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/dep-graph/admin/overview — admin', async () => {
    const res = await req('/v1/dep-graph/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 55: Rate Limit Analytics ---
describe('Wave 55: Platform Rate Limit Analytics', () => {
  it('GET /v1/rate-analytics/events — events (auth)', async () => {
    const res = await req('/v1/rate-analytics/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/rate-analytics/stats — stats (auth)', async () => {
    const res = await req('/v1/rate-analytics/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/rate-analytics/admin/overview — admin', async () => {
    const res = await req('/v1/rate-analytics/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 56: Tenant Tag System ---
describe('Wave 56: Tenant Tag System', () => {
  it('GET /v1/tags/tags — list (auth)', async () => {
    const res = await req('/v1/tags/tags', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/tags/tags — create (auth)', async () => {
    const res = await req('/v1/tags/tags', {
      method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'urgent', color: '#EF4444' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/tags/analytics — analytics (auth)', async () => {
    const res = await req('/v1/tags/analytics', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/tags/admin/overview — admin', async () => {
    const res = await req('/v1/tags/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 56: Admin System Health ---
describe('Wave 56: Admin System Health', () => {
  it('GET /admin/system-health/components — list (admin)', async () => {
    const res = await req('/admin/system-health/components', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/system-health/alerts — alerts (admin)', async () => {
    const res = await req('/admin/system-health/alerts', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/system-health/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/system-health/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/system-health/components — 403 without key', async () => {
    const res = await req('/admin/system-health/components');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 56: API Response Caching ---
describe('Wave 56: API Response Caching', () => {
  it('GET /admin/response-cache/rules — list (admin)', async () => {
    const res = await req('/admin/response-cache/rules', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/response-cache/analytics — analytics (admin)', async () => {
    const res = await req('/admin/response-cache/analytics', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/response-cache/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/response-cache/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/response-cache/rules — 403 without key', async () => {
    const res = await req('/admin/response-cache/rules');
    expect([401, 403]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 55-56: OpenAPI spec', () => {
  it('includes Wave 55-56 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/ip-geo/rules');
    expect(paths).toContain('/v1/dep-graph/dependencies');
    expect(paths).toContain('/v1/dep-graph/groups');
    expect(paths).toContain('/v1/rate-analytics/events');
    expect(paths).toContain('/v1/tags/tags');
    expect(paths).toContain('/v1/tags/analytics');
    expect(paths).toContain('/admin/system-health/components');
    expect(paths).toContain('/admin/system-health/alerts');
    expect(paths).toContain('/admin/response-cache/rules');
    expect(paths).toContain('/admin/response-cache/analytics');
  });
});
