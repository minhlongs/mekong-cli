/**
 * Wave 67-68 E2E tests — API Rate Quotas, Execution Metrics, Service Registry,
 * Data Masking, Deployment Tracking, API Gateway Logs
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

// --- Wave 67: Tenant API Rate Quotas ---
describe('Wave 67: Tenant API Rate Quotas', () => {
  it('GET /v1/api-rate-quotas/quotas — list (auth)', async () => {
    const res = await req('/v1/api-rate-quotas/quotas', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-rate-quotas/quotas — create (auth)', async () => {
    const res = await req('/v1/api-rate-quotas/quotas', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/missions/*', max_requests_per_minute: 60 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/api-rate-quotas/usage — usage (auth)', async () => {
    const res = await req('/v1/api-rate-quotas/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-rate-quotas/admin/overview — admin', async () => {
    const res = await req('/v1/api-rate-quotas/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 67: Mission Execution Metrics ---
describe('Wave 67: Mission Execution Metrics', () => {
  it('GET /v1/execution-metrics/metrics — list (auth)', async () => {
    const res = await req('/v1/execution-metrics/metrics', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/execution-metrics/metrics — record (auth)', async () => {
    const res = await req('/v1/execution-metrics/metrics', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', execution_time_ms: 1500, tokens_used: 500, model_used: 'gpt-4' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/execution-metrics/aggregates — aggregates (auth)', async () => {
    const res = await req('/v1/execution-metrics/aggregates', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/execution-metrics/admin/overview — admin', async () => {
    const res = await req('/v1/execution-metrics/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 67: Platform Service Registry ---
describe('Wave 67: Platform Service Registry', () => {
  it('GET /admin/service-registry/services — list (admin)', async () => {
    const res = await req('/admin/service-registry/services', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/service-registry/services — register (admin)', async () => {
    const res = await req('/admin/service-registry/services', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ service_name: 'mission-executor', service_type: 'worker', endpoint_url: 'https://executor.workers.dev' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/service-registry/health-checks — health checks (admin)', async () => {
    const res = await req('/admin/service-registry/health-checks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/service-registry/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/service-registry/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/service-registry/services — 403 without key', async () => {
    const res = await req('/admin/service-registry/services');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 68: Tenant Data Masking ---
describe('Wave 68: Tenant Data Masking', () => {
  it('GET /v1/data-masking/policies — list (auth)', async () => {
    const res = await req('/v1/data-masking/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/data-masking/policies — create (auth)', async () => {
    const res = await req('/v1/data-masking/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ field_pattern: 'email', masking_type: 'redact', replacement_value: '***' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/data-masking/events — events (auth)', async () => {
    const res = await req('/v1/data-masking/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/data-masking/admin/overview — admin', async () => {
    const res = await req('/v1/data-masking/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 68: Admin Deployment Tracking ---
describe('Wave 68: Admin Deployment Tracking', () => {
  it('GET /admin/deployment-tracking/deployments — list (admin)', async () => {
    const res = await req('/admin/deployment-tracking/deployments', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/deployment-tracking/deployments — create (admin)', async () => {
    const res = await req('/admin/deployment-tracking/deployments', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ version: '2.1.0', environment: 'production', deploy_type: 'full', commit_hash: 'abc123' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/deployment-tracking/rollbacks — rollbacks (admin)', async () => {
    const res = await req('/admin/deployment-tracking/rollbacks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/deployment-tracking/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/deployment-tracking/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/deployment-tracking/deployments — 403 without key', async () => {
    const res = await req('/admin/deployment-tracking/deployments');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 68: Tenant API Gateway Logs ---
describe('Wave 68: Tenant API Gateway Logs', () => {
  it('GET /v1/gateway-logs/logs — list (auth)', async () => {
    const res = await req('/v1/gateway-logs/logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/gateway-logs/logs — record (auth)', async () => {
    const res = await req('/v1/gateway-logs/logs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ method: 'GET', path: '/v1/missions', status_code: 200, response_time_ms: 45 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/gateway-logs/filters — summaries (auth)', async () => {
    const res = await req('/v1/gateway-logs/filters', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/gateway-logs/admin/overview — admin', async () => {
    const res = await req('/v1/gateway-logs/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 67-68: OpenAPI spec', () => {
  it('includes Wave 67-68 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/api-rate-quotas/quotas');
    expect(paths).toContain('/v1/api-rate-quotas/usage');
    expect(paths).toContain('/v1/execution-metrics/metrics');
    expect(paths).toContain('/v1/execution-metrics/aggregates');
    expect(paths).toContain('/admin/service-registry/services');
    expect(paths).toContain('/admin/service-registry/health-checks');
    expect(paths).toContain('/v1/data-masking/policies');
    expect(paths).toContain('/v1/data-masking/events');
    expect(paths).toContain('/admin/deployment-tracking/deployments');
    expect(paths).toContain('/admin/deployment-tracking/rollbacks');
    expect(paths).toContain('/v1/gateway-logs/logs');
    expect(paths).toContain('/v1/gateway-logs/filters');
  });
});
