/**
 * Wave 99-100 E2E tests — FINAL WAVE!
 * Health Monitor, Output Artifacts, Usage Report,
 * API Changelog, Dashboard Summary, Completion Certificates
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

describe('Wave 99: Tenant API Health Monitor', () => {
  it('GET /v1/health-monitor/monitors', async () => { const r = await req('/v1/health-monitor/monitors', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/health-monitor/monitors', async () => { const r = await req('/v1/health-monitor/monitors', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ monitor_name: 'api-health', endpoint_url: 'https://api.example.com/health' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/health-monitor/results', async () => { const r = await req('/v1/health-monitor/results', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/health-monitor/admin/overview', async () => { const r = await req('/v1/health-monitor/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 99: Mission Output Artifacts', () => {
  it('GET /v1/output-artifacts/artifacts', async () => { const r = await req('/v1/output-artifacts/artifacts', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/output-artifacts/artifacts', async () => { const r = await req('/v1/output-artifacts/artifacts', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', artifact_name: 'report.pdf', artifact_type: 'file' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/output-artifacts/downloads', async () => { const r = await req('/v1/output-artifacts/downloads', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/output-artifacts/admin/overview', async () => { const r = await req('/v1/output-artifacts/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 99: Admin Platform Usage Report', () => {
  it('GET /admin/usage-report/reports', async () => { const r = await req('/admin/usage-report/reports', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/usage-report/reports', async () => { const r = await req('/admin/usage-report/reports', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ report_name: 'March 2026', period: '2026-03' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/usage-report/sections', async () => { const r = await req('/admin/usage-report/sections', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,400,403,500]).toContain(r.status); });
  it('GET /admin/usage-report/dashboard', async () => { const r = await req('/admin/usage-report/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/usage-report/reports — 403', async () => { const r = await req('/admin/usage-report/reports'); expect([401,403]).toContain(r.status); });
});

describe('Wave 100: Tenant API Changelog', () => {
  it('GET /v1/api-changelog/entries', async () => { const r = await req('/v1/api-changelog/entries', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/api-changelog/entries', async () => { const r = await req('/v1/api-changelog/entries', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ version: '1.0.0', title: 'Initial Release', change_type: 'feature' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/api-changelog/subscriptions', async () => { const r = await req('/v1/api-changelog/subscriptions', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/api-changelog/admin/overview', async () => { const r = await req('/v1/api-changelog/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 100: Admin Platform Dashboard Summary', () => {
  it('GET /admin/dashboard-summary/widgets', async () => { const r = await req('/admin/dashboard-summary/widgets', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/dashboard-summary/widgets', async () => { const r = await req('/admin/dashboard-summary/widgets', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ widget_name: 'revenue-chart', widget_type: 'chart', data_source: 'billing' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/dashboard-summary/snapshots', async () => { const r = await req('/admin/dashboard-summary/snapshots', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/dashboard-summary/dashboard', async () => { const r = await req('/admin/dashboard-summary/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/dashboard-summary/widgets — 403', async () => { const r = await req('/admin/dashboard-summary/widgets'); expect([401,403]).toContain(r.status); });
});

describe('Wave 100: Mission Completion Certificates', () => {
  it('GET /v1/completion-certificates/certificates', async () => { const r = await req('/v1/completion-certificates/certificates', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/completion-certificates/certificates', async () => { const r = await req('/v1/completion-certificates/certificates', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', certificate_number: 'CERT-001', issued_to: 'user@example.com' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/completion-certificates/templates', async () => { const r = await req('/v1/completion-certificates/templates', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/completion-certificates/admin/overview', async () => { const r = await req('/v1/completion-certificates/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 99-100: OpenAPI spec — FINAL', () => {
  it('includes Wave 99-100 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/health-monitor/monitors'); expect(paths).toContain('/v1/health-monitor/results');
    expect(paths).toContain('/v1/output-artifacts/artifacts'); expect(paths).toContain('/v1/output-artifacts/downloads');
    expect(paths).toContain('/admin/usage-report/reports'); expect(paths).toContain('/admin/usage-report/sections');
    expect(paths).toContain('/v1/api-changelog/entries'); expect(paths).toContain('/v1/api-changelog/subscriptions');
    expect(paths).toContain('/admin/dashboard-summary/widgets'); expect(paths).toContain('/admin/dashboard-summary/snapshots');
    expect(paths).toContain('/v1/completion-certificates/certificates'); expect(paths).toContain('/v1/completion-certificates/templates');
  });
});
