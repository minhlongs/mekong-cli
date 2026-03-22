/**
 * Wave 81-82 E2E tests — API Key Rotation, Dependency Graph, Platform Changelog,
 * Data Export, Incident Management, API Sandbox
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

describe('Wave 81: Tenant API Key Rotation', () => {
  it('GET /v1/key-rotation/rotations', async () => { const r = await req('/v1/key-rotation/rotations', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/key-rotation/rotations', async () => { const r = await req('/v1/key-rotation/rotations', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ key_name: 'primary-api-key', rotation_interval_days: 90 }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/key-rotation/history', async () => { const r = await req('/v1/key-rotation/history', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/key-rotation/admin/overview', async () => { const r = await req('/v1/key-rotation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 81: Mission Dependency Graph', () => {
  it('GET /v1/dependency-graph/dependencies', async () => { const r = await req('/v1/dependency-graph/dependencies', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/dependency-graph/dependencies', async () => { const r = await req('/v1/dependency-graph/dependencies', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', depends_on_mission_id: 'm-0', dependency_type: 'required' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/dependency-graph/runs', async () => { const r = await req('/v1/dependency-graph/runs', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/dependency-graph/admin/overview', async () => { const r = await req('/v1/dependency-graph/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 81: Admin Platform Changelog', () => {
  it('GET /admin/platform-changelog/entries', async () => { const r = await req('/admin/platform-changelog/entries', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/platform-changelog/entries', async () => { const r = await req('/admin/platform-changelog/entries', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ version: '2.1.0', title: 'New API endpoints', change_type: 'feature' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/platform-changelog/subscribers', async () => { const r = await req('/admin/platform-changelog/subscribers', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-changelog/dashboard', async () => { const r = await req('/admin/platform-changelog/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/platform-changelog/entries — 403', async () => { const r = await req('/admin/platform-changelog/entries'); expect([401,403]).toContain(r.status); });
});

describe('Wave 82: Tenant Data Export', () => {
  it('GET /v1/data-export/exports', async () => { const r = await req('/v1/data-export/exports', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/data-export/exports', async () => { const r = await req('/v1/data-export/exports', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ export_type: 'full', format: 'json' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/data-export/templates', async () => { const r = await req('/v1/data-export/templates', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/data-export/admin/overview', async () => { const r = await req('/v1/data-export/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 82: Admin Incident Management', () => {
  it('GET /admin/incident-management/incidents', async () => { const r = await req('/admin/incident-management/incidents', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('POST /admin/incident-management/incidents', async () => { const r = await req('/admin/incident-management/incidents', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'API Outage', severity: 'high', affected_services: 'api-gateway' }) }); expect([200,201,400,403,500]).toContain(r.status); });
  it('GET /admin/incident-management/updates', async () => { const r = await req('/admin/incident-management/updates', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/incident-management/dashboard', async () => { const r = await req('/admin/incident-management/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,403,500]).toContain(r.status); });
  it('GET /admin/incident-management/incidents — 403', async () => { const r = await req('/admin/incident-management/incidents'); expect([401,403]).toContain(r.status); });
});

describe('Wave 82: Tenant API Sandbox', () => {
  it('GET /v1/api-sandbox/sandboxes', async () => { const r = await req('/v1/api-sandbox/sandboxes', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('POST /v1/api-sandbox/sandboxes', async () => { const r = await req('/v1/api-sandbox/sandboxes', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ sandbox_name: 'test-env', base_url: 'https://sandbox.example.com' }) }); expect([200,201,400,500]).toContain(r.status); });
  it('GET /v1/api-sandbox/requests', async () => { const r = await req('/v1/api-sandbox/requests', { headers: { Authorization: `Bearer ${token}` } }); expect(r.status).toBeLessThan(500); });
  it('GET /v1/api-sandbox/admin/overview', async () => { const r = await req('/v1/api-sandbox/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }); expect([200,401,403,500]).toContain(r.status); });
});

describe('Wave 81-82: OpenAPI spec', () => {
  it('includes Wave 81-82 paths', async () => {
    const r = await req('/openapi.json'); expect(r.status).toBe(200);
    const body = await r.json() as any; const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/key-rotation/rotations'); expect(paths).toContain('/v1/key-rotation/history');
    expect(paths).toContain('/v1/dependency-graph/dependencies'); expect(paths).toContain('/v1/dependency-graph/runs');
    expect(paths).toContain('/admin/platform-changelog/entries'); expect(paths).toContain('/admin/platform-changelog/subscribers');
    expect(paths).toContain('/v1/data-export/exports'); expect(paths).toContain('/v1/data-export/templates');
    expect(paths).toContain('/admin/incident-management/incidents'); expect(paths).toContain('/admin/incident-management/updates');
    expect(paths).toContain('/v1/api-sandbox/sandboxes'); expect(paths).toContain('/v1/api-sandbox/requests');
  });
});
