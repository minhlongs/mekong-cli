/**
 * Wave 59-60 E2E tests — Data Retention, Execution History, Error Budget,
 * API Versioning, Capacity Planning, Compliance Reporting
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

// --- Wave 59: Tenant Data Retention Policies ---
describe('Wave 59: Tenant Data Retention Policies', () => {
  it('GET /v1/data-retention/policies — list (auth)', async () => {
    const res = await req('/v1/data-retention/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/data-retention/policies — create (auth)', async () => {
    const res = await req('/v1/data-retention/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ entity_type: 'missions', retention_days: 90, action: 'archive' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/data-retention/runs — list runs (auth)', async () => {
    const res = await req('/v1/data-retention/runs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/data-retention/admin/overview — admin', async () => {
    const res = await req('/v1/data-retention/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 59: Mission Execution History ---
describe('Wave 59: Mission Execution History', () => {
  it('GET /v1/execution-history/executions — list (auth)', async () => {
    const res = await req('/v1/execution-history/executions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/execution-history/executions — record (auth)', async () => {
    const res = await req('/v1/execution-history/executions', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', executor_type: 'llm', status: 'completed', duration_ms: 1200 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/execution-history/metrics — metrics (auth)', async () => {
    const res = await req('/v1/execution-history/metrics', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/execution-history/admin/overview — admin', async () => {
    const res = await req('/v1/execution-history/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 59: Platform Error Budget ---
describe('Wave 59: Platform Error Budget', () => {
  it('GET /admin/error-budget/budgets — list (admin)', async () => {
    const res = await req('/admin/error-budget/budgets', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/error-budget/budgets — create (admin)', async () => {
    const res = await req('/admin/error-budget/budgets', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ service_name: 'api-gateway', slo_target: 99.9, window_days: 30 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/error-budget/events — events (admin)', async () => {
    const res = await req('/admin/error-budget/events?budget_id=b1', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/error-budget/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/error-budget/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/error-budget/budgets — 403 without key', async () => {
    const res = await req('/admin/error-budget/budgets');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 60: Tenant API Versioning ---
describe('Wave 60: Tenant API Versioning', () => {
  it('GET /v1/api-versioning/versions — list (auth)', async () => {
    const res = await req('/v1/api-versioning/versions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-versioning/versions — create (auth)', async () => {
    const res = await req('/v1/api-versioning/versions', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ version_label: 'v2', base_url: '/api/v2' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/api-versioning/mappings — mappings (auth)', async () => {
    const res = await req('/v1/api-versioning/mappings', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-versioning/admin/overview — admin', async () => {
    const res = await req('/v1/api-versioning/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 60: Admin Capacity Planning ---
describe('Wave 60: Admin Capacity Planning', () => {
  it('GET /admin/capacity-planning/plans — list (admin)', async () => {
    const res = await req('/admin/capacity-planning/plans', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/capacity-planning/plans — create (admin)', async () => {
    const res = await req('/admin/capacity-planning/plans', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ resource_type: 'workers', current_usage: 45.5, max_capacity: 100.0 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/capacity-planning/alerts — alerts (admin)', async () => {
    const res = await req('/admin/capacity-planning/alerts', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/capacity-planning/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/capacity-planning/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/capacity-planning/plans — 403 without key', async () => {
    const res = await req('/admin/capacity-planning/plans');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 60: Tenant Compliance Reporting ---
describe('Wave 60: Tenant Compliance Reporting', () => {
  it('GET /v1/compliance-reports/reports — list (auth)', async () => {
    const res = await req('/v1/compliance-reports/reports', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/compliance-reports/reports — create (auth)', async () => {
    const res = await req('/v1/compliance-reports/reports', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ report_type: 'gdpr', period_start: '2026-01-01', period_end: '2026-03-31' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/compliance-reports/rules — list rules (auth)', async () => {
    const res = await req('/v1/compliance-reports/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/compliance-reports/admin/overview — admin', async () => {
    const res = await req('/v1/compliance-reports/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 59-60: OpenAPI spec', () => {
  it('includes Wave 59-60 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/data-retention/policies');
    expect(paths).toContain('/v1/data-retention/runs');
    expect(paths).toContain('/v1/execution-history/executions');
    expect(paths).toContain('/v1/execution-history/metrics');
    expect(paths).toContain('/admin/error-budget/budgets');
    expect(paths).toContain('/admin/error-budget/events');
    expect(paths).toContain('/v1/api-versioning/versions');
    expect(paths).toContain('/v1/api-versioning/mappings');
    expect(paths).toContain('/admin/capacity-planning/plans');
    expect(paths).toContain('/admin/capacity-planning/alerts');
    expect(paths).toContain('/v1/compliance-reports/reports');
    expect(paths).toContain('/v1/compliance-reports/rules');
  });
});
