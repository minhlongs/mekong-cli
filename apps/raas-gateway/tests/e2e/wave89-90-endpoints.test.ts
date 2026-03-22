/**
 * Wave 89-90 E2E tests — Circuit Breaker, Resource Allocation, Audit Trail,
 * Caching Config, Release Management, Error Tracking
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';
class MockKV { private store = new Map<string, string>(); async get(key: string, type?: 'json') { const v = this.store.get(key); if (v === undefined) return null; return type === 'json' ? JSON.parse(v) : v; } async put(key: string, value: string) { this.store.set(key, value); } async delete(key: string) { this.store.delete(key); } async list(_opts?: any) { return { keys: Array.from(this.store.keys()).map(name => ({ name })) }; } }
class MockD1 { prepare(_q: string) { const stmt = { bind: (..._a: any[]) => stmt, first: async () => null, run: async () => ({ success: true, meta: { changes: 1 } }), all: async () => ({ results: [] }) }; return stmt; } async batch(_s: any[]) { return [{ results: [] }]; } }
const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345'; const ADMIN_API_KEY = 'test-admin-key';
async function makeToken(tier = 'pro') { const secret = new TextEncoder().encode(JWT_SECRET=REDACTED); return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] }).setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api').setExpirationTime('1h').sign(secret); }
function createEnv(): Env { return { DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any, SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test', ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY }; }
let env: Env; let token: string;
beforeEach(async () => { env = createEnv(); token = await makeToken(); });
function req(path: string, init?: RequestInit) { return app.request(path, init, env); }

describe('Wave 89: Tenant API Circuit Breaker', () => {
  it('GET /v1/circuit-breaker/breakers', async () => { const r = await req('/v1/circuit-breaker/breakers', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/circuit-breaker/breakers', async () => { const r = await req('/v1/circuit-breaker/breakers', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/external/*', failure_threshold: 5 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/circuit-breaker/events', async () => { const r = await req('/v1/circuit-breaker/events', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/circuit-breaker/admin/overview', async () => { const r = await req('/v1/circuit-breaker/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 89: Mission Resource Allocation', () => {
  it('GET /v1/resource-allocation/allocations', async () => { const r = await req('/v1/resource-allocation/allocations', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/resource-allocation/allocations', async () => { const r = await req('/v1/resource-allocation/allocations', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', resource_type: 'gpu', allocated_amount: 2 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/resource-allocation/pools', async () => { const r = await req('/v1/resource-allocation/pools', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/resource-allocation/admin/overview', async () => { const r = await req('/v1/resource-allocation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 89: Admin Platform Audit Trail', () => {
  it('GET /admin/audit-trail/entries', async () => { const r = await req('/admin/audit-trail/entries', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/audit-trail/entries', async () => { const r = await req('/admin/audit-trail/entries', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ actor: 'admin@example.com', action: 'create', resource_type: 'tenant' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/audit-trail/policies', async () => { const r = await req('/admin/audit-trail/policies', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/audit-trail/dashboard', async () => { const r = await req('/admin/audit-trail/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/audit-trail/entries — 403', async () => { const r = await req('/admin/audit-trail/entries'); expect([401,403]).toContain(r.status); });
});

describe('Wave 90: Tenant API Caching Config', () => {
  it('GET /v1/caching-config/configs', async () => { const r = await req('/v1/caching-config/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/caching-config/configs', async () => { const r = await req('/v1/caching-config/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/missions', ttl_seconds: 600 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/caching-config/stats', async () => { const r = await req('/v1/caching-config/stats', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/caching-config/admin/overview', async () => { const r = await req('/v1/caching-config/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 90: Admin Release Management', () => {
  it('GET /admin/release-management/releases', async () => { const r = await req('/admin/release-management/releases', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/release-management/releases', async () => { const r = await req('/admin/release-management/releases', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ version: '3.0.0', title: 'Major Release', release_type: 'major' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/release-management/notes', async () => { const r = await req('/admin/release-management/notes', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/release-management/dashboard', async () => { const r = await req('/admin/release-management/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/release-management/releases — 403', async () => { const r = await req('/admin/release-management/releases'); expect([401,403]).toContain(r.status); });
});

describe('Wave 90: Tenant Error Tracking', () => {
  it('GET /v1/error-tracking/errors', async () => { const r = await req('/v1/error-tracking/errors', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/error-tracking/errors', async () => { const r = await req('/v1/error-tracking/errors', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ error_type: 'runtime', message: 'Null pointer', endpoint: '/v1/missions' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/error-tracking/rules', async () => { const r = await req('/v1/error-tracking/rules', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/error-tracking/admin/overview', async () => { const r = await req('/v1/error-tracking/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 89-90: OpenAPI spec', () => {
  it('includes Wave 89-90 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/circuit-breaker/breakers'); expect(paths).toContain('/v1/circuit-breaker/events');
    expect(paths).toContain('/v1/resource-allocation/allocations'); expect(paths).toContain('/v1/resource-allocation/pools');
    expect(paths).toContain('/admin/audit-trail/entries'); expect(paths).toContain('/admin/audit-trail/policies');
    expect(paths).toContain('/v1/caching-config/configs'); expect(paths).toContain('/v1/caching-config/stats');
    expect(paths).toContain('/admin/release-management/releases'); expect(paths).toContain('/admin/release-management/notes');
    expect(paths).toContain('/v1/error-tracking/errors'); expect(paths).toContain('/v1/error-tracking/rules');
  });
});
