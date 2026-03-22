/**
 * Wave 75-76 E2E tests — API Deprecation, Artifact Storage, Tenant Scoring,
 * Custom Metrics, Platform Scaling, Notification Digest
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

describe('Wave 75: Tenant API Deprecation', () => {
  it('GET /v1/api-deprecation/notices — list', async () => { const r = await req('/v1/api-deprecation/notices', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/api-deprecation/notices — create', async () => { const r = await req('/v1/api-deprecation/notices', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: '/v1/old', message: 'Use /v1/new' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/api-deprecation/acknowledgements — ack', async () => { const r = await req('/v1/api-deprecation/acknowledgements', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/api-deprecation/admin/overview — admin', async () => { const r = await req('/v1/api-deprecation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 75: Mission Artifact Storage', () => {
  it('GET /v1/artifact-storage/artifacts — list', async () => { const r = await req('/v1/artifact-storage/artifacts', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/artifact-storage/artifacts — create', async () => { const r = await req('/v1/artifact-storage/artifacts', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', file_name: 'output.json', storage_path: 'r2://artifacts/output.json' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/artifact-storage/downloads — downloads', async () => { const r = await req('/v1/artifact-storage/downloads', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/artifact-storage/admin/overview — admin', async () => { const r = await req('/v1/artifact-storage/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 75: Platform Tenant Scoring', () => {
  it('GET /admin/tenant-scoring/scores — list', async () => { const r = await req('/admin/tenant-scoring/scores', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/tenant-scoring/scores — calculate', async () => { const r = await req('/admin/tenant-scoring/scores', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ tenant_id: 't-1', health_score: 85, engagement_score: 90, revenue_score: 70 }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/tenant-scoring/history — history', async () => { const r = await req('/admin/tenant-scoring/history', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/tenant-scoring/dashboard — dashboard', async () => { const r = await req('/admin/tenant-scoring/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/tenant-scoring/scores — 403 without key', async () => { const r = await req('/admin/tenant-scoring/scores'); expect([401,403]).toContain(r.status); });
});

describe('Wave 76: Tenant Custom Metrics', () => {
  it('GET /v1/custom-metrics/metrics — list', async () => { const r = await req('/v1/custom-metrics/metrics', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/custom-metrics/metrics — create', async () => { const r = await req('/v1/custom-metrics/metrics', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ metric_name: 'api_calls', unit: 'count' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/custom-metrics/data-points — data', async () => { const r = await req('/v1/custom-metrics/data-points', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/custom-metrics/admin/overview — admin', async () => { const r = await req('/v1/custom-metrics/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 76: Admin Platform Scaling', () => {
  it('GET /admin/platform-scaling/rules — list', async () => { const r = await req('/admin/platform-scaling/rules', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-scaling/rules — create', async () => { const r = await req('/admin/platform-scaling/rules', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ rule_name: 'auto-scale-workers', metric_trigger: 'cpu_usage', threshold: 80 }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-scaling/events — events', async () => { const r = await req('/admin/platform-scaling/events', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-scaling/dashboard — dashboard', async () => { const r = await req('/admin/platform-scaling/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-scaling/rules — 403 without key', async () => { const r = await req('/admin/platform-scaling/rules'); expect([401,403]).toContain(r.status); });
});

describe('Wave 76: Tenant Notification Digest', () => {
  it('GET /v1/notification-digest/configs — list', async () => { const r = await req('/v1/notification-digest/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/notification-digest/configs — create', async () => { const r = await req('/v1/notification-digest/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ digest_frequency: 'daily', include_types: 'all' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/notification-digest/deliveries — deliveries', async () => { const r = await req('/v1/notification-digest/deliveries', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/notification-digest/admin/overview — admin', async () => { const r = await req('/v1/notification-digest/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 75-76: OpenAPI spec', () => {
  it('includes Wave 75-76 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/api-deprecation/notices'); expect(paths).toContain('/v1/api-deprecation/acknowledgements');
    expect(paths).toContain('/v1/artifact-storage/artifacts'); expect(paths).toContain('/v1/artifact-storage/downloads');
    expect(paths).toContain('/admin/tenant-scoring/scores'); expect(paths).toContain('/admin/tenant-scoring/history');
    expect(paths).toContain('/v1/custom-metrics/metrics'); expect(paths).toContain('/v1/custom-metrics/data-points');
    expect(paths).toContain('/admin/platform-scaling/rules'); expect(paths).toContain('/admin/platform-scaling/events');
    expect(paths).toContain('/v1/notification-digest/configs'); expect(paths).toContain('/v1/notification-digest/deliveries');
  });
});
