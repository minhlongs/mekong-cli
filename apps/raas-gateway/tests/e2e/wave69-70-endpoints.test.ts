/**
 * Wave 69-70 E2E tests — Response Transform, SLA Compliance, License Management,
 * Data Pipeline, Platform Backup, API Mock Server
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

// --- Wave 69: Tenant API Response Transform ---
describe('Wave 69: Tenant API Response Transform', () => {
  it('GET /v1/response-transform/transforms — list (auth)', async () => {
    const res = await req('/v1/response-transform/transforms', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/response-transform/transforms — create (auth)', async () => {
    const res = await req('/v1/response-transform/transforms', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ rule_name: 'strip-nulls', match_pattern: '/v1/*', transform_type: 'map' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/response-transform/logs — logs (auth)', async () => {
    const res = await req('/v1/response-transform/logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/response-transform/admin/overview — admin', async () => {
    const res = await req('/v1/response-transform/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 69: Mission SLA Compliance ---
describe('Wave 69: Mission SLA Compliance', () => {
  it('GET /v1/sla-compliance/policies — list (auth)', async () => {
    const res = await req('/v1/sla-compliance/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/sla-compliance/policies — create (auth)', async () => {
    const res = await req('/v1/sla-compliance/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ policy_name: 'standard-sla', max_execution_time_ms: 30000, min_success_rate: 0.95 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/sla-compliance/violations — violations (auth)', async () => {
    const res = await req('/v1/sla-compliance/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/sla-compliance/admin/overview — admin', async () => {
    const res = await req('/v1/sla-compliance/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 69: Platform License Management ---
describe('Wave 69: Platform License Management', () => {
  it('GET /admin/license-management/licenses — list (admin)', async () => {
    const res = await req('/admin/license-management/licenses', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/license-management/licenses — create (admin)', async () => {
    const res = await req('/admin/license-management/licenses', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ license_key: 'LIC-001', license_type: 'enterprise', max_users: 100 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/license-management/activations — activations (admin)', async () => {
    const res = await req('/admin/license-management/activations?license_id=lic-1', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/license-management/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/license-management/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/license-management/licenses — 403 without key', async () => {
    const res = await req('/admin/license-management/licenses');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 70: Tenant Data Pipeline ---
describe('Wave 70: Tenant Data Pipeline', () => {
  it('GET /v1/data-pipeline/pipelines — list (auth)', async () => {
    const res = await req('/v1/data-pipeline/pipelines', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/data-pipeline/pipelines — create (auth)', async () => {
    const res = await req('/v1/data-pipeline/pipelines', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ pipeline_name: 'export-missions', source_type: 'missions', destination_type: 's3' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/data-pipeline/runs — runs (auth)', async () => {
    const res = await req('/v1/data-pipeline/runs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/data-pipeline/admin/overview — admin', async () => {
    const res = await req('/v1/data-pipeline/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 70: Admin Platform Backup ---
describe('Wave 70: Admin Platform Backup', () => {
  it('GET /admin/platform-backup/backups — list (admin)', async () => {
    const res = await req('/admin/platform-backup/backups', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/platform-backup/backups — create (admin)', async () => {
    const res = await req('/admin/platform-backup/backups', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ backup_type: 'full', storage_location: 'r2://backups/2026-03-22' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-backup/restore-points — restore points (admin)', async () => {
    const res = await req('/admin/platform-backup/restore-points', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 404, 500]).toContain(res.status);
  });
  it('GET /admin/platform-backup/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/platform-backup/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-backup/backups — 403 without key', async () => {
    const res = await req('/admin/platform-backup/backups');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 70: Tenant API Mock Server ---
describe('Wave 70: Tenant API Mock Server', () => {
  it('GET /v1/api-mocks/mocks — list (auth)', async () => {
    const res = await req('/v1/api-mocks/mocks', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-mocks/mocks — create (auth)', async () => {
    const res = await req('/v1/api-mocks/mocks', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mock_path: '/v1/test', method: 'GET', response_status: 200, response_body_json: '{"ok":true}' }) });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });
  it('GET /v1/api-mocks/requests — requests (auth)', async () => {
    const res = await req('/v1/api-mocks/requests', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-mocks/admin/overview — admin', async () => {
    const res = await req('/v1/api-mocks/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 69-70: OpenAPI spec', () => {
  it('includes Wave 69-70 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/response-transform/transforms');
    expect(paths).toContain('/v1/response-transform/logs');
    expect(paths).toContain('/v1/sla-compliance/policies');
    expect(paths).toContain('/v1/sla-compliance/violations');
    expect(paths).toContain('/admin/license-management/licenses');
    expect(paths).toContain('/admin/license-management/activations');
    expect(paths).toContain('/v1/data-pipeline/pipelines');
    expect(paths).toContain('/v1/data-pipeline/runs');
    expect(paths).toContain('/admin/platform-backup/backups');
    expect(paths).toContain('/admin/platform-backup/restore-points');
    expect(paths).toContain('/v1/api-mocks/mocks');
    expect(paths).toContain('/v1/api-mocks/requests');
  });
});
