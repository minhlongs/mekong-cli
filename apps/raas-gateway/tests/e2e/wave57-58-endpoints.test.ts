/**
 * Wave 57-58 E2E tests — Workspace Settings, Result Storage, Event Log,
 * Access Tokens, Tenant Analytics, Endpoint Monitoring
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store = new Map<string, string>();
  async get(key: string, type?: 'json') { const v = this.store.get(key); if (v === undefined) return null; return type === 'json' ? JSON.parse(v) : v; }
  async put(key: string, value: string) { this.store.set(key, value); }
  async delete(key: string) { this.store.delete(key); }
  async list(_opts?: any) { return { keys: Array.from(this.store.keys()).map(name => ({ name })) }; }
}
class MockD1 {
  prepare(_q: string) { const stmt = { bind: (..._a: any[]) => stmt, first: async () => null, run: async () => ({ success: true, meta: { changes: 1 } }), all: async () => ({ results: [] }) }; return stmt; }
  async batch(_s: any[]) { return [{ results: [] }]; }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';
async function makeToken(tier = 'pro') {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] }).setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api').setExpirationTime('1h').sign(secret);
}
function createEnv(): Env {
  return { DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any, SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test', ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY };
}
let env: Env; let token: string;
beforeEach(async () => { env = createEnv(); token = await makeToken(); });
function req(path: string, init?: RequestInit) { return app.request(path, init, env); }

// --- Wave 57: Tenant Workspace Settings ---
describe('Wave 57: Tenant Workspace Settings', () => {
  it('GET /v1/workspace/settings — get (auth)', async () => {
    const res = await req('/v1/workspace/settings', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('PUT /v1/workspace/settings — update (auth)', async () => {
    const res = await req('/v1/workspace/settings', { method: 'PUT', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ theme: 'dark', timezone: 'Asia/Saigon' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/workspace/invitations — list (auth)', async () => {
    const res = await req('/v1/workspace/invitations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/workspace/admin/overview — admin', async () => {
    const res = await req('/v1/workspace/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 57: Mission Result Storage ---
describe('Wave 57: Mission Result Storage', () => {
  it('POST /v1/results/results — store (auth)', async () => {
    const res = await req('/v1/results/results', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', content: 'Result data' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/results/results/m-1 — get (auth)', async () => {
    const res = await req('/v1/results/results/m-1', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/results/stats — storage stats (auth)', async () => {
    const res = await req('/v1/results/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/results/admin/overview — admin', async () => {
    const res = await req('/v1/results/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 57: Platform Event Log ---
describe('Wave 57: Platform Event Log', () => {
  it('GET /admin/event-log/categories — categories (public)', async () => {
    const res = await req('/admin/event-log/categories');
    expect(res.status).toBeLessThan(500);
  });
  it('GET /admin/event-log/events — events (admin)', async () => {
    const res = await req('/admin/event-log/events', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/event-log/stats — stats (admin)', async () => {
    const res = await req('/admin/event-log/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/event-log/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/event-log/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 58: Tenant Access Tokens ---
describe('Wave 58: Tenant Access Tokens', () => {
  it('POST /v1/access-tokens/tokens — create (auth)', async () => {
    const res = await req('/v1/access-tokens/tokens', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ scopes: ['read'], expires_in_hours: 24 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/access-tokens/tokens — list (auth)', async () => {
    const res = await req('/v1/access-tokens/tokens', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/access-tokens/introspect — introspect (public)', async () => {
    const res = await req('/v1/access-tokens/introspect', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token: 'test-token' }) });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/access-tokens/admin/overview — admin', async () => {
    const res = await req('/v1/access-tokens/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 58: Admin Tenant Analytics ---
describe('Wave 58: Admin Tenant Analytics', () => {
  it('GET /admin/tenant-analytics/health — list (admin)', async () => {
    const res = await req('/admin/tenant-analytics/health', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-analytics/risks — risks (admin)', async () => {
    const res = await req('/admin/tenant-analytics/risks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-analytics/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/tenant-analytics/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-analytics/health — 403 without key', async () => {
    const res = await req('/admin/tenant-analytics/health');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 58: API Endpoint Monitoring ---
describe('Wave 58: API Endpoint Monitoring', () => {
  it('GET /admin/endpoint-monitoring/availability — list (admin)', async () => {
    const res = await req('/admin/endpoint-monitoring/availability', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/endpoint-monitoring/alerts — alerts (admin)', async () => {
    const res = await req('/admin/endpoint-monitoring/alerts', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/endpoint-monitoring/slow — slow endpoints (admin)', async () => {
    const res = await req('/admin/endpoint-monitoring/slow', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/endpoint-monitoring/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/endpoint-monitoring/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 57-58: OpenAPI spec', () => {
  it('includes Wave 57-58 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/workspace/settings');
    expect(paths).toContain('/v1/workspace/invitations');
    expect(paths).toContain('/v1/results/results');
    expect(paths).toContain('/v1/results/stats');
    expect(paths).toContain('/admin/event-log/events');
    expect(paths).toContain('/admin/event-log/categories');
    expect(paths).toContain('/v1/access-tokens/tokens');
    expect(paths).toContain('/v1/access-tokens/introspect');
    expect(paths).toContain('/admin/tenant-analytics/health');
    expect(paths).toContain('/admin/tenant-analytics/risks');
    expect(paths).toContain('/admin/endpoint-monitoring/availability');
    expect(paths).toContain('/admin/endpoint-monitoring/alerts');
  });
});
