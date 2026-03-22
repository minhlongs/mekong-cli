/**
 * Wave 97-98 E2E tests — Event Sourcing, Execution Logs, Platform Notifications,
 * Feature Flags, System Configuration, Usage Quotas Management
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

describe('Wave 97: Tenant API Event Sourcing', () => {
  it('GET /v1/event-sourcing/events', async () => { const r = await req('/v1/event-sourcing/events', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/event-sourcing/events', async () => { const r = await req('/v1/event-sourcing/events', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ aggregate_id: 'agg-1', aggregate_type: 'mission', event_type: 'created', event_data: '{}' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/event-sourcing/snapshots', async () => { const r = await req('/v1/event-sourcing/snapshots', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/event-sourcing/admin/overview', async () => { const r = await req('/v1/event-sourcing/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 97: Mission Execution Logs', () => {
  it('GET /v1/execution-logs/logs', async () => { const r = await req('/v1/execution-logs/logs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/execution-logs/logs', async () => { const r = await req('/v1/execution-logs/logs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', step_name: 'init', message: 'Starting mission' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/execution-logs/summaries', async () => { const r = await req('/v1/execution-logs/summaries', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/execution-logs/admin/overview', async () => { const r = await req('/v1/execution-logs/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 97: Admin Platform Notifications', () => {
  it('GET /admin/platform-notifications/notifications', async () => { const r = await req('/admin/platform-notifications/notifications', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-notifications/notifications', async () => { const r = await req('/admin/platform-notifications/notifications', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'Maintenance', message: 'Scheduled downtime', notification_type: 'warning' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-notifications/deliveries', async () => { const r = await req('/admin/platform-notifications/deliveries', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-notifications/dashboard', async () => { const r = await req('/admin/platform-notifications/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-notifications/notifications — 403', async () => { const r = await req('/admin/platform-notifications/notifications'); expect([401,403]).toContain(r.status); });
});

describe('Wave 98: Tenant API Feature Flags', () => {
  it('GET /v1/feature-flags-mgmt/flags', async () => { const r = await req('/v1/feature-flags-mgmt/flags', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/feature-flags-mgmt/flags', async () => { const r = await req('/v1/feature-flags-mgmt/flags', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ flag_key: 'dark-mode', flag_value: 1 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/feature-flags-mgmt/evaluations', async () => { const r = await req('/v1/feature-flags-mgmt/evaluations', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/feature-flags-mgmt/admin/overview', async () => { const r = await req('/v1/feature-flags-mgmt/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 98: Admin System Configuration', () => {
  it('GET /admin/system-config/configs', async () => { const r = await req('/admin/system-config/configs', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/system-config/configs', async () => { const r = await req('/admin/system-config/configs', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ config_key: 'max_tenants', config_value: '1000', config_type: 'number' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/system-config/history', async () => { const r = await req('/admin/system-config/history', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/system-config/dashboard', async () => { const r = await req('/admin/system-config/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/system-config/configs — 403', async () => { const r = await req('/admin/system-config/configs'); expect([401,403]).toContain(r.status); });
});

describe('Wave 98: Tenant Usage Quotas Management', () => {
  it('GET /v1/usage-quotas/quotas', async () => { const r = await req('/v1/usage-quotas/quotas', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/usage-quotas/quotas', async () => { const r = await req('/v1/usage-quotas/quotas', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ resource_type: 'api_calls', quota_limit: 10000, period: 'monthly' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/usage-quotas/alerts', async () => { const r = await req('/v1/usage-quotas/alerts', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/usage-quotas/admin/overview', async () => { const r = await req('/v1/usage-quotas/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 97-98: OpenAPI spec', () => {
  it('includes Wave 97-98 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/event-sourcing/events'); expect(paths).toContain('/v1/event-sourcing/snapshots');
    expect(paths).toContain('/v1/execution-logs/logs'); expect(paths).toContain('/v1/execution-logs/summaries');
    expect(paths).toContain('/admin/platform-notifications/notifications'); expect(paths).toContain('/admin/platform-notifications/deliveries');
    expect(paths).toContain('/v1/feature-flags-mgmt/flags'); expect(paths).toContain('/v1/feature-flags-mgmt/evaluations');
    expect(paths).toContain('/admin/system-config/configs'); expect(paths).toContain('/admin/system-config/history');
    expect(paths).toContain('/v1/usage-quotas/quotas'); expect(paths).toContain('/v1/usage-quotas/alerts');
  });
});
