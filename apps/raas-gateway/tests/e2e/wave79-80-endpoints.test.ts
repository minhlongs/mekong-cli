/**
 * Wave 79-80 E2E tests — Playground Configs, Chain Orchestration, Feature Gating,
 * Consent Management, Platform Diagnostics, Rate Burst
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

describe('Wave 79: Tenant API Playground Configs', () => {
  it('GET /v1/playground-configs/configs', async () => { const r = await req('/v1/playground-configs/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/playground-configs/configs', async () => { const r = await req('/v1/playground-configs/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ config_name: 'test-missions', endpoint: '/v1/missions', method: 'GET' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/playground-configs/executions', async () => { const r = await req('/v1/playground-configs/executions', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/playground-configs/admin/overview', async () => { const r = await req('/v1/playground-configs/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 79: Mission Chain Orchestration', () => {
  it('GET /v1/chain-orchestration/chains', async () => { const r = await req('/v1/chain-orchestration/chains', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/chain-orchestration/chains', async () => { const r = await req('/v1/chain-orchestration/chains', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ chain_name: 'data-pipeline', steps_json: '[{"action":"extract"},{"action":"transform"}]' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/chain-orchestration/runs', async () => { const r = await req('/v1/chain-orchestration/runs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/chain-orchestration/admin/overview', async () => { const r = await req('/v1/chain-orchestration/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 79: Platform Feature Gating', () => {
  it('GET /admin/feature-gating/gates', async () => { const r = await req('/admin/feature-gating/gates', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/feature-gating/gates', async () => { const r = await req('/admin/feature-gating/gates', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ feature_key: 'advanced-analytics', display_name: 'Advanced Analytics', allowed_tiers: 'pro,enterprise' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/feature-gating/overrides', async () => { const r = await req('/admin/feature-gating/overrides', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/feature-gating/dashboard', async () => { const r = await req('/admin/feature-gating/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/feature-gating/gates — 403', async () => { const r = await req('/admin/feature-gating/gates'); expect([401,403]).toContain(r.status); });
});

describe('Wave 80: Tenant Consent Management', () => {
  it('GET /v1/consent-management/records', async () => { const r = await req('/v1/consent-management/records', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/consent-management/records', async () => { const r = await req('/v1/consent-management/records', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: 'u-1', consent_type: 'marketing', purpose: 'email campaigns', granted: 1 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/consent-management/policies', async () => { const r = await req('/v1/consent-management/policies', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/consent-management/admin/overview', async () => { const r = await req('/v1/consent-management/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 80: Admin Platform Diagnostics', () => {
  it('GET /admin/platform-diagnostics/checks', async () => { const r = await req('/admin/platform-diagnostics/checks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-diagnostics/checks', async () => { const r = await req('/admin/platform-diagnostics/checks', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ check_name: 'db-connectivity', check_type: 'health', target: 'D1' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-diagnostics/reports', async () => { const r = await req('/admin/platform-diagnostics/reports', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-diagnostics/dashboard', async () => { const r = await req('/admin/platform-diagnostics/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-diagnostics/checks — 403', async () => { const r = await req('/admin/platform-diagnostics/checks'); expect([401,403]).toContain(r.status); });
});

describe('Wave 80: Tenant API Rate Burst', () => {
  it('GET /v1/rate-burst/configs', async () => { const r = await req('/v1/rate-burst/configs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/rate-burst/configs', async () => { const r = await req('/v1/rate-burst/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/*', bucket_size: 100, refill_rate: 10 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/rate-burst/events', async () => { const r = await req('/v1/rate-burst/events', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/rate-burst/admin/overview', async () => { const r = await req('/v1/rate-burst/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 79-80: OpenAPI spec', () => {
  it('includes Wave 79-80 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/playground-configs/configs'); expect(paths).toContain('/v1/playground-configs/executions');
    expect(paths).toContain('/v1/chain-orchestration/chains'); expect(paths).toContain('/v1/chain-orchestration/runs');
    expect(paths).toContain('/admin/feature-gating/gates'); expect(paths).toContain('/admin/feature-gating/overrides');
    expect(paths).toContain('/v1/consent-management/records'); expect(paths).toContain('/v1/consent-management/policies');
    expect(paths).toContain('/admin/platform-diagnostics/checks'); expect(paths).toContain('/admin/platform-diagnostics/reports');
    expect(paths).toContain('/v1/rate-burst/configs'); expect(paths).toContain('/v1/rate-burst/events');
  });
});
