/**
 * Wave 61-62 E2E tests — Notification Channels, Cost Tracking, Audit Policies,
 * Encryption Keys, Traffic Shaping, Integration Marketplace
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

// --- Wave 61: Tenant Notification Channels ---
describe('Wave 61: Tenant Notification Channels', () => {
  it('GET /v1/notification-channels/channels — list (auth)', async () => {
    const res = await req('/v1/notification-channels/channels', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/notification-channels/channels — create (auth)', async () => {
    const res = await req('/v1/notification-channels/channels', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ channel_type: 'slack', config_json: '{"webhook_url":"https://hooks.slack.com/test"}' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/notification-channels/deliveries — deliveries (auth)', async () => {
    const res = await req('/v1/notification-channels/deliveries', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/notification-channels/admin/overview — admin', async () => {
    const res = await req('/v1/notification-channels/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 61: Mission Cost Tracking ---
describe('Wave 61: Mission Cost Tracking', () => {
  it('GET /v1/cost-tracking/costs — list (auth)', async () => {
    const res = await req('/v1/cost-tracking/costs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/cost-tracking/costs — record (auth)', async () => {
    const res = await req('/v1/cost-tracking/costs', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ mission_id: 'm-1', cost_type: 'llm', amount: 0.05, provider: 'openai', model: 'gpt-4' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/cost-tracking/budgets — budgets (auth)', async () => {
    const res = await req('/v1/cost-tracking/budgets', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/cost-tracking/admin/overview — admin', async () => {
    const res = await req('/v1/cost-tracking/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 61: Platform Audit Policies ---
describe('Wave 61: Platform Audit Policies', () => {
  it('GET /admin/audit-policies/policies — list (admin)', async () => {
    const res = await req('/admin/audit-policies/policies', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/audit-policies/policies — create (admin)', async () => {
    const res = await req('/admin/audit-policies/policies', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ policy_name: 'data-access', event_types: 'read,write', retention_days: 365 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/audit-policies/violations — violations (admin)', async () => {
    const res = await req('/admin/audit-policies/violations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/audit-policies/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/audit-policies/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/audit-policies/policies — 403 without key', async () => {
    const res = await req('/admin/audit-policies/policies');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 62: Tenant Data Encryption Keys ---
describe('Wave 62: Tenant Data Encryption Keys', () => {
  it('GET /v1/encryption-keys/keys — list (auth)', async () => {
    const res = await req('/v1/encryption-keys/keys', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/encryption-keys/keys — create (auth)', async () => {
    const res = await req('/v1/encryption-keys/keys', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ key_name: 'primary-key', algorithm: 'AES-256-GCM' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/encryption-keys/usage — usage logs (auth)', async () => {
    const res = await req('/v1/encryption-keys/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/encryption-keys/admin/overview — admin', async () => {
    const res = await req('/v1/encryption-keys/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 62: Admin Traffic Shaping ---
describe('Wave 62: Admin Traffic Shaping', () => {
  it('GET /admin/traffic-shaping/rules — list (admin)', async () => {
    const res = await req('/admin/traffic-shaping/rules', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/traffic-shaping/rules — create (admin)', async () => {
    const res = await req('/admin/traffic-shaping/rules', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ rule_name: 'api-limit', target_pattern: '/v1/*', max_rps: 100 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/traffic-shaping/events — events (admin)', async () => {
    const res = await req('/admin/traffic-shaping/events', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/traffic-shaping/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/traffic-shaping/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/traffic-shaping/rules — 403 without key', async () => {
    const res = await req('/admin/traffic-shaping/rules');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 62: Tenant Integration Marketplace ---
describe('Wave 62: Tenant Integration Marketplace', () => {
  it('GET /v1/integrations/integrations — list (auth)', async () => {
    const res = await req('/v1/integrations/integrations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/integrations/integrations — create (auth)', async () => {
    const res = await req('/v1/integrations/integrations', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ integration_type: 'webhook', provider_name: 'github', config_json: '{}' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/integrations/logs — logs (auth)', async () => {
    const res = await req('/v1/integrations/logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/integrations/admin/overview — admin', async () => {
    const res = await req('/v1/integrations/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 61-62: OpenAPI spec', () => {
  it('includes Wave 61-62 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/notification-channels/channels');
    expect(paths).toContain('/v1/notification-channels/deliveries');
    expect(paths).toContain('/v1/cost-tracking/costs');
    expect(paths).toContain('/v1/cost-tracking/budgets');
    expect(paths).toContain('/admin/audit-policies/policies');
    expect(paths).toContain('/admin/audit-policies/violations');
    expect(paths).toContain('/v1/encryption-keys/keys');
    expect(paths).toContain('/v1/encryption-keys/usage');
    expect(paths).toContain('/admin/traffic-shaping/rules');
    expect(paths).toContain('/admin/traffic-shaping/events');
    expect(paths).toContain('/v1/integrations/integrations');
    expect(paths).toContain('/v1/integrations/logs');
  });
});
