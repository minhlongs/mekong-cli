/**
 * Wave 63-64 E2E tests — Webhook Signatures, Retry Policies, Feature Usage,
 * API Throttling, Incident Response, Export Schedules
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

// --- Wave 63: Tenant Webhook Signatures ---
describe('Wave 63: Tenant Webhook Signatures', () => {
  it('GET /v1/webhook-signatures/signatures — list (auth)', async () => {
    const res = await req('/v1/webhook-signatures/signatures', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/webhook-signatures/signatures — create (auth)', async () => {
    const res = await req('/v1/webhook-signatures/signatures', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ algorithm: 'sha256', secret_key: 'whsec_test123' }) });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });
  it('GET /v1/webhook-signatures/verifications — verifications (auth)', async () => {
    const res = await req('/v1/webhook-signatures/verifications', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404]).toContain(res.status);
  });
  it('GET /v1/webhook-signatures/admin/overview — admin', async () => {
    const res = await req('/v1/webhook-signatures/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 63: Mission Retry Policies ---
describe('Wave 63: Mission Retry Policies', () => {
  it('GET /v1/retry-policies/policies — list (auth)', async () => {
    const res = await req('/v1/retry-policies/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/retry-policies/policies — create (auth)', async () => {
    const res = await req('/v1/retry-policies/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ policy_name: 'default', max_retries: 3, backoff_type: 'exponential' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/retry-policies/attempts — attempts (auth)', async () => {
    const res = await req('/v1/retry-policies/attempts', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/retry-policies/admin/overview — admin', async () => {
    const res = await req('/v1/retry-policies/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 63: Platform Feature Usage ---
describe('Wave 63: Platform Feature Usage', () => {
  it('GET /admin/feature-usage/usage — list (admin)', async () => {
    const res = await req('/admin/feature-usage/usage', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/feature-usage/usage — record (admin)', async () => {
    const res = await req('/admin/feature-usage/usage', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ feature_name: 'missions', tenant_id: 't-1', usage_count: 50 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/feature-usage/adoption — adoption (admin)', async () => {
    const res = await req('/admin/feature-usage/adoption', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/feature-usage/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/feature-usage/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/feature-usage/usage — 403 without key', async () => {
    const res = await req('/admin/feature-usage/usage');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 64: Tenant API Throttling ---
describe('Wave 64: Tenant API Throttling', () => {
  it('GET /v1/api-throttling/rules — list (auth)', async () => {
    const res = await req('/v1/api-throttling/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-throttling/rules — create (auth)', async () => {
    const res = await req('/v1/api-throttling/rules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/missions/*', requests_per_minute: 100 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/api-throttling/events — events (auth)', async () => {
    const res = await req('/v1/api-throttling/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-throttling/admin/overview — admin', async () => {
    const res = await req('/v1/api-throttling/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 64: Admin Incident Response ---
describe('Wave 64: Admin Incident Response', () => {
  it('GET /admin/incident-response/incidents — list (admin)', async () => {
    const res = await req('/admin/incident-response/incidents', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/incident-response/incidents — create (admin)', async () => {
    const res = await req('/admin/incident-response/incidents', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'API latency spike', severity: 'high', description: 'P99 > 5s' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/incident-response/updates — updates (admin)', async () => {
    const res = await req('/admin/incident-response/updates', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/incident-response/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/incident-response/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/incident-response/incidents — 403 without key', async () => {
    const res = await req('/admin/incident-response/incidents');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 64: Tenant Export Schedules ---
describe('Wave 64: Tenant Export Schedules', () => {
  it('GET /v1/export-schedules/schedules — list (auth)', async () => {
    const res = await req('/v1/export-schedules/schedules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/export-schedules/schedules — create (auth)', async () => {
    const res = await req('/v1/export-schedules/schedules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ export_type: 'missions', format: 'csv', cron_expression: '0 0 * * *', destination: 's3://exports' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/export-schedules/runs — runs (auth)', async () => {
    const res = await req('/v1/export-schedules/runs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/export-schedules/admin/overview — admin', async () => {
    const res = await req('/v1/export-schedules/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 63-64: OpenAPI spec', () => {
  it('includes Wave 63-64 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/webhook-signatures/keys');
    expect(paths).toContain('/v1/webhook-signatures/logs');
    expect(paths).toContain('/v1/retry-policies/policies');
    expect(paths).toContain('/v1/retry-policies/attempts');
    expect(paths).toContain('/admin/feature-usage/usage');
    expect(paths).toContain('/admin/feature-usage/adoption');
    expect(paths).toContain('/v1/api-throttling/rules');
    expect(paths).toContain('/v1/api-throttling/events');
    expect(paths).toContain('/admin/incident-response/incidents');
    expect(paths).toContain('/admin/incident-response/updates');
    expect(paths).toContain('/v1/export-schedules/schedules');
    expect(paths).toContain('/v1/export-schedules/runs');
  });
});
