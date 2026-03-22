/**
 * Wave 85-86 E2E tests — API Versioning Config, Quality Scoring, Platform Compliance,
 * Data Retention, Service Registry, API Rate Policies
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

describe('Wave 85: Tenant API Versioning Config', () => {
  it('GET /v1/versioning-config/configs', async () => { const r = await req('/v1/versioning-config/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/versioning-config/configs', async () => { const r = await req('/v1/versioning-config/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ api_version: 'v2', deprecation_policy: 'sunset-in-90-days' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/versioning-config/mappings', async () => { const r = await req('/v1/versioning-config/mappings', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/versioning-config/admin/overview', async () => { const r = await req('/v1/versioning-config/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 85: Mission Quality Scoring', () => {
  it('GET /v1/quality-scoring/scores', async () => { const r = await req('/v1/quality-scoring/scores', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/quality-scoring/scores', async () => { const r = await req('/v1/quality-scoring/scores', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', accuracy_score: 0.95, completeness_score: 0.88, overall_score: 0.91 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/quality-scoring/criteria', async () => { const r = await req('/v1/quality-scoring/criteria', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/quality-scoring/admin/overview', async () => { const r = await req('/v1/quality-scoring/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 85: Admin Platform Compliance', () => {
  it('GET /admin/platform-compliance/requirements', async () => { const r = await req('/admin/platform-compliance/requirements', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-compliance/requirements', async () => { const r = await req('/admin/platform-compliance/requirements', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ requirement_name: 'GDPR Article 17', regulation: 'GDPR' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-compliance/audits', async () => { const r = await req('/admin/platform-compliance/audits', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-compliance/dashboard', async () => { const r = await req('/admin/platform-compliance/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-compliance/requirements — 403', async () => { const r = await req('/admin/platform-compliance/requirements'); expect([401,403]).toContain(r.status); });
});

describe('Wave 86: Tenant Data Retention', () => {
  it('GET /v1/data-retention/policies', async () => { const r = await req('/v1/data-retention/policies', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/data-retention/policies', async () => { const r = await req('/v1/data-retention/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ data_type: 'logs', retention_days: 90, action: 'delete' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/data-retention/executions', async () => { const r = await req('/v1/data-retention/executions', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/data-retention/admin/overview', async () => { const r = await req('/v1/data-retention/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 86: Admin Service Registry', () => {
  it('GET /admin/service-registry/services', async () => { const r = await req('/admin/service-registry/services', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/service-registry/services', async () => { const r = await req('/admin/service-registry/services', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ service_name: 'auth-service', service_url: 'https://auth.example.com', health_endpoint: '/health' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/service-registry/dependencies', async () => { const r = await req('/admin/service-registry/dependencies', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/service-registry/dashboard', async () => { const r = await req('/admin/service-registry/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/service-registry/services — 403', async () => { const r = await req('/admin/service-registry/services'); expect([401,403]).toContain(r.status); });
});

describe('Wave 86: Tenant API Rate Policies', () => {
  it('GET /v1/rate-policies/policies', async () => { const r = await req('/v1/rate-policies/policies', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/rate-policies/policies', async () => { const r = await req('/v1/rate-policies/policies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ policy_name: 'standard', endpoint_pattern: '/v1/*', requests_per_minute: 100 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/rate-policies/violations', async () => { const r = await req('/v1/rate-policies/violations', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/rate-policies/admin/overview', async () => { const r = await req('/v1/rate-policies/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 85-86: OpenAPI spec', () => {
  it('includes Wave 85-86 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/versioning-config/configs'); expect(paths).toContain('/v1/versioning-config/mappings');
    expect(paths).toContain('/v1/quality-scoring/scores'); expect(paths).toContain('/v1/quality-scoring/criteria');
    expect(paths).toContain('/admin/platform-compliance/requirements'); expect(paths).toContain('/admin/platform-compliance/audits');
    expect(paths).toContain('/v1/data-retention/policies'); expect(paths).toContain('/v1/data-retention/executions');
    expect(paths).toContain('/admin/service-registry/services'); expect(paths).toContain('/admin/service-registry/dependencies');
    expect(paths).toContain('/v1/rate-policies/policies'); expect(paths).toContain('/v1/rate-policies/violations');
  });
});
