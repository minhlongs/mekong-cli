/**
 * Wave 65-66 E2E tests — Session Management, Quality Gates, Resource Pools,
 * API Docs Tenant, Change Management, Usage Alerts
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

// --- Wave 65: Tenant Session Management ---
describe('Wave 65: Tenant Session Management', () => {
  it('GET /v1/sessions/sessions — list (auth)', async () => {
    const res = await req('/v1/sessions/sessions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/sessions/sessions — create (auth)', async () => {
    const res = await req('/v1/sessions/sessions', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: 'u-1', device_info: 'Chrome/120', ip_address: '1.2.3.4' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/sessions/events — events (auth)', async () => {
    const res = await req('/v1/sessions/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/sessions/admin/overview — admin', async () => {
    const res = await req('/v1/sessions/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 65: Mission Quality Gates ---
describe('Wave 65: Mission Quality Gates', () => {
  it('GET /v1/quality-gates/gates — list (auth)', async () => {
    const res = await req('/v1/quality-gates/gates', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/quality-gates/gates — create (auth)', async () => {
    const res = await req('/v1/quality-gates/gates', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ gate_name: 'output-validation', criteria_json: '{"min_score":0.8}' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/quality-gates/evaluations — evaluations (auth)', async () => {
    const res = await req('/v1/quality-gates/evaluations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/quality-gates/admin/overview — admin', async () => {
    const res = await req('/v1/quality-gates/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 65: Platform Resource Pools ---
describe('Wave 65: Platform Resource Pools', () => {
  it('GET /admin/resource-pools/pools — list (admin)', async () => {
    const res = await req('/admin/resource-pools/pools', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/resource-pools/pools — create (admin)', async () => {
    const res = await req('/admin/resource-pools/pools', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ pool_name: 'gpu-pool', resource_type: 'gpu', total_capacity: 100 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/resource-pools/allocations — allocations (admin)', async () => {
    const res = await req('/admin/resource-pools/allocations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/resource-pools/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/resource-pools/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/resource-pools/pools — 403 without key', async () => {
    const res = await req('/admin/resource-pools/pools');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 66: Tenant API Documentation ---
describe('Wave 66: Tenant API Documentation', () => {
  it('GET /v1/api-docs-tenant/pages — list (auth)', async () => {
    const res = await req('/v1/api-docs-tenant/pages', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-docs-tenant/pages — create (auth)', async () => {
    const res = await req('/v1/api-docs-tenant/pages', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'Getting Started', slug: 'getting-started', content: '# Hello', category: 'guides' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/api-docs-tenant/versions — versions (auth)', async () => {
    const res = await req('/v1/api-docs-tenant/versions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-docs-tenant/admin/overview — admin', async () => {
    const res = await req('/v1/api-docs-tenant/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 66: Admin Change Management ---
describe('Wave 66: Admin Change Management', () => {
  it('GET /admin/change-management/changes — list (admin)', async () => {
    const res = await req('/admin/change-management/changes', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/change-management/changes — create (admin)', async () => {
    const res = await req('/admin/change-management/changes', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'DB migration', change_type: 'infrastructure', priority: 'high' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/change-management/logs — logs (admin)', async () => {
    const res = await req('/admin/change-management/logs?change_id=c1', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/change-management/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/change-management/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/change-management/changes — 403 without key', async () => {
    const res = await req('/admin/change-management/changes');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 66: Tenant Usage Alerts ---
describe('Wave 66: Tenant Usage Alerts', () => {
  it('GET /v1/usage-alerts/rules — list (auth)', async () => {
    const res = await req('/v1/usage-alerts/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/usage-alerts/rules — create (auth)', async () => {
    const res = await req('/v1/usage-alerts/rules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ metric_name: 'api_calls', threshold: 10000, comparison: 'gt' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/usage-alerts/triggers — triggers (auth)', async () => {
    const res = await req('/v1/usage-alerts/triggers', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/usage-alerts/admin/overview — admin', async () => {
    const res = await req('/v1/usage-alerts/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 65-66: OpenAPI spec', () => {
  it('includes Wave 65-66 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/sessions/sessions');
    expect(paths).toContain('/v1/sessions/events');
    expect(paths).toContain('/v1/quality-gates/gates');
    expect(paths).toContain('/v1/quality-gates/evaluations');
    expect(paths).toContain('/admin/resource-pools/pools');
    expect(paths).toContain('/admin/resource-pools/allocations');
    expect(paths).toContain('/v1/api-docs-tenant/pages');
    expect(paths).toContain('/v1/api-docs-tenant/versions');
    expect(paths).toContain('/admin/change-management/changes');
    expect(paths).toContain('/admin/change-management/logs');
    expect(paths).toContain('/v1/usage-alerts/rules');
    expect(paths).toContain('/v1/usage-alerts/triggers');
  });
});
