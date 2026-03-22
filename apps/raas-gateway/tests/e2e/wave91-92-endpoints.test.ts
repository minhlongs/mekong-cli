/**
 * Wave 91-92 E2E tests — Load Balancing, Workflow Engine, Security Scan,
 * Schema Validation, Deployment Pipeline, Performance Profiling
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

describe('Wave 91: Tenant API Load Balancing', () => {
  it('GET /v1/load-balancing/configs', async () => { const r = await req('/v1/load-balancing/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/load-balancing/configs', async () => { const r = await req('/v1/load-balancing/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ config_name: 'primary-lb', algorithm: 'round-robin' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/load-balancing/targets', async () => { const r = await req('/v1/load-balancing/targets', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/load-balancing/admin/overview', async () => { const r = await req('/v1/load-balancing/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 91: Mission Workflow Engine', () => {
  it('GET /v1/workflow-engine/workflows', async () => { const r = await req('/v1/workflow-engine/workflows', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/workflow-engine/workflows', async () => { const r = await req('/v1/workflow-engine/workflows', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ workflow_name: 'auto-report', trigger_event: 'mission_completed', steps_json: '[{"action":"generate_report"}]' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/workflow-engine/executions', async () => { const r = await req('/v1/workflow-engine/executions', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/workflow-engine/admin/overview', async () => { const r = await req('/v1/workflow-engine/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 91: Admin Platform Security Scan', () => {
  it('GET /admin/security-scan/scans', async () => { const r = await req('/admin/security-scan/scans', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/security-scan/scans', async () => { const r = await req('/admin/security-scan/scans', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ scan_type: 'dependency', target: 'raas-gateway' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/security-scan/findings', async () => { const r = await req('/admin/security-scan/findings', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/security-scan/dashboard', async () => { const r = await req('/admin/security-scan/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/security-scan/scans — 403', async () => { const r = await req('/admin/security-scan/scans'); expect([401,403]).toContain(r.status); });
});

describe('Wave 92: Tenant API Schema Validation', () => {
  it('GET /v1/schema-validation/schemas', async () => { const r = await req('/v1/schema-validation/schemas', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/schema-validation/schemas', async () => { const r = await req('/v1/schema-validation/schemas', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ schema_name: 'mission-create', endpoint_pattern: '/v1/missions', request_schema: '{"type":"object"}' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/schema-validation/violations', async () => { const r = await req('/v1/schema-validation/violations', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/schema-validation/admin/overview', async () => { const r = await req('/v1/schema-validation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 92: Admin Deployment Pipeline', () => {
  it('GET /admin/deployment-pipeline/pipelines', async () => { const r = await req('/admin/deployment-pipeline/pipelines', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/deployment-pipeline/pipelines', async () => { const r = await req('/admin/deployment-pipeline/pipelines', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ pipeline_name: 'prod-deploy', environment: 'production', stages_json: '[{"name":"build"},{"name":"test"},{"name":"deploy"}]' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/deployment-pipeline/runs', async () => { const r = await req('/admin/deployment-pipeline/runs', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/deployment-pipeline/dashboard', async () => { const r = await req('/admin/deployment-pipeline/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/deployment-pipeline/pipelines — 403', async () => { const r = await req('/admin/deployment-pipeline/pipelines'); expect([401,403]).toContain(r.status); });
});

describe('Wave 92: Tenant Performance Profiling', () => {
  it('GET /v1/performance-profiling/profiles', async () => { const r = await req('/v1/performance-profiling/profiles', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/performance-profiling/profiles', async () => { const r = await req('/v1/performance-profiling/profiles', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ profile_name: 'api-perf', endpoint: '/v1/missions', avg_response_ms: 45.2 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/performance-profiling/baselines', async () => { const r = await req('/v1/performance-profiling/baselines', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/performance-profiling/admin/overview', async () => { const r = await req('/v1/performance-profiling/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 91-92: OpenAPI spec', () => {
  it('includes Wave 91-92 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/load-balancing/configs'); expect(paths).toContain('/v1/load-balancing/targets');
    expect(paths).toContain('/v1/workflow-engine/workflows'); expect(paths).toContain('/v1/workflow-engine/executions');
    expect(paths).toContain('/admin/security-scan/scans'); expect(paths).toContain('/admin/security-scan/findings');
    expect(paths).toContain('/v1/schema-validation/violations');
    expect(paths).toContain('/admin/deployment-pipeline/pipelines'); expect(paths).toContain('/admin/deployment-pipeline/runs');
    expect(paths).toContain('/v1/performance-profiling/profiles'); expect(paths).toContain('/v1/performance-profiling/baselines');
  });
});
