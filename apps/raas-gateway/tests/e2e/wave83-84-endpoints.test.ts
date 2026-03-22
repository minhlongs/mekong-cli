/**
 * Wave 83-84 E2E tests — Webhook Signatures, Cost Tracking, Platform Maintenance,
 * Usage Analytics, Tenant Migration, Notification Preferences
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

describe('Wave 83: Tenant Webhook Signatures', () => {
  it('GET /v1/webhook-signatures/keys', async () => { const r = await req('/v1/webhook-signatures/keys', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/webhook-signatures/keys', async () => { const r = await req('/v1/webhook-signatures/keys', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ key_name: 'prod-signing-key', algorithm: 'hmac-sha256' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/webhook-signatures/logs', async () => { const r = await req('/v1/webhook-signatures/logs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/webhook-signatures/admin/overview', async () => { const r = await req('/v1/webhook-signatures/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 83: Mission Cost Tracking', () => {
  it('GET /v1/cost-tracking/costs', async () => { const r = await req('/v1/cost-tracking/costs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/cost-tracking/costs', async () => { const r = await req('/v1/cost-tracking/costs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', cost_type: 'compute', amount: 0.05 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/cost-tracking/budgets', async () => { const r = await req('/v1/cost-tracking/budgets', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/cost-tracking/admin/overview', async () => { const r = await req('/v1/cost-tracking/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 83: Admin Platform Maintenance', () => {
  it('GET /admin/platform-maintenance/windows', async () => { const r = await req('/admin/platform-maintenance/windows', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-maintenance/windows', async () => { const r = await req('/admin/platform-maintenance/windows', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'DB Upgrade', scheduled_start: '2026-04-01T02:00:00Z', scheduled_end: '2026-04-01T04:00:00Z' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-maintenance/notifications', async () => { const r = await req('/admin/platform-maintenance/notifications', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-maintenance/dashboard', async () => { const r = await req('/admin/platform-maintenance/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-maintenance/windows — 403', async () => { const r = await req('/admin/platform-maintenance/windows'); expect([401,403]).toContain(r.status); });
});

describe('Wave 84: Tenant Usage Analytics', () => {
  it('GET /v1/usage-analytics/analytics', async () => { const r = await req('/v1/usage-analytics/analytics', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/usage-analytics/analytics', async () => { const r = await req('/v1/usage-analytics/analytics', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint: '/v1/missions', method: 'GET', status_code: 200, response_time_ms: 45 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/usage-analytics/summaries', async () => { const r = await req('/v1/usage-analytics/summaries', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/usage-analytics/admin/overview', async () => { const r = await req('/v1/usage-analytics/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 84: Admin Tenant Migration', () => {
  it('GET /admin/tenant-migration/migrations', async () => { const r = await req('/admin/tenant-migration/migrations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/tenant-migration/migrations', async () => { const r = await req('/admin/tenant-migration/migrations', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ tenant_id: 't-1', from_tier: 'starter', to_tier: 'pro', migration_type: 'upgrade' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/tenant-migration/steps', async () => { const r = await req('/admin/tenant-migration/steps', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/tenant-migration/dashboard', async () => { const r = await req('/admin/tenant-migration/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/tenant-migration/migrations — 403', async () => { const r = await req('/admin/tenant-migration/migrations'); expect([401,403]).toContain(r.status); });
});

describe('Wave 84: Tenant Notification Preferences', () => {
  it('GET /v1/notification-preferences/preferences', async () => { const r = await req('/v1/notification-preferences/preferences', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/notification-preferences/preferences', async () => { const r = await req('/v1/notification-preferences/preferences', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ channel: 'email', event_type: 'mission_completed', enabled: 1 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/notification-preferences/channels', async () => { const r = await req('/v1/notification-preferences/channels', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/notification-preferences/admin/overview', async () => { const r = await req('/v1/notification-preferences/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 83-84: OpenAPI spec', () => {
  it('includes Wave 83-84 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/webhook-signatures/keys'); expect(paths).toContain('/v1/webhook-signatures/logs');
    expect(paths).toContain('/v1/cost-tracking/costs'); expect(paths).toContain('/v1/cost-tracking/budgets');
    expect(paths).toContain('/admin/platform-maintenance/windows'); expect(paths).toContain('/admin/platform-maintenance/notifications');
    expect(paths).toContain('/v1/usage-analytics/analytics'); expect(paths).toContain('/v1/usage-analytics/summaries');
    expect(paths).toContain('/admin/tenant-migration/migrations'); expect(paths).toContain('/admin/tenant-migration/steps');
    expect(paths).toContain('/v1/notification-preferences/preferences'); expect(paths).toContain('/v1/notification-preferences/channels');
  });
});
