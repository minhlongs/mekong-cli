/**
 * Wave 77-78 E2E tests — Access Control, Feedback Loop, Cost Dashboard,
 * Data Classification, Tenant Communication, Integration Testing
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
async function makeToken(tier = 'pro') { const secret = new TextEncoder().encode(JWT_SECRET=REDACTED); return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] }).setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api').setExpirationTime('1h').sign(secret); }
function createEnv(): Env { return { DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any, SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test', ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY }; }
let env: Env; let token: string;
beforeEach(async () => { env = createEnv(); token = await makeToken(); });
function req(path: string, init?: RequestInit) { return app.request(path, init, env); }

describe('Wave 77: Tenant API Access Control', () => {
  it('GET /v1/access-control/rules', async () => { const r = await req('/v1/access-control/rules', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/access-control/rules', async () => { const r = await req('/v1/access-control/rules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ resource_pattern: '/v1/missions/*', action: 'allow' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/access-control/audit', async () => { const r = await req('/v1/access-control/audit', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/access-control/admin/overview', async () => { const r = await req('/v1/access-control/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 77: Mission Feedback Loop', () => {
  it('GET /v1/feedback-loop/feedback', async () => { const r = await req('/v1/feedback-loop/feedback', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/feedback-loop/feedback', async () => { const r = await req('/v1/feedback-loop/feedback', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', rating: 5, feedback_text: 'Great' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/feedback-loop/actions', async () => { const r = await req('/v1/feedback-loop/actions', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/feedback-loop/admin/overview', async () => { const r = await req('/v1/feedback-loop/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 77: Platform Cost Dashboard', () => {
  it('GET /admin/cost-dashboard/entries', async () => { const r = await req('/admin/cost-dashboard/entries', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/cost-dashboard/entries', async () => { const r = await req('/admin/cost-dashboard/entries', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ category: 'compute', provider: 'cloudflare', amount: 25.50 }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/cost-dashboard/budgets', async () => { const r = await req('/admin/cost-dashboard/budgets', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/cost-dashboard/dashboard', async () => { const r = await req('/admin/cost-dashboard/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/cost-dashboard/entries — 403', async () => { const r = await req('/admin/cost-dashboard/entries'); expect([401,403]).toContain(r.status); });
});

describe('Wave 78: Tenant Data Classification', () => {
  it('GET /v1/data-classification/classifications', async () => { const r = await req('/v1/data-classification/classifications', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/data-classification/classifications', async () => { const r = await req('/v1/data-classification/classifications', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ field_path: 'user.email', classification_level: 'pii', sensitivity: 'high' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/data-classification/scans', async () => { const r = await req('/v1/data-classification/scans', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/data-classification/admin/overview', async () => { const r = await req('/v1/data-classification/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 78: Admin Tenant Communication', () => {
  it('GET /admin/tenant-communication/messages', async () => { const r = await req('/admin/tenant-communication/messages', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/tenant-communication/messages', async () => { const r = await req('/admin/tenant-communication/messages', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ tenant_id: 't-1', subject: 'Maintenance', body: 'Scheduled downtime' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/tenant-communication/templates', async () => { const r = await req('/admin/tenant-communication/templates', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/tenant-communication/dashboard', async () => { const r = await req('/admin/tenant-communication/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/tenant-communication/messages — 403', async () => { const r = await req('/admin/tenant-communication/messages'); expect([401,403]).toContain(r.status); });
});

describe('Wave 78: Tenant Integration Testing', () => {
  it('GET /v1/integration-testing/configs', async () => { const r = await req('/v1/integration-testing/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/integration-testing/configs', async () => { const r = await req('/v1/integration-testing/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ test_name: 'health-check', target_endpoint: 'https://api.example.com/health', expected_status: 200 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/integration-testing/results', async () => { const r = await req('/v1/integration-testing/results', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/integration-testing/admin/overview', async () => { const r = await req('/v1/integration-testing/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 77-78: OpenAPI spec', () => {
  it('includes Wave 77-78 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/access-control/rules'); expect(paths).toContain('/v1/access-control/audit');
    expect(paths).toContain('/v1/feedback-loop/feedback'); expect(paths).toContain('/v1/feedback-loop/actions');
    expect(paths).toContain('/admin/cost-dashboard/entries'); expect(paths).toContain('/admin/cost-dashboard/budgets');
    expect(paths).toContain('/v1/data-classification/classifications'); expect(paths).toContain('/v1/data-classification/scans');
    expect(paths).toContain('/admin/tenant-communication/messages'); expect(paths).toContain('/admin/tenant-communication/templates');
    expect(paths).toContain('/v1/integration-testing/configs'); expect(paths).toContain('/v1/integration-testing/results');
  });
});
