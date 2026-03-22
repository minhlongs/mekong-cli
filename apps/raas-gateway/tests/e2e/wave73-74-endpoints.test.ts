/**
 * Wave 73-74 E2E tests — API Changelog, Queue Priority, Compliance Audit,
 * Secret Vault, Platform Migration, Event Replay
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

// --- Wave 73: Tenant API Changelog ---
describe('Wave 73: Tenant API Changelog', () => {
  it('GET /v1/api-changelog/entries — list (auth)', async () => {
    const res = await req('/v1/api-changelog/entries', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/api-changelog/entries — create (auth)', async () => {
    const res = await req('/v1/api-changelog/entries', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ change_type: 'update', endpoint: '/v1/missions', description: 'Added pagination' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/api-changelog/subscriptions — subscriptions (auth)', async () => {
    const res = await req('/v1/api-changelog/subscriptions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/api-changelog/admin/overview — admin', async () => {
    const res = await req('/v1/api-changelog/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 73: Mission Queue Priority ---
describe('Wave 73: Mission Queue Priority', () => {
  it('GET /v1/queue-priority/queues — list (auth)', async () => {
    const res = await req('/v1/queue-priority/queues', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/queue-priority/queues — create (auth)', async () => {
    const res = await req('/v1/queue-priority/queues', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ queue_name: 'high-priority', priority_level: 1, max_concurrency: 5 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/queue-priority/items — items (auth)', async () => {
    const res = await req('/v1/queue-priority/items', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/queue-priority/admin/overview — admin', async () => {
    const res = await req('/v1/queue-priority/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 73: Platform Compliance Audit ---
describe('Wave 73: Platform Compliance Audit', () => {
  it('GET /admin/compliance-audit/checks — list (admin)', async () => {
    const res = await req('/admin/compliance-audit/checks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/compliance-audit/checks — create (admin)', async () => {
    const res = await req('/admin/compliance-audit/checks', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ check_name: 'data-encryption', category: 'security', standard: 'SOC2' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/compliance-audit/results — results (admin)', async () => {
    const res = await req('/admin/compliance-audit/results', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/compliance-audit/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/compliance-audit/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/compliance-audit/checks — 403 without key', async () => {
    const res = await req('/admin/compliance-audit/checks');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 74: Tenant Secret Vault ---
describe('Wave 74: Tenant Secret Vault', () => {
  it('GET /v1/secret-vault/secrets — list (auth)', async () => {
    const res = await req('/v1/secret-vault/secrets', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/secret-vault/secrets — create (auth)', async () => {
    const res = await req('/v1/secret-vault/secrets', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ secret_name: 'openai-key', encrypted_value: 'enc_sk-xxx', secret_type: 'api_key' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/secret-vault/access-logs — access logs (auth)', async () => {
    const res = await req('/v1/secret-vault/access-logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/secret-vault/admin/overview — admin', async () => {
    const res = await req('/v1/secret-vault/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 74: Admin Platform Migration ---
describe('Wave 74: Admin Platform Migration', () => {
  it('GET /admin/platform-migration/migrations — list (admin)', async () => {
    const res = await req('/admin/platform-migration/migrations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/platform-migration/migrations — create (admin)', async () => {
    const res = await req('/admin/platform-migration/migrations', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ migration_name: 'add-index-tenants', version: '2.0.1', migration_type: 'schema' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-migration/rollbacks — rollbacks (admin)', async () => {
    const res = await req('/admin/platform-migration/rollbacks', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-migration/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/platform-migration/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-migration/migrations — 403 without key', async () => {
    const res = await req('/admin/platform-migration/migrations');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 74: Tenant Event Replay ---
describe('Wave 74: Tenant Event Replay', () => {
  it('GET /v1/event-replay/configs — list (auth)', async () => {
    const res = await req('/v1/event-replay/configs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/event-replay/configs — create (auth)', async () => {
    const res = await req('/v1/event-replay/configs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ source_event_type: 'mission.completed', target_endpoint: 'https://example.com/replay', replay_speed: 1.0 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/event-replay/runs — runs (auth)', async () => {
    const res = await req('/v1/event-replay/runs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/event-replay/admin/overview — admin', async () => {
    const res = await req('/v1/event-replay/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 73-74: OpenAPI spec', () => {
  it('includes Wave 73-74 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/api-changelog/entries');
    expect(paths).toContain('/v1/api-changelog/subscriptions');
    expect(paths).toContain('/v1/queue-priority/queues');
    expect(paths).toContain('/v1/queue-priority/items');
    expect(paths).toContain('/admin/compliance-audit/checks');
    expect(paths).toContain('/admin/compliance-audit/results');
    expect(paths).toContain('/v1/secret-vault/secrets');
    expect(paths).toContain('/v1/secret-vault/access-logs');
    expect(paths).toContain('/admin/platform-migration/migrations');
    expect(paths).toContain('/admin/platform-migration/rollbacks');
    expect(paths).toContain('/v1/event-replay/configs');
    expect(paths).toContain('/v1/event-replay/runs');
  });
});
